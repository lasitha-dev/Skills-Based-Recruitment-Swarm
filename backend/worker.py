"""Background worker that runs the MARS pipeline for a queued job."""

from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
import os
import time
import traceback
from typing import Any

from agents.state import AgentState
from backend.job_store import JobStoreError, load_job_payload, load_job_state, save_job_state, utc_now_iso
from main_graph import run_mars_pipeline

logger = logging.getLogger(__name__)

DEFAULT_JOB_TIMEOUT_SECONDS = 600
HEARTBEAT_INTERVAL_SECONDS = 15


def _resolve_job_timeout_seconds() -> int:
    """Resolve timeout value from environment with safe fallback.

    Returns:
        Timeout duration in seconds.
    """
    raw_value = os.getenv("MARS_JOB_TIMEOUT_SECONDS", str(DEFAULT_JOB_TIMEOUT_SECONDS))
    try:
        timeout_seconds = int(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid MARS_JOB_TIMEOUT_SECONDS value '%s'. Falling back to %s.",
            raw_value,
            DEFAULT_JOB_TIMEOUT_SECONDS,
        )
        return DEFAULT_JOB_TIMEOUT_SECONDS

    return max(60, timeout_seconds)


def _run_pipeline_child(payload: dict[str, Any], result_queue: mp.Queue) -> None:
    """Run the MARS pipeline in a separate process and push result to queue.

    Args:
        payload: Persisted payload with resume path and optional user inputs.
        result_queue: Multiprocessing queue used to send result back to parent.
    """
    try:
        initial_state: AgentState = {
            "resume_file_path": payload.get("resume_file_path", ""),
            "candidate_name": payload.get("candidate_name", ""),
            "job_description": payload.get("job_description", ""),
            "required_skills": payload.get("required_skills", []),
            "found_skills": [],
            "logs": ["[BackendWorker] Pipeline subprocess invoked."],
        }

        final_state = run_mars_pipeline(initial_state)
        result_queue.put({"ok": True, "final_state": final_state})
    except Exception as error:
        result_queue.put({"ok": False, "error": str(error), "traceback": traceback.format_exc()})


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

    timeout_seconds = _resolve_job_timeout_seconds()
    result_queue: mp.Queue = mp.Queue()
    child = mp.Process(target=_run_pipeline_child, args=(payload, result_queue), daemon=True)

    try:
        child.start()

        start_time = time.monotonic()
        last_heartbeat = start_time

        while child.is_alive():
            elapsed = time.monotonic() - start_time
            remaining = timeout_seconds - elapsed

            if remaining <= 0:
                break

            child.join(timeout=min(1.0, remaining))

            now = time.monotonic()
            if child.is_alive() and (now - last_heartbeat) >= HEARTBEAT_INTERVAL_SECONDS:
                state.updated_at = utc_now_iso()
                state.logs.append(
                    f"[BackendWorker] Job {job_id} still running ({int(elapsed)}s elapsed)."
                )
                save_job_state(state)
                last_heartbeat = now

        if child.is_alive():
            child.terminate()
            child.join(timeout=5)

            state.status = "failed"
            state.updated_at = utc_now_iso()
            state.error = (
                f"Pipeline timed out after {timeout_seconds} seconds. "
                "Job terminated to avoid indefinite running state."
            )
            state.logs.append(f"[BackendWorker] Job {job_id} timed out and was terminated.")
            save_job_state(state)
            return

        if result_queue.empty():
            state.status = "failed"
            state.updated_at = utc_now_iso()
            state.error = "Pipeline subprocess exited without returning results."
            state.logs.append(f"[BackendWorker] Job {job_id} failed: no result payload.")
            save_job_state(state)
            return

        result = result_queue.get()
        if not result.get("ok", False):
            state.status = "failed"
            state.updated_at = utc_now_iso()
            state.error = str(result.get("error", "Unknown pipeline error"))
            state.logs.append("[BackendWorker] Job failed.")
            state.logs.append(str(result.get("traceback", "No traceback available.")))
            save_job_state(state)
            return

        final_state = result.get("final_state", {})

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
