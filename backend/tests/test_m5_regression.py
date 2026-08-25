from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
GENERATED = Path(__file__).resolve().parents[2] / "data" / "generated"


def test_api_explicitly_disables_browser_caching_for_local_rebuilds() -> None:
    success = client.get("/api/v1/search", params={"q": "P00533"})
    assert success.status_code == 200
    assert success.headers["cache-control"] == "no-store"

    missing = client.get("/api/v1/proteins/NOT_A_PROTEIN")
    assert missing.status_code == 404
    assert missing.headers["cache-control"] == "no-store"


def test_every_bounded_public_list_rejects_oversized_pages() -> None:
    requests = (
        ("/api/v1/search", {"q": "EGFR", "limit": 51}),
        ("/api/v1/proteins/P00533/variants", {"limit": 201}),
        (
            "/api/v1/proteins/P00533/qtl",
            {"source": "GTEx", "qtl_type": "eQTL", "limit": 201},
        ),
        (
            "/api/v1/proteins/P00533/interactions",
            {"source": "BioGRID", "limit": 201},
        ),
        ("/api/v1/proteins/P00533/interactions/mutation-effects", {"limit": 201}),
        ("/api/v1/proteins/P00533/diseases", {"source": "gencc", "limit": 201}),
        (
            "/api/v1/proteins/P00533/diseases/hpo",
            {"category": "observed", "limit": 201},
        ),
    )
    for path, params in requests:
        response = client.get(path, params=params)
        assert response.status_code == 422, (path, response.text)


def test_large_detail_resources_require_disambiguating_filters() -> None:
    assert client.get("/api/v1/proteins/P00533/qtl").status_code == 422
    assert client.get(
        "/api/v1/proteins/P00533/qtl", params={"source": "GTEx"}
    ).status_code == 422
    assert client.get("/api/v1/proteins/P00533/interactions").status_code == 422
    assert client.get("/api/v1/proteins/P00533/diseases/hpo").status_code == 422
    assert client.get("/api/v1/variants/7-1-A-T").status_code == 404


def test_prefix_suggestion_limit_still_applies_but_exact_sets_are_complete() -> None:
    prefix = client.get("/api/v1/search", params={"q": "ENSG", "limit": 2})
    assert prefix.status_code == 200
    prefix_body = prefix.json()
    assert len(prefix_body["items"]) == 2
    assert prefix_body["total_or_estimate"]["value"] > 2
    assert prefix_body["applied_filters"]["exact_candidate_set_complete"] is False

    exact = client.get("/api/v1/search", params={"q": "SHORT", "limit": 2})
    assert exact.status_code == 200
    assert len(exact.json()["items"]) == exact.json()["total_or_estimate"]["value"] == 94


def test_annotation_cursor_is_opaque_and_bound_to_its_section() -> None:
    first = client.get(
        "/api/v1/proteins/P0CG48/annotations", params={"section": "reactome"}
    )
    assert first.status_code == 200
    cursor = first.json()["next_cursor"]
    assert cursor and "offset" not in cursor
    second = client.get(
        "/api/v1/proteins/P0CG48/annotations",
        params={"section": "reactome", "cursor": cursor},
    )
    assert second.status_code == 200
    mismatch = client.get(
        "/api/v1/proteins/P0CG48/annotations",
        params={"section": "location", "cursor": cursor},
    )
    assert mismatch.status_code == 400


def test_read_only_requests_do_not_touch_generated_databases() -> None:
    databases = [
        GENERATED / "memvar_core.duckdb",
        GENERATED / "memvar_m2.duckdb",
        GENERATED / "memvar_m3.duckdb",
        GENERATED / "memvar_m4.duckdb",
        GENERATED / "alphagenome" / "alphagenome_catalog.duckdb",
    ]
    before = {path: path.stat().st_mtime_ns for path in databases}
    responses = (
        client.get("/api/v1/proteins/P00533"),
        client.get("/api/v1/proteins/P00533/sequence"),
        client.get(
            "/api/v1/proteins/P00533/expression", params={"modality": "all"}
        ),
        client.get("/api/v1/proteins/P00533/qtl/summary"),
        client.get("/api/v1/proteins/P00533/interactions/summary"),
        client.get("/api/v1/proteins/P00533/diseases"),
        client.get("/api/v1/proteins/P00533/alphagenome/summary"),
    )
    assert all(response.status_code == 200 for response in responses)
    after = {path: path.stat().st_mtime_ns for path in databases}
    assert after == before


def test_sequence_window_and_invalid_cursor_errors_are_clear() -> None:
    too_wide = client.get(
        "/api/v1/proteins/P00533/sequence", params={"start": 1, "end": 501}
    )
    assert too_wide.status_code == 400
    assert "cannot exceed 500" in too_wide.json()["detail"]

    invalid = client.get(
        "/api/v1/proteins/P00533/qtl",
        params={"source": "GTEx", "qtl_type": "eQTL", "cursor": "bad"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Invalid QTL cursor"
