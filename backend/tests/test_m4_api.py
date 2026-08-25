from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.m4 import (
    accession_bucket,
    interaction_bucket_glob,
    interaction_mutation_bucket_glob,
    load_source_descriptions,
)
from app.main import app


client = TestClient(app)


def test_egfr_interaction_summary_keeps_evidence_and_native_counts_distinct() -> None:
    response = client.get("/api/v1/proteins/P00533/interactions/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert {item["source_database"] for item in body["items"]} == {"BioGRID", "IntAct"}
    assert {item["interaction_category"] for item in body["items"] if item["source_database"] == "BioGRID"} == {
        "physical", "genetic"
    }
    assert all(item["evidence_record_count"] >= item["distinct_native_interaction_count"] for item in body["items"])
    assert any(item["evidence_record_count"] > item["distinct_native_interaction_count"] for item in body["items"])
    assert all("curation scope" in meta["caveat"] or "context" in meta["caveat"] for meta in body["source_semantics"])


def test_interaction_detail_is_single_source_keyset_paged_and_filter_bound() -> None:
    params = {"source": "BioGRID", "category": "physical", "limit": 2}
    first = client.get("/api/v1/proteins/P00533/interactions", params=params)
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 2
    assert first_body["next_cursor"]
    assert all(item["interaction_category"] == "physical" for item in first_body["items"])
    assert all(set(item["source_specific"]) == {"biogrid"} for item in first_body["items"])

    second = client.get(
        "/api/v1/proteins/P00533/interactions",
        params={**params, "cursor": first_body["next_cursor"]},
    )
    assert second.status_code == 200
    first_rows = {(item["native_interaction_id"], item["context"]) for item in first_body["items"]}
    second_rows = {(item["native_interaction_id"], item["context"]) for item in second.json()["items"]}
    assert first_rows.isdisjoint(second_rows)

    mismatch = client.get(
        "/api/v1/proteins/P00533/interactions",
        params={
            **params, "category": "genetic", "cursor": first_body["next_cursor"],
        },
    )
    assert mismatch.status_code == 400


def test_intact_negative_and_expansion_context_are_not_discarded() -> None:
    response = client.get(
        "/api/v1/proteins/Q08379/interactions",
        params={"source": "IntAct", "category": "negative", "limit": 20},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    for item in body["items"]:
        assert item["interaction_category"] == "negative"
        intact = item["source_specific"]["intact"]
        assert intact["is_negative"] is True
        assert "expansion_method" in intact


def test_mutation_effects_are_a_separate_bounded_subresource() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/interactions/mutation-effects", params={"limit": 2}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["next_cursor"]
    assert all(item["source_database"] == "IntAct" for item in body["items"])
    assert all(item["feature_accession"] for item in body["items"])
    assert client.get(
        "/api/v1/proteins/P00533/interactions/mutation-effects",
        params={"cursor": "not-a-cursor"},
    ).status_code == 400


def test_interaction_empty_invalid_missing_and_single_bucket_paths() -> None:
    empty = client.get(
        "/api/v1/proteins/Q12836/interactions", params={"source": "BioGRID"}
    )
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total_or_estimate"]["value"] == 0
    assert client.get("/api/v1/proteins/P00533/interactions").status_code == 422
    assert client.get(
        "/api/v1/proteins/P00533/interactions", params={"source": "STRING"}
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/NOT_A_PROTEIN/interactions", params={"source": "BioGRID"}
    ).status_code == 404

    detail_path = interaction_bucket_glob("BioGRID", "P00533")
    mutation_path = interaction_mutation_bucket_glob("P00533")
    assert detail_path is not None and mutation_path is not None
    assert str(detail_path).endswith(str(
        Path("interaction") / "source=BioGRID"
        / f"accession_bucket={accession_bucket('P00533')}" / "*.parquet"
    ))
    assert str(mutation_path).endswith(str(
        Path("interaction_mutation") / "source=IntAct"
        / f"accession_bucket={accession_bucket('P00533')}" / "*.parquet"
    ))
    assert "**" not in detail_path and "**" not in mutation_path


def test_egfr_disease_sections_are_source_specific_without_voting() -> None:
    response = client.get("/api/v1/proteins/P00533/diseases")
    assert response.status_code == 200
    body = response.json()
    assert body["interpretation"] == "source_specific_no_cross_source_voting"
    assert set(body["sections"]) == {
        "clingen_validity", "clingen_dosage", "gencc", "omim", "hpo"
    }
    assert {name: section["total_or_estimate"]["value"] for name, section in body["sections"].items()} == {
        "clingen_validity": 1, "clingen_dosage": 1, "gencc": 9, "omim": 4, "hpo": 2,
    }
    validity = body["sections"]["clingen_validity"]["items"][0]
    assert validity["assertion"]["classification"] == "Definitive"
    assert validity["exact_mondo_mappings"]
    assert all(
        mapping["mapping_basis"] in {
            "direct MONDO identifier", "eligible exact MONDO xref"
        }
        for mapping in validity["exact_mondo_mappings"]
    )
    assert validity["exact_mondo_mappings"][0]["categories"]
    assert all(
        {"category_mondo_id", "category_name", "category_axis", "is_hereditary", "is_neoplastic"}
        <= set(category)
        for mapping in validity["exact_mondo_mappings"]
        for category in mapping["categories"]
    )


def test_hpo_observed_absent_and_inheritance_are_separate_with_bound_cursor() -> None:
    observed = client.get(
        "/api/v1/proteins/P00533/diseases/hpo",
        params={"category": "observed", "disease_id": "OMIM:211980", "limit": 2},
    )
    assert observed.status_code == 200
    body = observed.json()
    assert body["items"] and body["next_cursor"]
    assert all(item["phenotype_status"] == "observed" and item["aspect"] != "I" for item in body["items"])

    second = client.get(
        "/api/v1/proteins/P00533/diseases/hpo",
        params={
            "category": "observed", "disease_id": "OMIM:211980", "limit": 2,
            "cursor": body["next_cursor"],
        },
    )
    assert second.status_code == 200
    mismatch = client.get(
        "/api/v1/proteins/P00533/diseases/hpo",
        params={"category": "inheritance", "cursor": body["next_cursor"]},
    )
    assert mismatch.status_code == 400

    absent = client.get(
        "/api/v1/proteins/P00533/diseases/hpo",
        params={"category": "explicitly_absent"},
    )
    assert absent.status_code == 200
    assert absent.json()["items"] == []
    inheritance = client.get(
        "/api/v1/proteins/P00533/diseases/hpo",
        params={"category": "inheritance"},
    )
    assert inheritance.status_code == 200
    assert inheritance.json()["items"]
    assert all(item["aspect"] == "I" for item in inheritance.json()["items"])

    absent_evidence = client.get(
        "/api/v1/proteins/Q9UMD9/diseases/hpo",
        params={"category": "explicitly_absent", "limit": 5},
    )
    assert absent_evidence.status_code == 200
    assert absent_evidence.json()["items"]
    assert all(
        item["qualifier"] == "NOT"
        and item["phenotype_status"] == "explicitly_absent"
        and item["aspect"] != "I"
        for item in absent_evidence.json()["items"]
    )


def test_disease_sparse_empty_cursor_binding_and_quarantine_is_not_exposed() -> None:
    empty = client.get("/api/v1/proteins/O00161/diseases")
    assert empty.status_code == 200
    assert all(section["items"] == [] for section in empty.json()["sections"].values())

    first = client.get(
        "/api/v1/proteins/P00533/diseases",
        params={"source": "gencc", "limit": 2},
    )
    assert first.status_code == 200
    cursor = first.json()["sections"]["gencc"]["next_cursor"]
    assert cursor
    assert client.get(
        "/api/v1/proteins/P00533/diseases",
        params={"source": "omim", "limit": 2, "cursor": cursor},
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/P00533/diseases",
        params={"source": "clingen_validity_quarantine"},
    ).status_code == 422

    sources = client.get("/api/v1/data-sources")
    assert sources.status_code == 200
    source_items = sources.json()["items"]
    source_ids = {item["source_id"] for item in source_items}
    assert {
        "uniprot_basic", "goa_annotation", "reactome", "dbptm", "pfam", "consurf",
        "uniprot_covalent_structure", "clinvar_variant", "cosmic_variant",
        "gnomad_variant", "dbsnp_variant", "hpa_rna_expression", "hpa_ms_expression",
        "hpa_ihc_expression", "paxdb_expression", "gtex_qtl", "eqtlgen_qtl",
        "qtlbase_qtl", "biogrid_interaction", "intact_interaction",
        "intact_mutation_effect", "clingen_gene_disease_validity", "clingen_dosage",
        "gencc_assertion", "omim_gene_disease", "hpo_disease_phenotype",
        "mondo_navigation",
        "alphagenome",
    } <= source_ids
    assert all("quarantine" not in source_id for source_id in source_ids)
    by_id = {item["source_id"]: item for item in source_items}
    assert "2026-07-26" in by_id["goa_annotation"]["source_release"]
    assert "2026-06-15" in by_id["goa_annotation"]["source_release"]
    assert "unresolved_from_fasta_header" in by_id["consurf"]["caveat"]


def test_source_registry_is_the_validated_single_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = tmp_path / "sources.yaml"
    registry.write_text(
        "sources:\n"
        "  one:\n"
        "    display_name: One\n"
        "    layer: test\n"
        "    source_release: null\n"
        "    record_grain: one row\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MEMVAR_SOURCE_REGISTRY", str(registry))
    descriptions = load_source_descriptions()
    assert [item.source_id for item in descriptions] == ["one"]

    registry.write_text(
        "sources:\n"
        "  clingen_quarantine:\n"
        "    display_name: Forbidden\n"
        "    layer: disease\n"
        "    record_grain: quarantined row\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="Quarantine"):
        load_source_descriptions()
