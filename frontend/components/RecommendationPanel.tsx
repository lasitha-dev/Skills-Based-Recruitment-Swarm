"use client";

import { JobStatusResponse, getReportDownloadUrl } from "@/lib/api";

interface RecommendationPanelProps {
  job: JobStatusResponse | null;
  runState: "idle" | "submitting" | "polling" | "completed" | "failed" | "poll-error";
  pollError: string;
}

export function RecommendationPanel({ job, runState, pollError }: Readonly<RecommendationPanelProps>): JSX.Element {
  if (runState === "poll-error") {
    return (
      <section className="panel recommendation-panel">
        <h2>Recommendation</h2>
        <p className="error-box">Status sync interrupted: {pollError || "Polling failed unexpectedly."}</p>
      </section>
    );
  }

  if (!job || (job.status !== "completed" && job.status !== "failed")) {
    return (
      <section className="panel recommendation-panel">
        <h2>Recommendation</h2>
        <p className="muted">Final synthesis appears here after Agent 4 completes.</p>
      </section>
    );
  }

  if (job.status === "failed") {
    return (
      <section className="panel recommendation-panel">
        <h2>Recommendation</h2>
        <p className="error-box">Pipeline failed: {job.error || "Unknown error"}</p>
      </section>
    );
  }

  return (
    <section className="panel recommendation-panel reveal-in">
      <h2>Recommendation</h2>
      <p className="recommendation-label">{job.final_recommendation || "Insufficient data"}</p>
      <p>{job.recommendation_reason || "No recommendation reason provided."}</p>
      <a className="report-link" href={getReportDownloadUrl(job.job_id)} target="_blank" rel="noreferrer">
        Download Generated Report
      </a>
      <p className="muted">Report path: {job.report_path || "not available"}</p>
    </section>
  );
}
