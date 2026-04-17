export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface JobCreateResponse {
  job_id: string;
  status: JobStatus;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  final_recommendation: string;
  recommendation_reason: string;
  report_path: string;
  logs: string[];
  error: string;
  metadata: Record<string, string>;
}

const apiBase =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function createJob(input: {
  resumeFile: File;
  candidateName: string;
  jobDescription: string;
  requiredSkills: string;
}): Promise<JobCreateResponse> {
  const formData = new FormData();
  formData.append("resume", input.resumeFile);
  formData.append("candidate_name", input.candidateName);
  formData.append("job_description", input.jobDescription);
  formData.append("required_skills", input.requiredSkills);

  const response = await fetch(`${apiBase}/api/jobs`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await extractError(response));
  }

  return (await response.json()) as JobCreateResponse;
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${apiBase}/api/jobs/${jobId}`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await extractError(response));
  }

  return (await response.json()) as JobStatusResponse;
}

export function getReportDownloadUrl(jobId: string): string {
  return `${apiBase}/api/jobs/${jobId}/report`;
}

async function extractError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    // no-op fallback
  }
  return `Request failed with status ${response.status}`;
}
