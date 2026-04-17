"use client";

import { useEffect, useMemo, useRef } from "react";

import { JobStatusResponse } from "@/lib/api";

interface JobMonitorProps {
  job: JobStatusResponse | null;
  jobId: string;
  isPolling: boolean;
  onPoll: (jobId: string) => Promise<void>;
}

export function JobMonitor({ job, jobId, isPolling, onPoll }: Readonly<JobMonitorProps>): JSX.Element {
  const pollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    const pollInterval = job?.status === "running" ? 1500 : 1000;

    pollTimerRef.current = globalThis.setInterval(() => {
      void onPoll(jobId);
    }, pollInterval);

    return () => {
      if (pollTimerRef.current) {
        globalThis.clearInterval(pollTimerRef.current);
      }
    };
  }, [job?.status, jobId, onPoll]);

  const badgeClass = useMemo(() => {
    if (!job) {
      return "status-badge queued";
    }
    return `status-badge ${job.status}`;
  }, [job]);

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
      <p className="muted">{isPolling ? "Polling latest state..." : "Idle"}</p>

      <div className="log-box">
        {(job?.logs ?? []).slice(-10).map((logLine, index) => (
          <p key={`${logLine}-${index}`}>{logLine}</p>
        ))}
      </div>
    </section>
  );
}
