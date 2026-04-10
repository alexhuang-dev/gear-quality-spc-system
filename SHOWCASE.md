# Showcase Guide

## Architecture Preview

![Architecture Overview](docs/assets/architecture-overview.svg)

## What To Show In A Demo

### 1. Explain the system boundary

Start with the key point:

- deterministic facts are produced by Python
- natural-language explanation is optional and sits outside the source of truth

That one sentence makes the architecture feel much more serious.

### 2. Show the production flow

Suggested order:

1. CSV input
2. FastAPI `/analyze`
3. SPC + Western Electric + history
4. Harness validation
5. HTML report and SVG chart output
6. Dashboard visibility
7. Optional Langflow front-end demo

### 3. Explain why Langflow is optional

This is important in interviews:

- the backend is pure Python and fully runnable without Langflow
- Langflow is kept as a visual workflow layer for demos and business-facing presentation

### 4. Show the files that matter

Point people to:

- `api/main.py`
- `core/spc.py`
- `core/history.py`
- `core/harness.py`
- `graph/build.py`
- `dashboard/streamlit_app.py`
- `langflow_integration/gear_spc_component.py`

## Suggested Screenshot Set

If you want to make the repository even stronger later, the most valuable screenshots are:

1. Langflow final workflow
2. Dashboard home page
3. HTML report page
4. Harness result JSON
5. GitHub repo home page

## Interview Framing

This project is best presented as:

> A production-oriented industrial SPC system that separates deterministic quality computation from LLM-facing explanation, while preserving historical memory, validation, reporting, and deployment readiness.
