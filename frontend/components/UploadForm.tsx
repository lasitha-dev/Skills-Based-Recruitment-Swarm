"use client";

import { FormEvent, useMemo, useState } from "react";

interface UploadFormProps {
  onSubmit: (payload: {
    resumeFile: File;
    candidateName: string;
    jobDescription: string;
    requiredSkills: string;
  }) => Promise<void>;
  isSubmitting: boolean;
}

export function UploadForm({ onSubmit, isSubmitting }: Readonly<UploadFormProps>): JSX.Element {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [candidateName, setCandidateName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [error, setError] = useState("");

  const submitLabel = useMemo(() => {
    if (isSubmitting) {
      return "Launching Pipeline...";
    }
    return "Start Agentic Evaluation";
  }, [isSubmitting]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");

    if (!resumeFile) {
      setError("Upload a PDF or DOCX resume first.");
      return;
    }

    const extension = resumeFile.name.split(".").pop()?.toLowerCase() ?? "";
    if (!(extension === "pdf" || extension === "docx")) {
      setError("Only PDF and DOCX files are supported.");
      return;
    }

    try {
      await onSubmit({
        resumeFile,
        candidateName,
        jobDescription,
        requiredSkills,
      });
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : "Failed to submit job.";
      setError(message);
    }
  }

  return (
    <form className="panel upload-panel" onSubmit={handleSubmit}>
      <h2>Resume Ingestion</h2>
      <p className="muted">Upload resume, define role context, and trigger the sequential MARS agent pipeline.</p>

      <label htmlFor="resume">Resume File (PDF or DOCX)</label>
      <input
        id="resume"
        type="file"
        accept=".pdf,.docx"
        onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
        disabled={isSubmitting}
      />

      <label htmlFor="candidateName">Candidate Name (Optional)</label>
      <input
        id="candidateName"
        type="text"
        placeholder="e.g., Alice Johnson"
        value={candidateName}
        onChange={(event) => setCandidateName(event.target.value)}
        disabled={isSubmitting}
      />

      <label htmlFor="jobDescription">Job Description (Optional)</label>
      <textarea
        id="jobDescription"
        rows={4}
        placeholder="Paste role expectations..."
        value={jobDescription}
        onChange={(event) => setJobDescription(event.target.value)}
        disabled={isSubmitting}
      />

      <label htmlFor="requiredSkills">Required Skills (Comma Separated)</label>
      <input
        id="requiredSkills"
        type="text"
        placeholder="Python, AWS, Docker"
        value={requiredSkills}
        onChange={(event) => setRequiredSkills(event.target.value)}
        disabled={isSubmitting}
      />

      {error ? <p className="error-box">{error}</p> : null}

      <button type="submit" disabled={isSubmitting}>{submitLabel}</button>
    </form>
  );
}
