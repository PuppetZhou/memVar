from pathlib import Path

from fastapi.testclient import TestClient

from app.m3 import accession_bucket, qtl_bucket_glob
from app.main import app


client = TestClient(app)


def test_egfr_expression_keeps_four_modalities_and_ms_nulls() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/expression", params={"modality": "all"}
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body["groups"]) == {"hpa_rna", "hpa_ms", "hpa_ihc", "paxdb"}
    assert all(group["complete"] is True for group in body["groups"].values())
    assert all(group["items"] for group in body["groups"].values())
    assert body["groups"]["hpa_rna"]["items"][0]["unit"] == "nTPM"
    assert body["groups"]["paxdb"]["items"][0]["unit"] == "ppm"

    assert body["response_bounds"]["strategy"] == "complete_bounded_modality"

    sparse_ms = client.get(
        "/api/v1/proteins/A0A075B6H7/expression", params={"modality": "hpa_ms"}
    )
    assert sparse_ms.status_code == 200
    ms_items = sparse_ms.json()["groups"]["hpa_ms"]["items"]
    assert any(item["raw_value"] is None for item in ms_items)


def test_expression_requires_a_valid_modality_and_handles_missing_protein() -> None:
    assert client.get("/api/v1/proteins/P00533/expression").status_code == 422
    assert client.get(
        "/api/v1/proteins/P00533/expression", params={"modality": "combined_score"}
    ).status_code == 422
    assert client.get(
        "/api/v1/proteins/NOT_A_PROTEIN/expression", params={"modality": "all"}
    ).status_code == 404


def test_gtex_summary_and_detail_keep_exact_counts_build_and_semantics() -> None:
    summary = client.get(
        "/api/v1/proteins/P00533/qtl/summary",
        params={"source": "gtex", "qtl_type": "eqtl"},
    )
    assert summary.status_code == 200
    summary_body = summary.json()
    assert summary_body["items"]
    assert {item["source_database"] for item in summary_body["items"]} == {"GTEx"}
    assert {item["qtl_type"] for item in summary_body["items"]} == {"eQTL"}
    assert all(item["record_count"] > 0 for item in summary_body["items"])
    assert all(item["distinct_variant_or_locus_count"] > 0 for item in summary_body["items"])
    assert summary_body["source_semantics"] == [{
        "source_database": "GTEx",
        "evidence_semantics": "official significant pairs",
        "genome_build": "GRCh38",
    }]

    cortex = next(
        item for item in summary_body["items"]
        if item["tissue_or_context"] == "Brain_Cortex"
    )
    detail = client.get(
        "/api/v1/proteins/P00533/qtl",
        params={
            "source": "GTEx", "qtl_type": "eQTL", "tissue": "Brain_Cortex",
            "limit": 2,
        },
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["total_or_estimate"] == {
        "value": cortex["record_count"], "kind": "exact"
    }
    assert detail_body["items"]
    assert all(item["genome_build"] == "GRCh38" for item in detail_body["items"])
    assert all(item["evidence_semantics"] == "official significant pair" for item in detail_body["items"])
    assert all(set(item["source_specific"]) == {"gtex"} for item in detail_body["items"])


def test_qtlbase_rows_are_associations_and_loci_are_not_exact_variants() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/qtl",
        params={"source": "QTLbase", "qtl_type": "eQTL", "limit": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_semantics"]["evidence_semantics"] == (
        "associations; not a uniform significant set"
    )
    assert body["items"]
    for item in body["items"]:
        assert item["evidence_semantics"] == "association"
        assert "significant" not in item["evidence_semantics"].lower()
        assert item["genome_build"] == "GRCh38"
        assert item["variant_or_locus"]["kind"] == "chromosome_position_locus"
        assert item["variant_or_locus"]["has_ref_alt_or_rsid"] is False
        assert set(item["source_specific"]) == {"qtlbase"}


def test_sparse_eqtlgen_is_an_explicit_empty_grch37_state() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/qtl",
        params={"source": "eQTLGen", "qtl_type": "cis_eQTL"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total_or_estimate"] == {"value": 0, "kind": "exact"}
    assert body["source_semantics"]["genome_build"] == "GRCh37"


def test_qtl_cursor_is_keyset_paged_and_bound_to_all_filters() -> None:
    params = {
        "source": "GTEx", "qtl_type": "eQTL", "tissue": "Brain_Cortex",
        "limit": 2,
    }
    first = client.get("/api/v1/proteins/P00533/qtl", params=params)
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 2
    assert first_body["next_cursor"]

    second = client.get(
        "/api/v1/proteins/P00533/qtl",
        params={**params, "cursor": first_body["next_cursor"]},
    )
    assert second.status_code == 200
    first_ids = {item["variant_or_locus"]["identifier"] for item in first_body["items"]}
    second_ids = {item["variant_or_locus"]["identifier"] for item in second.json()["items"]}
    assert first_ids.isdisjoint(second_ids)

    mismatch = client.get(
        "/api/v1/proteins/P00533/qtl",
        params={
            **params, "tissue": "Brain_Cerebellum",
            "cursor": first_body["next_cursor"],
        },
    )
    assert mismatch.status_code == 400
    assert client.get(
        "/api/v1/proteins/P00533/qtl",
        params={**params, "cursor": "not-a-cursor"},
    ).status_code == 400


def test_qtl_detail_requires_valid_source_type_and_source_specific_filters() -> None:
    assert client.get("/api/v1/proteins/P00533/qtl").status_code == 422
    assert client.get(
        "/api/v1/proteins/P00533/qtl", params={"source": "unknown", "qtl_type": "eQTL"}
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/P00533/qtl", params={"source": "GTEx", "qtl_type": "cis_eQTL"}
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/P00533/qtl",
        params={"source": "GTEx", "qtl_type": "eQTL", "population": "EUR"},
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/NOT_A_PROTEIN/qtl",
        params={"source": "GTEx", "qtl_type": "eQTL"},
    ).status_code == 404


def test_qtl_path_resolves_one_source_type_accession_bucket_only() -> None:
    path = qtl_bucket_glob("GTEx", "eQTL", "P00533")
    assert path is not None
    expected = (
        Path("qtl") / "source=GTEx" / "type=eQTL"
        / f"accession_bucket={accession_bucket('P00533')}" / "*.parquet"
    )
    assert Path(path).is_absolute()
    assert str(path).endswith(str(expected))
    assert "**" not in path
