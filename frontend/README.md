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

### Browser E2E (Playwright)

1. Install Playwright browsers:
   ```bash
   npm run e2e:install
   ```
2. Start backend (`http://127.0.0.1:8000`) and frontend (`http://127.0.0.1:3000`) manually.
3. Run the real-backend E2E upload flow:
   ```bash
   RUN_REAL_BACKEND_E2E=1 npm run e2e
   ```

Notes:
- The E2E tests upload a single PDF file and a single DOCX file in separate flows, and assert that the UI receives job state.
- Without `RUN_REAL_BACKEND_E2E=1`, the real-backend spec is skipped by design.

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
