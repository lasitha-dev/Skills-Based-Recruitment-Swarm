# MARS Backend Adapter

This module exposes a small FastAPI adapter to run the existing LangGraph pipeline asynchronously from a UI.

## Run

```bash
uvicorn backend.api:app --reload --port 8000
```

## Endpoints

- `GET /api/health`
- `POST /api/jobs` (multipart: `resume`, optional `candidate_name`, `job_description`, `required_skills`)
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/report`

## Notes

- Uploads are saved in `data/uploads/`.
- Job metadata is saved in `data/jobs/`.
- Worker process executes the existing `run_mars_pipeline` function.
