"""Background worker that runs the MARS pipeline for a queued job."""

from __future__ import annotations

import argparse
import logging
import traceback

from agents.state import AgentState
from backend.job_store import JobStoreError, load_job_payload, load_job_state, save_job_state, utc_now_iso
from main_graph import run_mars_pipeline

logger = logging.getLogger(__name__)


def run_job(job_id: str) -> None:
    """Execute a single job by loading payload and running the pipeline.

    Args:
        job_id: Unique job identifier.

    Raises:
        JobStoreError: If loading/saving persisted state fails.
    """
    state = load_job_state(job_id)
    payload = load_job_payload(job_id)

    state.status = "running"
    state.updated_at = utc_now_iso()
    state.logs.append(f"[BackendWorker] Job {job_id} started.")
    save_job_state(state)

    try:
        initial_state: AgentState = {
            "resume_file_path": payload.get("resume_file_path", ""),
            "candidate_name": payload.get("candidate_name", ""),
            "job_description": payload.get("job_description", ""),
            "required_skills": payload.get("required_skills", []),
            "found_skills": [],
            "logs": [f"[BackendWorker] Pipeline invoked for job {job_id}."]
        }

        final_state = run_mars_pipeline(initial_state)

        state.status = "completed"
        state.updated_at = utc_now_iso()
        state.final_recommendation = str(final_state.get("final_recommendation", ""))
        state.recommendation_reason = str(final_state.get("recommendation_reason", ""))
        state.report_path = str(final_state.get("report_path", ""))
        state.logs = list(final_state.get("logs", []))
        state.logs.append(f"[BackendWorker] Job {job_id} completed.")
        save_job_state(state)
    except Exception as error:
        logger.exception("Pipeline failed for job %s: %s", job_id, error)
        state.status = "failed"
        state.updated_at = utc_now_iso()
        state.error = str(error)
        state.logs.append("[BackendWorker] Job failed.")
        state.logs.append(traceback.format_exc())
        save_job_state(state)


def parse_args() -> argparse.Namespace:
    """Parse worker CLI arguments.

    Returns:
        Parsed CLI namespace.
    """
    parser = argparse.ArgumentParser(description="Run MARS pipeline worker for one job")
    parser.add_argument("--job-id", required=True, help="Job ID to run")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint for worker execution.

    Returns:
        Process exit code.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")

    args = parse_args()

    try:
        run_job(job_id=args.job_id)
        return 0
    except JobStoreError as error:
        logger.error("Worker aborted due to job store error: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
