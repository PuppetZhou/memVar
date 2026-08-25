from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_go_term_summary_is_bounded_grouped_and_filterable() -> None:
    response = client.get("/api/v1/proteins/P00533/go/terms", params={"aspect": "MF", "limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["total_or_estimate"] == {"value": 21, "kind": "exact"}
    assert body["annotation_count"] == 663
    assert len(body["items"]) == 2
    assert body["next_cursor"]
    assert all(item["aspect"] == "MF" for item in body["items"])
    assert all(item["annotation_count"] >= item["reference_count"] for item in body["items"])
    assert all(item["evidence_codes"] for item in body["items"])
    assert [(item["aspect"], item["term_count"], item["annotation_count"]) for item in body["aspect_counts"]] == [
        ("MF", 21, 663),
        ("BP", 43, 67),
        ("CC", 27, 252),
    ]
    assert all(item["reference_count"] > 0 for item in body["aspect_counts"])
    assert body["applied_filters"]["default_excludes_negated"] is True
    assert body["provenance"] == {
        "source_id": "goa_annotation",
        "display_name": "Gene Ontology Annotation and local GO term dictionary",
        "layer": "annotation",
        "source_release": "GOA ontology 2026-07-26; local GO OBO 2026-06-15",
        "record_grain": "UniProt-GO annotation evidence",
        "caveat": "GOA and the local go-basic.obo snapshot dates differ; NOT annotations remain explicit and do not enter positive summaries.",
    }

    second_page = client.get(
        "/api/v1/proteins/P00533/go/terms",
        params={"aspect": "MF", "limit": 2, "cursor": body["next_cursor"]},
    )
    assert second_page.status_code == 200
    assert {item["go_id"] for item in body["items"]}.isdisjoint(
        {item["go_id"] for item in second_page.json()["items"]}
    )

    filtered = client.get(
        "/api/v1/proteins/P00533/go/terms",
        params={"q": "epidermal growth factor receptor", "evidence_code": "ida"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["items"]
    assert all(
        "epidermal growth factor receptor" in item["go_term_name"].lower()
        and any(code["evidence_code"] == "IDA" for code in item["evidence_codes"])
        for item in filtered.json()["items"]
    )


def test_go_term_evidence_is_lazy_pageable_and_keeps_raw_annotation_fields() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/go/terms/GO:0005006/evidence", params={"limit": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_or_estimate"] == {"value": 12, "kind": "exact"}
    assert len(body["items"]) == 2
    assert body["next_cursor"]
    item = body["items"][0]
    assert item["go_id"] == "GO:0005006"
    assert item["qualifier"]
    assert item["evidence_code"] == "IDA"
    assert item["reference_id"].startswith("PMID:")
    assert item["assigned_by"]
    assert item["annotation_date"]

    second_page = client.get(
        "/api/v1/proteins/P00533/go/terms/GO:0005006/evidence",
        params={"limit": 2, "cursor": body["next_cursor"]},
    )
    assert second_page.status_code == 200
    assert {row["go_evidence_id"] for row in body["items"]}.isdisjoint(
        {row["go_evidence_id"] for row in second_page.json()["items"]}
    )


def test_go_term_evidence_applies_evidence_code_to_rows_counts_and_cursor() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/go/terms/GO:0005006/evidence",
        params={"evidence_code": "ida", "limit": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_or_estimate"] == {"value": 7, "kind": "exact"}
    assert body["applied_filters"]["evidence_code"] == "IDA"
    assert body["items"]
    assert all(item["evidence_code"] == "IDA" for item in body["items"])

    second_page = client.get(
        "/api/v1/proteins/P00533/go/terms/GO:0005006/evidence",
        params={"evidence_code": "IDA", "limit": 2, "cursor": body["next_cursor"]},
    )
    assert second_page.status_code == 200
    assert all(item["evidence_code"] == "IDA" for item in second_page.json()["items"])

    mismatched_filter = client.get(
        "/api/v1/proteins/P00533/go/terms/GO:0005006/evidence",
        params={"evidence_code": "IMP", "limit": 2, "cursor": body["next_cursor"]},
    )
    assert mismatched_filter.status_code == 400
    assert mismatched_filter.json()["detail"] == "Invalid GO evidence cursor"


def test_go_default_explicitly_excludes_negated_annotations() -> None:
    excluded = client.get("/api/v1/proteins/P12270/go/terms", params={"limit": 50})
    included = client.get(
        "/api/v1/proteins/P12270/go/terms", params={"limit": 50, "include_negated": "true"},
    )

    assert excluded.status_code == included.status_code == 200
    assert excluded.json()["annotation_count"] < included.json()["annotation_count"]
    assert excluded.json()["applied_filters"]["include_negated"] is False
    assert included.json()["applied_filters"]["include_negated"] is True


def test_go_cursor_is_bound_to_its_filters_and_protein() -> None:
    first = client.get("/api/v1/proteins/P00533/go/terms", params={"limit": 1}).json()
    response = client.get(
        "/api/v1/proteins/P00533/go/terms",
        params={"aspect": "CC", "limit": 1, "cursor": first["next_cursor"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid GO evidence cursor"
