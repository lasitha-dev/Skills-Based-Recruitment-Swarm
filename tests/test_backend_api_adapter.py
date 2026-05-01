"""Backend adapter endpoint tests for upload validation and job status flow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from backend.api import app
from backend.models import JobState


pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    """Pin anyio test execution to asyncio backend only."""
    return "asyncio"


async def test_create_job_rejects_unsupported_extension() -> None:
    """POST /api/jobs rejects non-PDF/DOCX files with HTTP 400."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/jobs",
            files={"resume": ("resume.txt", b"plain text", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF and DOCX files are allowed."


async def test_create_job_accepts_pdf_and_queues_job(monkeypatch) -> None:
    """POST /api/jobs accepts PDF upload and returns queued job payload."""
    async_subprocess = AsyncMock()

    monkeypatch.setattr("backend.api.uuid.uuid4", lambda: "job-queued-1")
    monkeypatch.setattr("backend.api.utc_now_iso", lambda: "2026-04-19T00:00:00+00:00")
    monkeypatch.setattr("backend.api.save_upload", lambda **_: Path("data/uploads/job-queued-1.pdf"))
    monkeypatch.setattr("backend.api.save_job_state", lambda _state: None)
    monkeypatch.setattr("backend.api.save_job_payload", lambda **_: Path("data/jobs/job-queued-1.payload.json"))
    monkeypatch.setattr("backend.api.asyncio.create_subprocess_exec", async_subprocess)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/jobs",
            data={
                "candidate_name": "Jane",
                "job_description": "Need Python",
                "required_skills": "Python, AWS",
            },
            files={"resume": ("resume.pdf", b"%PDF-1.4 fake bytes", "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json() == {"job_id": "job-queued-1", "status": "queued"}
    async_subprocess.assert_awaited_once()


async def test_get_job_status_returns_payload(monkeypatch) -> None:
    """GET /api/jobs/{job_id} returns persisted status payload."""
    state = JobState(
        job_id="job-status-1",
        status="running",
        created_at="2026-04-19T00:00:00+00:00",
        updated_at="2026-04-19T00:00:05+00:00",
        input_file_name="resume.pdf",
        resume_file_path="data/uploads/resume.pdf",
        candidate_name="Jane",
        job_description="Need Python",
        required_skills=["Python"],
        final_recommendation="",
        recommendation_reason="",
        report_path="",
        logs=["[BackendWorker] started"],
        error="",
    )

    monkeypatch.setattr("backend.api.load_job_state", lambda _job_id: state)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/jobs/job-status-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == "job-status-1"
    assert payload["status"] == "running"
    assert payload["metadata"]["candidate_name"] == "Jane"
    assert payload["metadata"]["input_file_name"] == "resume.pdf"


async def test_get_job_report_returns_409_when_not_completed(monkeypatch) -> None:
    """GET /api/jobs/{job_id}/report returns 409 for non-completed jobs."""
    state = JobState(
        job_id="job-report-1",
        status="running",
        created_at="2026-04-19T00:00:00+00:00",
        updated_at="2026-04-19T00:00:05+00:00",
        input_file_name="resume.pdf",
        resume_file_path="data/uploads/resume.pdf",
        candidate_name="Jane",
        logs=[],
    )

    monkeypatch.setattr("backend.api.load_job_state", lambda _job_id: state)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/jobs/job-report-1/report")

    assert response.status_code == 409
    assert "not available until job completes" in response.json()["detail"]
