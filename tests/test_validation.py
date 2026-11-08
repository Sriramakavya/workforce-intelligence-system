from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data_generator import generate, RAW, TRUTH
from src.validation import validate
from src.analytics import load_tables, utilization_report, forecast_demand, forecast_segmented_demand, detect_anomalies

def test_generated_data_integrity():
    generate("starter", seed=20261022)
    result = validate(RAW)
    assert result.passed.all(), result[~result.passed].to_dict("records")

def test_required_entities_and_relationships():
    tables = load_tables()
    required = {"employee", "role", "skill", "employeeskill", "project", "demandplan",
                "allocation", "availability", "training", "gapanalysis", "allocationevent"}
    assert required.issubset(tables)
    assert tables["allocationevent"].allocation_id.isin(tables["allocation"].allocation_id).all()

def test_edge_cases_are_detected_and_labelled():
    generate("starter", seed=20261022)
    truth = __import__("pandas").read_csv(TRUTH / "ground_truth.csv")
    found = detect_anomalies(load_tables())
    expected = set(truth.issue_type)
    assert expected.issubset(set(found.issue_type))
    for row in truth.itertuples(index=False):
        assert ((found.issue_type == row.issue_type) & (found.record_id == row.record_id)).any()

def test_capacity_and_forecast_outputs():
    t = load_tables()
    util = utilization_report(t)
    assert {"utilization", "capacity_balance_fte", "utilization_status"}.issubset(util.columns)
    forecast, metrics = forecast_demand(t, periods=12)
    assert len(forecast) == 12
    assert metrics["mae"] is not None and metrics["rmse"] is not None
    segmented = forecast_segmented_demand(t, periods=12)
    assert {"project", "role"}.issubset(set(segmented.entity_type))
    assert segmented.groupby("entity_type").size().min() >= 12


def test_fixed_seed_reproducibility():
    import json
    generate("starter", seed=20261022)
    first = json.loads((RAW / "checksums.json").read_text())
    generate("starter", seed=20261022)
    second = json.loads((RAW / "checksums.json").read_text())
    assert first == second
