import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, createJob, getJobStatus, getReportDownloadUrl } from "@/lib/api";

describe("frontend api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("createJob returns parsed payload on success", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: "job-100", status: "queued" }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const result = await createJob({
      resumeFile: new File(["pdf"], "resume.pdf", { type: "application/pdf" }),
      candidateName: "Jane",
      jobDescription: "Need Python",
      requiredSkills: "Python, AWS",
    });

    expect(result).toEqual({ job_id: "job-100", status: "queued" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/jobs",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("getJobStatus throws ApiError with backend detail for non-200 responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Job abc not found" }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await expect(getJobStatus("abc")).rejects.toEqual(
      expect.objectContaining({
        name: "ApiError",
        message: "Job abc not found",
        statusCode: 404,
      }),
    );
  });

  it("createJob throws fallback ApiError when error payload is malformed", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("Invalid JSON");
      },
    });

    vi.stubGlobal("fetch", fetchMock);

    await expect(
      createJob({
        resumeFile: new File(["pdf"], "resume.pdf", { type: "application/pdf" }),
        candidateName: "Jane",
        jobDescription: "Need Python",
        requiredSkills: "Python, AWS",
      }),
    ).rejects.toEqual(
      expect.objectContaining({
        name: "ApiError",
        message: "Request failed with status 500",
        statusCode: 500,
      }),
    );
  });

  it("getReportDownloadUrl returns deterministic endpoint", () => {
    expect(getReportDownloadUrl("job-200")).toBe("http://127.0.0.1:8000/api/jobs/job-200/report");
  });

  it("ApiError exposes statusCode", () => {
    const error = new ApiError("failed", 418);
    expect(error.name).toBe("ApiError");
    expect(error.message).toBe("failed");
    expect(error.statusCode).toBe(418);
  });
});
