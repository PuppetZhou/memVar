from fastapi.testclient import TestClient

from app.m2 import covalent_pair_id
from app.main import create_app


client = TestClient(create_app())


def test_selected_site_summary_preserves_canonical_evidence_and_stability_distribution() -> None:
    response = client.get("/api/v1/proteins/P00533/sites/252/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["identity"] == {
        "uniprot_accession": "P00533",
        "sequence_id": "P00533",
        "sequence_version": 2,
        "position": 252,
        "reference_residue": "R",
        "coordinate_basis": "canonical_1_based",
    }
    conservation = body["conservation"]
    assert conservation["jsd_conservation"] == 0.6631831222361044
    assert conservation["occupancy"] == 0.995
    assert conservation["neff_site"] == 199.0
    assert conservation["confidence"] == "High"
    stability = body["stability"]
    assert stability["available"] is True
    assert stability["unit"] == "kcal/mol"
    assert stability["ddg_median"] == 0.8168303072452545
    assert stability["ddg_min"] < 0 < stability["ddg_max"]
    assert {item["direction"] for item in stability["substitutions"]} == {
        "predicted_stabilizing", "small_predicted_change", "predicted_destabilizing",
    }
    assert body["response_bounds"]["raw_evidence_json_returned"] is False


def test_selected_site_summary_keeps_both_covalent_endpoints_and_compact_evidence() -> None:
    start = client.get("/api/v1/proteins/P00533/sites/31/summary")
    end = client.get("/api/v1/proteins/P00533/sites/58/summary")

    assert start.status_code == end.status_code == 200
    start_pair = next(pair for pair in start.json()["covalent_pairs"] if pair["start_endpoint"] == 31)
    end_pair = next(pair for pair in end.json()["covalent_pairs"] if pair["end_endpoint"] == 58)
    assert start_pair["pair_id"] == end_pair["pair_id"]
    assert start_pair["start_endpoint"] == 31
    assert start_pair["end_endpoint"] == 58
    assert start_pair["feature_type"] == "Disulfide bond"
    assert {item["source"] for item in start_pair["evidence"] if item["source"]} == {"PubMed", "PDB"}
    assert all("evidence_json" not in item for item in start_pair["evidence"])


def test_covalent_pair_id_without_feature_id_is_stable_across_endpoint_queries() -> None:
    fields = ("Disulfide bond", 31, 58, None, None, None, None, '[{"source":"PDB","id":"1NQL"}]')

    from_start_endpoint = covalent_pair_id("P00533", *fields)
    from_end_endpoint = covalent_pair_id("P00533", *fields)

    assert from_start_endpoint == from_end_endpoint
    assert from_start_endpoint.startswith("P00533:pair:")


def test_selected_site_summary_preserves_missing_as_null_not_zero() -> None:
    response = client.get("/api/v1/proteins/P43627/sites/1/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["stability"]["available"] is False
    assert body["stability"]["ddg_median"] is None
    assert body["stability"]["substitutions"] == []
    assert body["variants"]["total"] == 0
    assert body["variants"]["preview"] == []


def test_selected_site_summary_rejects_out_of_bounds_position() -> None:
    response = client.get("/api/v1/proteins/P00533/sites/1211/summary")

    assert response.status_code == 422
    assert "between 1 and 1210" in response.json()["detail"]
