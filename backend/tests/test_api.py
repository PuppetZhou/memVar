from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_egfr_search_and_overview_excludes_sequence_content() -> None:
    search = client.get("/api/v1/search", params={"q": "EGFR"})
    assert search.status_code == 200
    search_body = search.json()
    assert search_body["resolution"] == "direct_candidate"
    assert search_body["ambiguity"] is False
    assert search_body["items"][0]["uniprot_accession"] == "P00533"
    assert search_body["items"][0]["match"]["kind"] == "exact"

    protein = client.get("/api/v1/proteins/P00533")
    assert protein.status_code == 200
    body = protein.json()
    assert body["gene_symbol"] == "EGFR"
    assert body["canonical_sequence"]["length"] == 1210
    assert "sequence" not in body["canonical_sequence"]
    assert any(identifier["identifier_full"] == "HGNC:3236" for identifier in body["identifiers"])
    assert body["annotation_summary"]["go"]["molecular_function"]
    assert body["annotation_summary"]["reactome_total"] > 0
    assert body["annotation_summary"]["locations_total"] > 0


def test_exact_ambiguous_ids_return_every_candidate_even_when_limit_is_small() -> None:
    response = client.get("/api/v1/search", params={"q": "SHORT", "limit": 1})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == body["total_or_estimate"]["value"] == 94
    assert body["ambiguity"] is True
    assert body["resolution"] == "candidate_selection"
    assert len({item["uniprot_accession"] for item in body["items"]}) == 94
    assert all(item["match"]["kind"] == "exact" for item in body["items"])
    assert body["applied_filters"]["exact_candidate_set_complete"] is True

    for query, expected in (("ENSG00000166160", 3), ("GNT1", 9)):
        ambiguous = client.get("/api/v1/search", params={"q": query, "limit": 1})
        assert ambiguous.status_code == 200
        ambiguous_body = ambiguous.json()
        assert len(ambiguous_body["items"]) == expected
        assert ambiguous_body["total_or_estimate"]["value"] == expected
        assert len({item["uniprot_accession"] for item in ambiguous_body["items"]}) == expected


def test_missing_protein_and_empty_search() -> None:
    assert client.get("/api/v1/proteins/NOT_A_PROTEIN").status_code == 404

    empty = client.get("/api/v1/search", params={"q": "   "})
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["resolution"] == "no_match"


def test_annotations_are_compact_and_paged() -> None:
    response = client.get("/api/v1/proteins/P00533/annotations", params={"section": "reactome"})
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert {item["section"] for item in body["items"]} == {"reactome"}
    assert body["total_or_estimate"]["kind"] == "exact"
