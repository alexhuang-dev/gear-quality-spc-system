import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app


ASCII_CSV = """batch_no,time,part_id,metric_a,metric_b,defect_count
LOT001,2024-07-01 08:00,P001,12,4,0
LOT001,2024-07-01 08:05,P002,13,5,0
LOT001,2024-07-01 08:10,P003,14,6,1
LOT001,2024-07-01 08:15,P004,15,5,0
"""

ASCII_SPECS = {
    "metric_a": {"USL": 20, "LSL": 0},
    "metric_b": {"USL": 10, "LSL": 0},
}


def test_ready_and_public_config(monkeypatch, tmp_path):
    monkeypatch.setenv("GEAR_OUTPUT_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("GEAR_HISTORY_DB_PATH", str(tmp_path / "history.db"))
    with TestClient(app) as client:
        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["output_dir"] == str(tmp_path / "reports")

        public_config = client.get("/config/public")
        assert public_config.status_code == 200
        assert public_config.json()["output_dir"] == str(tmp_path / "reports")


def test_analyze_file_endpoint_and_report_output(tmp_path):
    config = {
        "history_db_path": str(tmp_path / "history.db"),
        "checkpoint_db_path": str(tmp_path / "checkpoints.db"),
        "output_dir": str(tmp_path / "reports"),
        "generate_pdf": False,
    }
    with TestClient(app) as client:
        response = client.post(
            "/analyze-file",
            files={"file": ("sample.csv", ASCII_CSV.encode("utf-8"), "text/csv")},
            data={
                "specs_json": json.dumps(ASCII_SPECS),
                "config_json": json.dumps(config),
            },
        )

    assert response.status_code == 200
    data = response.json()
    html_path = Path(data["report_paths"]["html_report_path"])
    html_text = html_path.read_text(encoding="utf-8")
    assert "Gear SPC Production Report" in html_text
    assert "Metric Summary" in html_text
    assert data["spc_result"]["batch_numbers"] == ["LOT001"]
