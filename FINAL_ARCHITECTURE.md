# Gear Quality System Final Architecture

## What stays

- `New Flow - v8 package-harness-final.json`: stable Langflow showcase baseline
- `gear_quality/pipeline.py`: preserved v8 monolithic implementation

## What is new

This production-oriented version is split into explicit layers:

```text
core/      deterministic SPC engine
harness/   golden-case regression helpers
graph/     LangGraph-style orchestration with sequential fallback
api/       FastAPI service
langflow_integration/  single custom component that calls the API
tests/     golden fixtures + pytest tests
data/      specs, reports, SQLite databases
```

## Main entry points

- Core calculation: `core/spc.py`
- Machine harness: `core/harness.py`
- LangGraph orchestration: `graph/build.py`
- FastAPI app: `api/main.py`
- Langflow custom component: `langflow_integration/gear_spc_component.py`

## FastAPI endpoints

- `GET /health`
- `GET /ready`
- `GET /config/public`
- `POST /analyze`
- `POST /analyze-file`
- `GET /history?n=10`
- `GET /report/{run_id}`
- `GET /dashboard/summary`
- `POST /regression`
- `POST /alerts/test`

## Runtime notes

- Default specs file: `data/specs/default.json`
- Default history DB: `data/history.db`
- Default report output dir: `data/reports`
- Incoming CSV watch dir: `data/incoming`
- Processed CSV dir: `data/processed`
- Failed CSV dir: `data/failed_inputs`
- LangGraph package is optional at runtime. If unavailable, `graph/build.py`
  falls back to a deterministic sequential pipeline with the same output shape.
- Environment-variable overrides are supported via `.env` / process env.
- Windows production startup: `start_production_stack.ps1`
- Container startup: `docker-compose.production.yml`

## Output contract

`POST /analyze` returns:

```json
{
  "spc_result": {},
  "harness_eval": {},
  "history_comparison": {},
  "charts": {},
  "report_paths": {},
  "alert_payload": {},
  "metadata": {}
}
```

## Testing

Golden fixtures live in `tests/golden/`:

- `case_001_normal.json`
- `case_002_warning.json`
- `case_003_critical.json`

These are intended to validate normal, warning, and critical scenarios before
shipping changes.
