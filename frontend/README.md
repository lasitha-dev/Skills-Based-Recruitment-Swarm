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

## Testing Runbook

### Frontend tests

1. Run all frontend tests:
   ```bash
   npm run test
   ```
2. Run in watch mode while editing:
   ```bash
   npm run test:watch
   ```

### What frontend tests cover

- Terminal-state polling stop behavior
- Poll retry behavior after transient failures
- Poll-error message rendering
- Home page submit -> poll -> terminal state integration flow (mocked API)

### Backend adapter tests (repository root)

```bash
pytest tests/test_backend_api_adapter.py -q
```

These validate API upload constraints, queued job creation path, status payload shape, and report availability rules.
