"""Persistence helpers for backend job and upload files."""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from backend.models import JobState

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
UPLOADS_DIR = DATA_DIR / "uploads"


class JobStoreError(Exception):
    """Raised when job store operations fail."""


def ensure_job_directories() -> None:
    """Create required directories for job metadata and uploads.

    Raises:
        JobStoreError: If directories cannot be created.
    """
    try:
        JOBS_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as error:
        logger.exception("Failed to create job directories: %s", error)
        raise JobStoreError(f"Failed to create job directories: {error}") from error


def utc_now_iso() -> str:
    """Return an ISO UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def get_job_file_path(job_id: str) -> Path:
    """Get file path for a job metadata document.

    Args:
        job_id: Unique job identifier.

    Returns:
        Path to the job JSON file.
    """
    return JOBS_DIR / f"{job_id}.json"


def get_job_payload_path(job_id: str) -> Path:
    """Get file path for worker payload data.

    Args:
        job_id: Unique job identifier.

    Returns:
        Path to the payload JSON file.
    """
    return JOBS_DIR / f"{job_id}.payload.json"


def save_upload(job_id: str, original_name: str, content: BinaryIO) -> Path:
    """Persist uploaded resume content to uploads directory.

    Args:
        job_id: Unique job identifier.
        original_name: Original file name.
        content: Binary stream for uploaded file.

    Returns:
        Path to saved upload.

    Raises:
        JobStoreError: If upload cannot be saved.
    """
    ensure_job_directories()
    extension = Path(original_name).suffix.lower()
    target = UPLOADS_DIR / f"{job_id}{extension}"

    try:
        with target.open("wb") as file_handle:
            shutil.copyfileobj(content, file_handle)
    except Exception as error:
        logger.exception("Failed to save upload for job %s: %s", job_id, error)
        raise JobStoreError(f"Failed to save upload: {error}") from error

    return target


def write_json_atomic(path: Path, payload: dict) -> None:
    """Write JSON payload atomically to avoid torn writes during polling.

    Args:
        path: Target file path.
        payload: Serializable dictionary payload.

    Raises:
        JobStoreError: If write operation fails.
    """
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, dir=str(path.parent)) as tmp:
            json.dump(payload, tmp, indent=2, ensure_ascii=True)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
    except Exception as error:
        logger.exception("Atomic write failed for %s: %s", path, error)
        raise JobStoreError(f"Failed to write file {path}: {error}") from error


def save_job_state(state: JobState) -> None:
    """Persist a job state document to disk.

    Args:
        state: JobState object to serialize.

    Raises:
        JobStoreError: If save operation fails.
    """
    ensure_job_directories()
    write_json_atomic(get_job_file_path(state.job_id), state.model_dump())


def load_job_state(job_id: str) -> JobState:
    """Load persisted job state.

    Args:
        job_id: Unique job identifier.

    Returns:
        Parsed JobState object.

    Raises:
        JobStoreError: If job state cannot be loaded.
    """
    path = get_job_file_path(job_id)
    if not path.exists():
        raise JobStoreError(f"Job {job_id} not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return JobState(**payload)
    except Exception as error:
        logger.exception("Failed to load job %s: %s", job_id, error)
        raise JobStoreError(f"Failed to load job {job_id}: {error}") from error


def save_job_payload(job_id: str, payload: dict) -> Path:
    """Persist worker input payload for background processing.

    Args:
        job_id: Unique job identifier.
        payload: Worker payload data.

    Returns:
        Path to payload file.

    Raises:
        JobStoreError: If payload cannot be written.
    """
    ensure_job_directories()
    path = get_job_payload_path(job_id)
    write_json_atomic(path, payload)
    return path


def load_job_payload(job_id: str) -> dict:
    """Load worker payload from disk.

    Args:
        job_id: Unique job identifier.

    Returns:
        Worker payload dictionary.

    Raises:
        JobStoreError: If payload cannot be loaded.
    """
    path = get_job_payload_path(job_id)
    if not path.exists():
        raise JobStoreError(f"Payload for job {job_id} not found")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        logger.exception("Failed to load payload for job %s: %s", job_id, error)
        raise JobStoreError(f"Failed to load payload for job {job_id}: {error}") from error
