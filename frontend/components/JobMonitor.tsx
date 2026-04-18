"use client";

import { useEffect, useMemo, useRef } from "react";

import { JobStatusResponse } from "@/lib/api";

interface JobMonitorProps {
  job: JobStatusResponse | null;
  jobId: string;
  isPolling: boolean;
  runState: "idle" | "submitting" | "polling" | "completed" | "failed" | "poll-error";
  pollError: string;
  onPoll: (jobId: string) => Promise<void>;
}

export function JobMonitor({ job, jobId, isPolling, runState, pollError, onPoll }: Readonly<JobMonitorProps>): JSX.Element {
  const pollTimerRef = useRef<number | null>(null);
  const pollFailureCountRef = useRef(0);

  const isTerminal = job?.status === "completed" || job?.status === "failed";

  useEffect(() => {
    if (!jobId || isTerminal) {
      return;
    }

    let cancelled = false;

    const scheduleNextPoll = (delayMs: number): void => {
      if (cancelled) {
        return;
      }

      pollTimerRef.current = globalThis.setTimeout(async () => {
        try {
          await onPoll(jobId);
          pollFailureCountRef.current = 0;
        } catch {
          pollFailureCountRef.current += 1;
        }

        const baseInterval = job?.status === "running" ? 1500 : 1000;
        const backoffInterval = Math.min(baseInterval * (pollFailureCountRef.current + 1), 8000);
        scheduleNextPoll(backoffInterval);
      }, delayMs);
    };

    scheduleNextPoll(0);

    return () => {
      cancelled = true;
      if (pollTimerRef.current) {
        globalThis.clearTimeout(pollTimerRef.current);
      }
    };
  }, [isTerminal, job?.status, jobId, onPoll]);

  const badgeClass = useMemo(() => {
    if (!job) {
      return "status-badge queued";
    }
    return `status-badge ${job.status}`;
  }, [job]);

  const statusMessage = useMemo(() => {
    if (runState === "completed" || runState === "failed") {
      return "Terminal state reached. Polling stopped.";
    }

    if (isPolling) {
      return "Polling latest state...";
    }

    return "Idle";
  }, [isPolling, runState]);

  if (!jobId) {
    return (
      <section className="panel status-panel">
        <h2>Pipeline Status</h2>
        <p className="muted">No active run yet.</p>
      </section>
    );
  }

  return (
    <section className="panel status-panel">
      <h2>Pipeline Status</h2>
      <p><strong>Job ID:</strong> {jobId}</p>
      <p className={badgeClass}>{job?.status ?? "queued"}</p>
      <p className="muted">{statusMessage}</p>

      {pollError ? <p className="error-box">Polling issue: {pollError}</p> : null}

      <p className="muted"><strong>Candidate:</strong> {job?.metadata?.candidate_name ?? "N/A"}</p>
      <p className="muted"><strong>File:</strong> {job?.metadata?.input_file_name ?? "N/A"}</p>
      <p className="muted"><strong>Created:</strong> {job?.metadata?.created_at ?? "N/A"}</p>
      <p className="muted"><strong>Updated:</strong> {job?.metadata?.updated_at ?? "N/A"}</p>

      <div className="log-box">
        {(job?.logs ?? []).slice(-10).map((logLine, index) => (
          <p key={`${logLine}-${index}`}>{logLine}</p>
        ))}
      </div>
    </section>
  );
}
