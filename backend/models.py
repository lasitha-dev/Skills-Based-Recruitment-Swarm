"""Typed models for backend job lifecycle payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

JobStatus = Literal["queued", "running", "completed", "failed"]


class JobState(BaseModel):
    """Persisted state for a pipeline execution job.

    Attributes:
        job_id: Unique identifier for the job.
        status: Current execution status.
        created_at: ISO timestamp when the job was created.
        updated_at: ISO timestamp when job state was last updated.
        input_file_name: Original uploaded file name.
        resume_file_path: Absolute path to stored uploaded resume file.
        candidate_name: Candidate name supplied by user.
        job_description: Job description text supplied by user.
        required_skills: Optional required skill list supplied by user.
        final_recommendation: Agent 4 recommendation once completed.
        recommendation_reason: Agent 4 reason once completed.
        report_path: Local path to generated report.
        logs: Aggregated logs from all agents.
        error: Failure message for failed jobs.
    """

    job_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    input_file_name: str
    resume_file_path: str
    candidate_name: str = ""
    job_description: str = ""
    required_skills: List[str] = Field(default_factory=list)
    final_recommendation: str = ""
    recommendation_reason: str = ""
    report_path: str = ""
    logs: List[str] = Field(default_factory=list)
    error: str = ""


class JobCreateResponse(BaseModel):
    """API response returned after creating a new job."""

    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    """API response returned when querying job state."""

    job_id: str
    status: JobStatus
    final_recommendation: str = ""
    recommendation_reason: str = ""
    report_path: str = ""
    logs: List[str] = Field(default_factory=list)
    error: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health endpoint payload."""

    status: Literal["ok"]
    message: str
    ollama_model: Optional[str] = None
