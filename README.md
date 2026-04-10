# Gear Quality SPC System

A production-oriented gear quality analysis system built around deterministic SPC computation, LangGraph orchestration, FastAPI services, Langflow presentation, and harness-based machine validation.

## What this project does

- Parses gear inspection CSV data
- Computes SPC statistics deterministically
- Evaluates Western Electric 8 rules
- Persists history in SQLite for cross-run comparison
- Generates JSON, HTML, and SVG reporting artifacts
- Produces machine-checkable harness evaluation results
- Supports alert payload generation for webhook delivery
- Exposes a FastAPI backend for Langflow and other clients
- Provides a Streamlit dashboard for recent run visibility
- Supports automatic folder-based CSV processing

## Architecture

```text
core/                  deterministic SPC, history, charts, reports, alerts, harness
graph/                 LangGraph orchestration with deterministic fallback
api/                   FastAPI service layer
harness/               golden-case regression helpers
services/              background auto-runner
dashboard/             Streamlit operational dashboard
langflow_integration/  Langflow custom component
tests/                 unit tests and golden-case regression tests
data/specs/            default specification configuration
```

## Final Langflow entry

- Flow file: `New Flow - v9.3 api-frontend-prompt-merge-friendly.json`
- Custom component: `langflow_integration/gear_spc_component.py`

Langflow is the presentation layer. The FastAPI backend is the source of truth.

## Main runtime features

- Deterministic SPC engine
- Historical comparison across runs
- Western Electric rule analysis
- Harness validation with regression endpoint
- HTML report with embedded charts and plain-language summary
- Optional PDF generation
- Dashboard summary endpoint
- Incoming CSV watcher
- Docker deployment skeleton
- Windows startup scripts

## Quick start

### Local

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\start_production_stack.ps1
```

Open:

- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Ready check: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)
- Dashboard: [http://127.0.0.1:8501](http://127.0.0.1:8501)

### Docker

```bash
cp .env.example .env
docker compose -f docker-compose.production.yml up --build -d
```

## API endpoints

- `GET /health`
- `GET /ready`
- `GET /config/public`
- `POST /analyze`
- `POST /analyze-file`
- `GET /history`
- `GET /report/{run_id}`
- `GET /dashboard/summary`
- `POST /regression`
- `POST /alerts/test`

## Test

```powershell
.\.venv\Scripts\python -m pytest tests -q
```

## Notes before real factory deployment

- Specification limits must be replaced with real process standards
- Webhook URLs must be configured for real alert delivery
- Langfuse keys are optional and only needed if observability is enabled
- MES/ERP/PLC integration is project-specific and not bundled here

## Additional docs

- `PRODUCTION_DEPLOYMENT.md`
- `FINAL_ARCHITECTURE.md`
- `langflow_integration/SETUP.md`
