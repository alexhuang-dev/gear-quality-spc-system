from core.config import DefectRateMode, load_runtime_config, load_specs
from core.spc import calculate, parse_csv


SAMPLE_CSV = """批次号,检测时间,件号,齿距累计偏差(μm),齿圈径向跳动(μm),公法线长度变动(μm),齿形误差(μm),齿向误差(μm),缺陷数量
P202407001,2024-07-01 08:00,G001,12,15,8,6.0,7.0,0
P202407001,2024-07-01 08:05,G002,12,15,8,6.1,7.1,1
P202407001,2024-07-01 08:10,G003,13,16,9,6.0,7.0,0
"""


def test_calculate_returns_expected_structure():
    df = parse_csv(SAMPLE_CSV)
    config = load_runtime_config({"defect_rate_mode": DefectRateMode.BINARY.value})
    result = calculate(df, load_specs(), config, csv_text=SAMPLE_CSV)
    assert result["schema_version"] == "gear_spc_v9"
    assert result["batch_numbers"] == ["P202407001"]
    assert result["defect_rate"] == 0.333333
    assert "齿形误差(μm)" in result["metrics"]
    assert result["overall_min_cpk"] is not None
