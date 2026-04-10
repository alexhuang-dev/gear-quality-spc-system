from fastapi.testclient import TestClient

from api.main import app


CSV_TEXT = """批次号,检测时间,件号,齿距累计偏差(μm),齿圈径向跳动(μm),公法线长度变动(μm),齿形误差(μm),齿向误差(μm),缺陷数量
P202407002,2024-07-02 08:00,G001,12,15,8,8.7,7.0,0
P202407002,2024-07-02 08:05,G002,12,15,8,8.8,7.1,1
P202407002,2024-07-02 08:10,G003,12,15,8,8.9,7.1,0
P202407002,2024-07-02 08:15,G004,12,15,8,9.0,7.1,1
"""


def test_analyze_endpoint(tmp_path):
    client = TestClient(app)
    response = client.post(
        "/analyze",
        json={
            "csv": CSV_TEXT,
            "config": {
                "history_db_path": str(tmp_path / "history.db"),
                "checkpoint_db_path": str(tmp_path / "checkpoints.db"),
                "output_dir": str(tmp_path / "reports"),
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["spc_result"]["schema_version"] == "gear_spc_v9"
    assert "harness_eval" in data
    assert "report_paths" in data
