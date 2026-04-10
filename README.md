# Gear Quality SPC System

[中文说明](README.zh-CN.md)

A production-oriented gear quality analysis system for industrial SPC workflows, built with deterministic Python computation, LangGraph orchestration, FastAPI services, machine-checkable harness evaluation, reporting, and an optional Langflow presentation layer.

## Overview

This project is designed to make gear inspection data operational instead of static. It takes CSV-based inspection results, computes SPC metrics deterministically, compares runs against historical batches, generates reports and charts, and produces a harness evaluation layer that checks whether the final output is internally consistent.

The core production path is **pure Python**:

- `FastAPI` for service exposure
- `LangGraph` for orchestration, with deterministic fallback
- `SQLite` for history persistence
- `Streamlit` for dashboard visibility
- `pytest` + golden cases for regression checks

`Langflow` is **optional**. It is included as a visual presentation and demo entry, not as the system of record.

## What This Project Does

- Parses gear inspection CSV data
- Computes SPC metrics deterministically
- Evaluates Western Electric 8 rules
- Persists run history in SQLite
- Compares current batches against previous runs
- Generates JSON, HTML, SVG, and optional PDF outputs
- Produces machine-checkable harness evaluation results
- Builds alert payloads for webhook delivery
- Exposes a backend API for Langflow or other clients
- Provides a Streamlit dashboard for operational visibility
- Supports automatic folder-based CSV ingestion

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

## Runtime Modes

### 1. Pure Python Production Mode

Use the backend directly through FastAPI, the dashboard, and the auto-runner.

This is the recommended deployment mode for real engineering use.

### 2. Langflow Showcase Mode

Use:

- `New Flow - v9.3 api-frontend-prompt-merge-friendly.json`
- `langflow_integration/gear_spc_component.py`

In this mode, Langflow is the presentation layer. The backend API remains the source of truth.

## Main Features

- Deterministic SPC engine
- Historical comparison across runs
- Western Electric rule analysis
- Harness validation with regression endpoint
- HTML report with embedded charts and plain-language summary
- Optional PDF generation
- Alert payload generation and webhook testing
- Dashboard summary endpoint
- Incoming CSV watcher
- Docker deployment skeleton
- Windows startup scripts

## Quick Start

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

## FAQ

### Is this a pure Python system?

Yes for the production backend.

The core system can run without Langflow. The production stack is Python-based and includes FastAPI, LangGraph, SQLite, Streamlit, and the harness/test layer.

### Does it require Langflow?

No.

Langflow is optional and mainly useful for demos, workflows, and visual presentation. If Langflow is removed, the backend still works.

### Is it ready for a real factory?

The software architecture is production-oriented, but actual deployment still depends on:

- Real specification limits
- Real webhook configuration
- Real MES/ERP/PLC integration requirements

## Additional Docs

- `PRODUCTION_DEPLOYMENT.md`
- `FINAL_ARCHITECTURE.md`
- `langflow_integration/SETUP.md`
