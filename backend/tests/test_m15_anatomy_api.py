from fastapi.testclient import TestClient

from app.anatomy import mapped_region, normalize_term
from app.main import create_app


client = TestClient(create_app())


def test_crosswalk_uses_only_explicit_normalized_aliases() -> None:
    assert normalize_term("Brain_Cortex") == "brain cortex"
    assert mapped_region("Brain_Cortex") == ("brain", "UBERON:0000955", True)
    assert mapped_region("Whole_Blood") == ("blood", "UBERON:0000178", True)
    assert mapped_region("Esophagus_Mucosa") == ("esophagus", "UBERON:0001043", True)
    assert mapped_region("Artery_Aorta") == ("vasculature", "UBERON:0002049", True)
    assert mapped_region("Brain-Spinal Cord") == ("spinal_cord", "UBERON:0002240", True)
    assert mapped_region("invented pulmonary-like label") == ("other", None, False)


def test_anatomy_summary_is_availability_navigation_without_combined_score() -> None:
    response = client.get("/api/v1/proteins/P00533/anatomy/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["fill_semantics"] == "availability_or_selection_only"
    assert body["cross_modality_score"] is False
    assert len(body["regions"]) == 47
    lung = next(item for item in body["regions"] if item["body_region_id"] == "lung")
    assert lung["has_data"] is True
    assert {item["layer"] for item in lung["evidence"]} >= {"expression", "qtl"}
    assert all(item["raw_filter_terms"] for item in lung["evidence"])
    blood = next(item for item in body["regions"] if item["body_region_id"] == "blood")
    assert {item["layer"] for item in blood["evidence"]} >= {"expression", "gen", "qtl"}
    pituitary = next(item for item in body["regions"] if item["body_region_id"] == "pituitary")
    assert pituitary["ontology_id"] == "UBERON:0000007"
    other = next(item for item in body["regions"] if item["body_region_id"] == "other")
    assert other["mapping_status"] == "explicit"
