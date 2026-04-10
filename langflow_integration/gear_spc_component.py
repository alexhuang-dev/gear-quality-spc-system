from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from lfx.custom.custom_component.component import Component
from lfx.io import MultilineInput, Output, StrInput
from lfx.schema.data import Data


class GearSPCComponent(Component):
    display_name = "Gear SPC API"
    description = "Call the FastAPI production backend and return structured SPC results."
    icon = "activity"
    documentation = "http://localhost:8000/docs"

    inputs = [
        MultilineInput(
            name="csv_text",
            display_name="CSV Text",
            info="Paste CSV text here. Leave empty if you provide a file path.",
            value="",
            required=False,
            input_types=["Message"],
        ),
        StrInput(
            name="csv_file_path",
            display_name="CSV File Path",
            info="Optional local CSV file path. Used when CSV Text is empty.",
            value="",
            required=False,
        ),
        MultilineInput(
            name="specs_json",
            display_name="Specs JSON",
            info="Optional JSON spec overrides.",
            value="",
            required=False,
        ),
        MultilineInput(
            name="config_json",
            display_name="Config JSON",
            info="Optional runtime config.",
            value="",
            required=False,
        ),
        StrInput(
            name="api_url",
            display_name="API URL",
            value="http://127.0.0.1:8000",
            required=True,
        ),
        StrInput(
            name="timeout_seconds",
            display_name="Timeout Seconds",
            value="300",
            required=True,
        ),
    ]

    outputs = [
        Output(display_name="Analysis", name="analysis", type_=Data, method="build_analysis"),
        Output(display_name="SPC JSON", name="spc_json", type_=Data, method="build_spc_json"),
        Output(display_name="Harness JSON", name="harness_json", type_=Data, method="build_harness_json"),
        Output(display_name="Report Paths", name="report_paths", type_=Data, method="build_report_paths"),
    ]

    _response_cache: dict[str, Any] | None = None

    def _load_csv(self) -> str:
        if str(self.csv_text or "").strip():
            return str(self.csv_text)
        path = Path(str(self.csv_file_path or "").strip())
        if not path.exists():
            raise ValueError("No CSV text provided and CSV file path does not exist.")
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return path.read_text(encoding="utf-8", errors="ignore")

    def _parse_json(self, raw: str) -> dict[str, Any] | None:
        text = str(raw or "").strip()
        if not text:
            return None
        return json.loads(text)

    def _call_api(self) -> dict[str, Any]:
        if self._response_cache is not None:
            return self._response_cache

        payload = {
            "csv": self._load_csv(),
            "specs": self._parse_json(self.specs_json),
            "config": self._parse_json(self.config_json),
        }
        response = requests.post(
            f"{str(self.api_url).rstrip('/')}/analyze",
            json=payload,
            timeout=float(self.timeout_seconds or 300),
        )
        response.raise_for_status()
        self._response_cache = response.json()
        self.status = self._response_cache
        return self._response_cache

    def build_analysis(self) -> Data:
        return Data(data=self._call_api())

    def build_spc_json(self) -> Data:
        return Data(data={"spc_result": self._call_api().get("spc_result")})

    def build_harness_json(self) -> Data:
        return Data(data={"harness_eval": self._call_api().get("harness_eval")})

    def build_report_paths(self) -> Data:
        return Data(data={"report_paths": self._call_api().get("report_paths")})
