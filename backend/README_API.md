# Visual Investigator API

FastAPI server for face search.

## Run

From project root:

```bash
cd backend
uvicorn api_server:app --reload --host 0.0.0.0
```

Or from project root with module path:

```bash
uvicorn backend.api_server:app --reload --host 0.0.0.0
```
(Requires `backend` to be on PYTHONPATH or run as a package.)

API: http://localhost:8000
