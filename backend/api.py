"""FastAPI adapter for resume upload and async pipeline job execution."""

from __future__ import annotations

import asyncio
from io import BytesIO
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.job_store import JobStoreError, ROOT_DIR, load_job_state, save_job_payload, save_job_state, save_upload, utc_now_iso
from backend.models import HealthResponse, JobCreateResponse, JobState, JobStatusResponse

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(title="MARS Backend Adapter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_required_skills(raw_skills: str) -> List[str]:
    """Parse comma-separated required skills into a normalized list.

    Args:
        raw_skills: Comma-separated skills string.

    Returns:
        List of normalized skill names.
    """
    if not raw_skills.strip():
        return []
    return [item.strip() for item in raw_skills.split(",") if item.strip()]


def _validate_upload(upload: UploadFile) -> None:
    """Validate uploaded resume type and size constraints.

    Args:
        upload: Uploaded file metadata and content.

    Raises:
        HTTPException: If upload extension or size is invalid.
    """
    file_name = upload.filename or ""
    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")


@app.get("/api/health")
def health_check() -> HealthResponse:
    """Return a simple service health payload."""
    return HealthResponse(status="ok", message="MARS backend adapter is healthy", ollama_model=os.getenv("OLLAMA_MODEL"))


@app.post(
    "/api/jobs",
    responses={
        400: {"description": "Invalid upload request."},
        500: {"description": "Backend persistence or worker startup failure."},
    },
)
async def create_job(
    resume: UploadFile = File(...),
    candidate_name: str = Form(default=""),
    job_description: str = Form(default=""),
    required_skills: str = Form(default=""),
) -> JobCreateResponse:
    """Create an async MARS pipeline job from uploaded resume data.

    Args:
        resume: Uploaded PDF or DOCX resume.
        candidate_name: Optional candidate name override.
        job_description: Optional job description text.
        required_skills: Optional comma-separated required skills.

    Returns:
        JobCreateResponse containing created job ID and initial status.

    Raises:
        HTTPException: If upload validation, persistence, or worker spawn fails.
    """
    _validate_upload(resume)

    contents = await resume.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit.")

    job_id = str(uuid.uuid4())

    try:
        upload_path = save_upload(
            job_id=job_id,
            original_name=resume.filename or "resume.pdf",
            content=BytesIO(contents),
        )

        created_at = utc_now_iso()
        state = JobState(
            job_id=job_id,
            status="queued",
            created_at=created_at,
            updated_at=created_at,
            input_file_name=resume.filename or "resume.pdf",
            resume_file_path=str(upload_path),
            candidate_name=candidate_name.strip(),
            job_description=job_description.strip(),
            required_skills=_parse_required_skills(required_skills),
            logs=[f"[BackendAPI] Job {job_id} created."],
        )
        save_job_state(state)

        payload = {
            "resume_file_path": str(upload_path),
            "candidate_name": candidate_name.strip(),
            "job_description": job_description.strip(),
            "required_skills": _parse_required_skills(required_skills),
        }
        save_job_payload(job_id=job_id, payload=payload)

        await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "backend.worker",
            "--job-id",
            job_id,
            cwd=str(ROOT_DIR),
        )
    except JobStoreError as error:
        logger.exception("Failed to create job %s: %s", job_id, error)
        raise HTTPException(status_code=500, detail=f"Failed to persist job data: {error}") from error
    except Exception as error:
        logger.exception("Failed to spawn worker for job %s: %s", job_id, error)
        raise HTTPException(status_code=500, detail=f"Failed to start worker: {error}") from error

    return JobCreateResponse(job_id=job_id, status="queued")


@app.get(
    "/api/jobs/{job_id}",
    responses={
        404: {"description": "Job not found."},
    },
)
def get_job_status(job_id: str) -> JobStatusResponse:
    """Return the latest persisted status for a job.

    Args:
        job_id: Unique job identifier.

    Returns:
        JobStatusResponse payload for frontend polling.

    Raises:
        HTTPException: If job cannot be found or loaded.
    """
    try:
        state = load_job_state(job_id)
    except JobStoreError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    metadata = {
        "candidate_name": state.candidate_name,
        "input_file_name": state.input_file_name,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }

    return JobStatusResponse(
        job_id=state.job_id,
        status=state.status,
        final_recommendation=state.final_recommendation,
        recommendation_reason=state.recommendation_reason,
        report_path=state.report_path,
        logs=state.logs,
        error=state.error,
        metadata=metadata,
    )


@app.get(
    "/api/jobs/{job_id}/report",
    responses={
        404: {"description": "Job or report file not found."},
        409: {"description": "Job has not completed yet."},
    },
)
def get_job_report(job_id: str) -> FileResponse:
    """Return generated report for a completed job.

    Args:
        job_id: Unique job identifier.

    Returns:
        FileResponse with markdown report if available.

    Raises:
        HTTPException: If job/report is not ready.
    """
    try:
        state = load_job_state(job_id)
    except JobStoreError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    if state.status != "completed":
        raise HTTPException(status_code=409, detail="Report is not available until job completes.")

    report_path = Path(state.report_path)
    if not state.report_path or not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found.")

    return FileResponse(path=report_path, media_type="application/pdf", filename=report_path.name)
