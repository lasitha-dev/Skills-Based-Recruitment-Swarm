import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { JobStatusResponse } from "@/lib/api";

const { createJobMock, getJobStatusMock } = vi.hoisted(() => {
  return {
    createJobMock: vi.fn(),
    getJobStatusMock: vi.fn(),
  };
});

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    createJob: createJobMock,
    getJobStatus: getJobStatusMock,
  };
});

vi.mock("@/components/UploadForm", () => ({
  UploadForm: ({ onSubmit }: { onSubmit: (payload: { resumeFile: File; candidateName: string; jobDescription: string; requiredSkills: string }) => Promise<void> }) => (
    <button
      data-testid="submit-upload"
      onClick={() => {
        void onSubmit({
          resumeFile: new File(["resume"], "resume.pdf", { type: "application/pdf" }),
          candidateName: "Test User",
          jobDescription: "Need Python",
          requiredSkills: "Python",
        });
      }}
    >
      Submit Upload
    </button>
  ),
}));

vi.mock("@/components/JobMonitor", () => ({
  JobMonitor: ({ jobId, runState, pollError, onPoll }: { jobId: string; runState: string; pollError: string; onPoll: (jobId: string) => Promise<void> }) => (
    <div>
      <p data-testid="job-id">{jobId || "no-job"}</p>
      <p data-testid="run-state">{runState}</p>
      <p data-testid="poll-error">{pollError || "none"}</p>
      <button
        data-testid="poll-now"
        onClick={() => {
          void onPoll(jobId || "job-123").catch(() => undefined);
        }}
      >
        Poll Now
      </button>
    </div>
  ),
}));

vi.mock("@/components/RecommendationPanel", () => ({
  RecommendationPanel: ({ runState, pollError, job }: { runState: string; pollError: string; job: JobStatusResponse | null }) => (
    <div>
      <p data-testid="recommendation-run-state">{runState}</p>
      <p data-testid="recommendation-poll-error">{pollError || "none"}</p>
      <p data-testid="recommendation-value">{job?.final_recommendation || "none"}</p>
    </div>
  ),
}));

describe("HomePage integration flow", () => {
  beforeEach(() => {
    createJobMock.mockReset();
    getJobStatusMock.mockReset();
  });

  it("submits upload then reaches completed state after polling", async () => {
    const { default: HomePage } = await import("@/app/page");

    createJobMock.mockResolvedValue({
      job_id: "job-123",
      status: "queued",
    });

    getJobStatusMock.mockResolvedValue({
      job_id: "job-123",
      status: "completed",
      final_recommendation: "Strong Hire",
      recommendation_reason: "Great fit",
      report_path: "report.md",
      logs: ["done"],
      error: "",
      metadata: {},
    });

    render(<HomePage />);

    fireEvent.click(screen.getByTestId("submit-upload"));

    await waitFor(() => {
      expect(screen.getByTestId("job-id").textContent).toBe("job-123");
      expect(screen.getByTestId("run-state").textContent).toBe("polling");
    });

    fireEvent.click(screen.getByTestId("poll-now"));

    await waitFor(() => {
      expect(screen.getByTestId("run-state").textContent).toBe("completed");
      expect(screen.getByTestId("recommendation-value").textContent).toBe("Strong Hire");
    });
  });

  it("shows poll-error state when status polling fails", async () => {
    const { default: HomePage } = await import("@/app/page");

    createJobMock.mockResolvedValue({
      job_id: "job-124",
      status: "queued",
    });

    getJobStatusMock.mockRejectedValue(new Error("Network down"));

    render(<HomePage />);

    fireEvent.click(screen.getByTestId("submit-upload"));
    await waitFor(() => {
      expect(screen.getByTestId("job-id").textContent).toBe("job-124");
    });

    fireEvent.click(screen.getByTestId("poll-now"));

    await waitFor(() => {
      expect(screen.getByTestId("run-state").textContent).toBe("poll-error");
      expect(screen.getByTestId("poll-error").textContent).toContain("Network down");
    });
  });
});
