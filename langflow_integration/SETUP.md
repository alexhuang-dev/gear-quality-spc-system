# Langflow Setup For Gear SPC Production Backend

## 1. Start the API

```powershell
powershell -ExecutionPolicy Bypass -File .\start_production_stack.ps1
```

Default URL:

```text
http://127.0.0.1:8000
```

Dashboard URL:

```text
http://127.0.0.1:8501
```

## 2. Add the custom component

Use:

```text
langflow_integration/gear_spc_component.py
```

Paste the component into Langflow custom components, or place it where your
Langflow instance loads local custom components.

## 3. Import the final frontend flow

Use:

```text
New Flow - v9.3 api-frontend-prompt-merge-friendly.json
```

## 4. Minimal flow

```text
Chat Input
  -> Gear SPC API
      -> SPC JSON -> Agent 1 SPC Analyst
      -> SPC JSON -> Agent 2 Quality Plan
      -> Analysis -> Report Writer
      -> Harness JSON -> Harness QA Agent
```

## 5. Recommended API config

Example `Config JSON`:

```json
{
  "history_db_path": "data/history.db",
  "checkpoint_db_path": "data/langgraph_checkpoints.sqlite",
  "output_dir": "data/reports",
  "history_limit": 10,
  "generate_artifacts": true,
  "generate_pdf": false,
  "western_electric_enabled": true,
  "alert_cpk_threshold": 1.0,
  "defect_rate_mode": "binary"
}
```

The backend also supports:

- `POST /analyze-file` for multipart file upload
- `GET /ready` for readiness
- `GET /config/public` for current runtime config
- `POST /regression` for golden-case regression

The custom component also exposes `Timeout Seconds`, so long-running report jobs
do not fail in Langflow before the backend finishes.

## 6. What Langflow should do

- Display and narrate
- Run SPC/quality/report Agents
- Show final QA summary

## 7. What Langflow should not do

- Recalculate Cpk
- Decide core status by itself
- Rewrite structured facts from the backend

The backend API is the source of truth. Langflow should explain and present it.
