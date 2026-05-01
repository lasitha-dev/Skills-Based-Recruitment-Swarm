import React from "react";
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { JobMonitor } from "@/components/JobMonitor";

describe("JobMonitor", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("does not poll when job is already in terminal state", async () => {
    const onPoll = vi.fn().mockResolvedValue(undefined);

    render(
      <JobMonitor
        job={{
          job_id: "job-1",
          status: "completed",
          final_recommendation: "Proceed to Interview",
          recommendation_reason: "Done",
          report_path: "",
          logs: [],
          error: "",
          metadata: {},
        }}
        jobId="job-1"
        isPolling={false}
        runState="completed"
        pollError=""
        onPoll={onPoll}
      />,
    );

    await act(async () => {
      vi.advanceTimersByTime(10000);
    });

    expect(onPoll).not.toHaveBeenCalled();
    expect(screen.getByText("Terminal state reached. Polling stopped.")).toBeInTheDocument();
  });

  it("retries polling after failures with delayed attempts", async () => {
    const onPoll = vi
      .fn()
      .mockRejectedValueOnce(new Error("network"))
      .mockRejectedValueOnce(new Error("network"))
      .mockResolvedValue(undefined);

    render(
      <JobMonitor
        job={{
          job_id: "job-2",
          status: "running",
          final_recommendation: "",
          recommendation_reason: "",
          report_path: "",
          logs: [],
          error: "",
          metadata: {
            candidate_name: "Test Candidate",
            input_file_name: "resume.pdf",
          },
        }}
        jobId="job-2"
        isPolling={true}
        runState="polling"
        pollError=""
        onPoll={onPoll}
      />,
    );

    await act(async () => {
      vi.advanceTimersByTime(0);
    });
    expect(onPoll).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(2999);
    });
    expect(onPoll).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(1);
    });
    expect(onPoll).toHaveBeenCalledTimes(2);

    await act(async () => {
      vi.advanceTimersByTime(4500);
    });
    expect(onPoll).toHaveBeenCalledTimes(3);
  });
});
