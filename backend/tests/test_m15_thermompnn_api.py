from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())
VARIANT_KEY = "7-55156538-A-C"


def test_variant_list_and_stability_evidence_join_prediction_by_variant_and_accession() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"scope": "canonical", "start": 338, "end": 338, "limit": 50},
    )
    assert response.status_code == 200
    item = next(row for row in response.json()["items"] if row["variant_key"] == VARIANT_KEY)
    prediction = item["stability_prediction"]
    assert prediction["source"] == "ThermoMPNN"
    assert prediction["unit"] == "kcal/mol"
    assert prediction["direction"] == "small_predicted_change"
    assert prediction["ddg"] == -0.06067943572998047

    stability_evidence = client.get(
        f"/api/v1/variants/{VARIANT_KEY}/evidence/stability",
        params={"protein_accession": "P00533"},
    )
    assert stability_evidence.status_code == 200
    assert stability_evidence.json()["prediction"] == prediction


def test_sequence_overview_and_bounded_sites_expose_distributions_not_facts() -> None:
    overview = client.get(
        "/api/v1/proteins/P00533/sequence/overview", params={"bins": 400},
    )
    assert overview.status_code == 200
    body = overview.json()
    assert len(body["stability_bins"]) == 400
    assert body["stability_totals"] == {
        "predicted_variants": 2790,
        "canonical_sites": 1117,
        "distinct_substitutions": 2700,
    }
    assert all("variant_key" not in item for item in body["stability_bins"])

    sites = client.get(
        "/api/v1/proteins/P00533/sites",
        params={"start": 338, "end": 338, "tracks": "stability"},
    )
    assert sites.status_code == 200
    rows = sites.json()["tracks"]["stability"]
    assert len(rows) == 1
    assert rows[0]["position"] == 338
    assert rows[0]["distinct_substitution_count"] == 1
    assert rows[0]["ddg_median"] == -0.06067943572998047


def test_site_preview_keeps_stability_semantics_independent() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/variants/site-preview",
        params={"position": 338, "limit": 12},
    )
    assert response.status_code == 200
    item = next(row for row in response.json()["items"] if row["variant_key"] == VARIANT_KEY)
    assert item["stability_prediction"]["direction"] == "small_predicted_change"


def test_stability_site_detail_returns_each_distinct_substitution_bounded() -> None:
    response = client.get("/api/v1/proteins/P00533/stability/sites/252")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "ThermoMPNN"
    assert body["unit"] == "kcal/mol"
    assert body["ref_aa"] == "R"
    assert len(body["substitutions"]) == 6
    assert len({item["alt_aa"] for item in body["substitutions"]}) == 6
    assert body["ddg_min"] == min(item["ddg"] for item in body["substitutions"])
    assert body["ddg_max"] == max(item["ddg"] for item in body["substitutions"])
    assert body["response_bounds"] == {"complete": True, "max_substitutions": 19}
