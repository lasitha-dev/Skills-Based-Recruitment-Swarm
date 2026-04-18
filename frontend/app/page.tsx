"use client";

import { useCallback, useMemo, useState } from "react";

import { JobMonitor } from "@/components/JobMonitor";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { UploadForm } from "@/components/UploadForm";
import { JobStatusResponse, createJob, getJobStatus } from "@/lib/api";

type RunViewState = "idle" | "submitting" | "polling" | "completed" | "failed" | "poll-error";

export default function HomePage(): JSX.Element {
  const [jobId, setJobId] = useState("");
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [runState, setRunState] = useState<RunViewState>("idle");
  const [pollError, setPollError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);

  const subtitle = useMemo(() => {
    if (!jobId) {
      return "Start with resume ingestion and launch your 4-agent hiring workflow.";
    }
    return "Pipeline active. Agent findings are synced in global state until final recommendation.";
  }, [jobId]);

  const handleSubmit = useCallback(async (payload: {
    resumeFile: File;
    candidateName: string;
    jobDescription: string;
    requiredSkills: string;
  }) => {
    setIsSubmitting(true);
    setRunState("submitting");
    setPollError("");

    try {
      const created = await createJob(payload);
      setJobId(created.job_id);
      setJob({
        job_id: created.job_id,
        status: created.status,
        final_recommendation: "",
        recommendation_reason: "",
        report_path: "",
        logs: ["[Frontend] Job created. Waiting for worker..."],
        error: "",
        metadata: {},
      });
      setRunState("polling");
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const handlePoll = useCallback(async (id: string) => {
    setIsPolling(true);

    try {
      const status = await getJobStatus(id);
      setJob(status);

      if (status.status === "completed") {
        setRunState("completed");
      } else if (status.status === "failed") {
        setRunState("failed");
      } else {
        setRunState("polling");
      }

      setPollError("");
    } finally {
      setIsPolling(false);
    }
  }, []);

  const handlePollSafe = useCallback(async (id: string) => {
    try {
      await handlePoll(id);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to poll job status.";
      setPollError(message);
      setRunState("poll-error");
      throw error;
    }
  }, [handlePoll]);

  return (
    <main className="app-shell">
      <div className="bg-ornament bg-ornament-top" />
      <div className="bg-ornament bg-ornament-bottom" />

      <header className="hero">
        <p className="kicker">MARS Recruiter Console</p>
        <h1>Sequential Agentic Hiring, Visible End-to-End</h1>
        <p className="hero-subtitle">{subtitle}</p>
      </header>

      <section className="grid-layout">
        <UploadForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
        <JobMonitor
          job={job}
          jobId={jobId}
          isPolling={isPolling}
          runState={runState}
          pollError={pollError}
          onPoll={handlePollSafe}
        />
      </section>

      <RecommendationPanel job={job} runState={runState} pollError={pollError} />
    </main>
  );
}
