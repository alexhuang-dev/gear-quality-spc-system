# Gear Quality SPC System

![Python](https://img.shields.io/badge/Python-Production-blue)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-black)
![Status](https://img.shields.io/badge/Status-v1.0.0-success)

[中文说明](README.zh-CN.md)

Gear Quality SPC System started from a simple engineering constraint: in quality analysis, some parts of the pipeline can be expressive, but the numbers cannot be negotiable.

That decision shaped the whole project. SPC metrics, control limits, historical comparisons, and release checks are computed by deterministic Python code. The presentation layer can still be conversational, but it is not allowed to become the source of truth. I kept Langflow in the project because it is useful for demos and workflow presentation, but I pushed it out of the critical path. The production backbone is a Python service stack.

The result is a system that takes gear inspection CSV data, turns it into a repeatable SPC pipeline, compares it against historical runs, generates reports and charts, and then runs a harness layer over the final output to check that the story still matches the numbers.

![Architecture Overview](docs/assets/architecture-overview.svg)

## Design Decisions

### 1. Deterministic core before language layer

I did not want quality conclusions to depend on prompt phrasing. For that reason, SPC calculation, Western Electric rules, historical comparison, and status grading all live in code under `core/`. The LLM-facing layer is allowed to explain results, not invent them.

### 2. Langflow as interface, not dependency

The project includes a final Langflow flow because it is good for demonstration and workflow visibility. But the production path is built around `FastAPI`, `LangGraph`, `SQLite`, and `Streamlit`. If Langflow disappeared tomorrow, the backend would still run.

### 3. Validation was part of the first version, not an afterthought

I treated output consistency as a product requirement. The system includes a harness evaluation layer, golden-case regression tests, and a release process, because a report generator without a reliability story is not very interesting in an industrial setting.

## What Is In The Repo

```text
core/                  SPC, history, charts, reports, alerts, harness logic
graph/                 LangGraph orchestration with deterministic fallback
api/                   FastAPI service layer
harness/               golden-case regression helpers
services/              background auto-runner
dashboard/             Streamlit dashboard
langflow_integration/  Langflow custom component
tests/                 unit tests and regression fixtures
data/specs/            default specification configuration
```

## Current Scope

Today the system covers the software side of a production-style SPC workflow:

- deterministic SPC computation
- Western Electric 8-rule evaluation
- SQLite-backed historical memory
- report and chart generation
- webhook-ready alert payloads
- machine-checkable harness validation
- dashboard visibility
- optional Langflow presentation flow

What it does not pretend to solve by itself is the factory integration work: real spec ownership, MES/ERP/PLC interfaces, and on-site data contracts still need to come from the actual environment.

## Running The System

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

## Langflow Entry

If you want the visual workflow version, use:

- `New Flow - v9.3 api-frontend-prompt-merge-friendly.json`
- `langflow_integration/gear_spc_component.py`

That flow calls the backend API. It is the front end, not the system boundary.

## API Endpoints

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

## Testing

```powershell
.\.venv\Scripts\python -m pytest tests -q
```

## Additional Docs

- `PRODUCTION_DEPLOYMENT.md`
- `FINAL_ARCHITECTURE.md`
- `PROJECT_INTRO_BILINGUAL.md`
- `INTERVIEW_GUIDE.zh-CN.md`
- `SHOWCASE.md`
