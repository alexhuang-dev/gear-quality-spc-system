# Gear Quality Production Deployment

This is the production-oriented package for the gear SPC system. The architecture is:

- `api/`: FastAPI service
- `graph/`: LangGraph orchestration with deterministic fallback
- `core/`: SPC, history, reporting, alerts, harness, charts
- `services/auto_runner.py`: incoming CSV watcher
- `dashboard/streamlit_app.py`: operations dashboard
- `langflow_integration/gear_spc_component.py`: Langflow presentation entry

## What is production-ready in this package

- Deterministic SPC computation and status grading
- SQLite history persistence across sessions
- Western Electric 8-rule evaluation
- Harness machine evaluation with regression endpoint
- HTML report + JSON report + SVG charts
- Optional PDF generation
- Webhook alert payload generation and test endpoint
- Background watcher for new CSV files
- Streamlit dashboard
- Environment-variable based runtime configuration
- Docker and Docker Compose deployment skeleton
- Windows one-click stack start/stop scripts

## Recommended local startup

1. Install dependencies into `.venv`
2. Start the stack:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_production_stack.ps1
```

3. Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/ready`
- Dashboard: `http://127.0.0.1:8501`

## Recommended container startup

1. Copy `.env.example` to `.env`
2. Adjust webhook and Langfuse values if needed
3. Run:

```bash
docker compose -f docker-compose.production.yml up --build -d
```

## Langflow entry

Use:

- `New Flow - v9.3 api-frontend-prompt-merge-friendly.json`

And the custom component:

- `langflow_integration/gear_spc_component.py`

Langflow should remain the showcase/presentation layer. The API is the source of truth.

## Important production caveats

This package is production-oriented, but real factory deployment still requires external decisions:

1. Final spec limits must come from real process standards, not synthetic defaults.
2. Webhook URL must be replaced with your real WeCom/Feishu endpoint.
3. Langfuse keys must be configured if observability is required.
4. PDF generation may need OS-level dependencies on the target host.
5. MES/ERP/PLC integration is not bundled; it must be adapted to the target factory environment.

## Smoke checklist

- `GET /health` returns `ok`
- `GET /ready` returns runtime paths and history count
- `POST /regression` passes all golden cases
- `POST /alerts/test` returns `sent_http_200` or the expected enterprise webhook code
- Drop a CSV into `data/incoming/` and confirm it moves to `data/processed/`
- Confirm a new HTML report and charts appear under `data/reports/`
