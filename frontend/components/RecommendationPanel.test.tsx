import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RecommendationPanel } from "@/components/RecommendationPanel";

describe("RecommendationPanel", () => {
  it("shows poll error state distinctly", () => {
    render(
      <RecommendationPanel
        job={null}
        runState="poll-error"
        pollError="Connection timed out"
      />,
    );

    expect(screen.getByText("Recommendation")).toBeInTheDocument();
    expect(screen.getByText(/Status sync interrupted:/)).toBeInTheDocument();
    expect(screen.getByText(/Connection timed out/)).toBeInTheDocument();
  });

  it("shows completed recommendation output", () => {
    render(
      <RecommendationPanel
        runState="completed"
        pollError=""
        job={{
          job_id: "job-1",
          status: "completed",
          final_recommendation: "Strong Hire",
          recommendation_reason: "Excellent skills match",
          report_path: "report.md",
          logs: [],
          error: "",
          metadata: {},
        }}
      />,
    );

    expect(screen.getByText("Strong Hire")).toBeInTheDocument();
    expect(screen.getByText("Excellent skills match")).toBeInTheDocument();
    expect(screen.getByText("Download Generated Report")).toBeInTheDocument();
  });
});
