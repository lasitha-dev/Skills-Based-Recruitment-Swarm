# MARS Frontend (Next.js)

Modern UI for uploading resumes and tracking async MARS pipeline runs.

## Setup

1. Install deps:
   ```bash
   npm install
   ```
2. Create `.env.local`:
   ```bash
   NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
   ```
3. Run dev server:
   ```bash
   npm run dev
   ```

## Flow

- Upload PDF or DOCX
- Submit optional candidate name + job description + required skills
- Poll job status every 1-2 seconds
- View recommendation + download generated report
