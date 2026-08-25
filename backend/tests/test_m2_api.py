from fastapi.testclient import TestClient
from fastapi import HTTPException
import duckdb
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app.main import app
from app import m2
from app.m2 import cosmic_roles, source_list, variant_catalog_summary, variant_key_bucket


client = TestClient(app)


def test_variant_catalog_summary_uses_distinct_variants_without_clinvar_voting(monkeypatch, tmp_path) -> None:
    paths = {name: tmp_path / f"{name}.parquet" for name in ("core", "effect", "clinvar")}
    pq.write_table(pa.Table.from_pylist([
        {"page_accession": "TEST1", "variant_key": key}
        for key in ("both", "no-clinvar", "benign", "pathogenic", "uncertain", "conflict", "other", "unclassified")
    ]), paths["core"])
    pq.write_table(pa.Table.from_pylist([
        {
            "uniprot_accession": "TEST1", "variant_key": key, "effect_scope": "canonical",
            "uniprot_isoform_id": "TEST1-1",
            "Consequence": "missense_variant,splice_region_variant" if key == "both" else "missense_variant",
        }
        for key in ("both", "no-clinvar", "benign", "pathogenic", "uncertain", "conflict", "other", "unclassified")
    ] + [{
        "uniprot_accession": "TEST1", "variant_key": "both", "effect_scope": "isoform",
        "uniprot_isoform_id": "TEST1-2", "Consequence": "missense_variant",
    }]), paths["effect"])
    pq.write_table(pa.Table.from_pylist([
        {"page_accession": "TEST1", "variant_key": "both", "ClinicalSignificance": "Likely benign"},
        {"page_accession": "TEST1", "variant_key": "both", "ClinicalSignificance": "Pathogenic"},
        {"page_accession": "TEST1", "variant_key": "benign", "ClinicalSignificance": "Benign/Likely benign"},
        {"page_accession": "TEST1", "variant_key": "pathogenic", "ClinicalSignificance": "Likely pathogenic"},
        {"page_accession": "TEST1", "variant_key": "uncertain", "ClinicalSignificance": "Uncertain significance"},
        {"page_accession": "TEST1", "variant_key": "conflict", "ClinicalSignificance": "Conflicting classifications of pathogenicity"},
        {"page_accession": "TEST1", "variant_key": "other", "ClinicalSignificance": "drug response"},
        {"page_accession": "TEST1", "variant_key": "unclassified", "ClinicalSignificance": None},
    ]), paths["clinvar"])

    monkeypatch.setattr(m2, "require_protein", lambda _connection, _acc: {"uniprot_accession": "TEST1"})
    monkeypatch.setattr(m2, "bucket_glob", lambda _accession, *parts: str(paths[parts[-1]]))
    summary = variant_catalog_summary("TEST1", duckdb.connect())

    assert summary.total.model_dump() == {
        "value": 8, "record_grain": "distinct_variant_key", "categories_overlap": False,
    }
    assert summary.protein_forms.model_dump() == {
        "record_grain": "distinct_variant_key", "categories_overlap": True,
        "items": [
            {"category": "canonical", "variant_count": 8, "isoform_id": "TEST1-1"},
            {"category": "isoform", "variant_count": 1, "isoform_id": "TEST1-2"},
        ],
    }
    assert {item.category: item.variant_count for item in summary.consequences.items} == {
        "missense_variant": 8, "splice_region_variant": 1,
    }
    assert {item.category: item.variant_count for item in summary.clinvar_pathogenicity.items} == {
        "benign": 2, "pathogenic": 2, "uncertain": 1,
        "conflicting": 1, "other": 1, "unclassified": 2,
    }


def test_p00533_variant_catalog_summary_conserves_real_accession_counts(monkeypatch) -> None:
    generated_root = Path("data/generated")
    bucket = m2.accession_bucket("P00533")
    monkeypatch.setattr(
        m2,
        "bucket_glob",
        lambda _accession, *parts: str(
            generated_root.joinpath(*parts, f"accession_bucket={bucket}", "*.parquet")
        ),
    )
    connection = duckdb.connect(str(generated_root / "memvar_core.duckdb"), read_only=True)
    try:
        body = variant_catalog_summary("P00533", connection).model_dump()
        options = m2.variant_filter_options("P00533", "all", connection).model_dump()
        expected_total = connection.execute(
            "SELECT count(DISTINCT variant_key) FROM read_parquet(?) WHERE page_accession = 'P00533'",
            [str(generated_root / "variant" / "core" / f"accession_bucket={bucket}" / "*.parquet")],
        ).fetchone()[0]
        expected_canonical = connection.execute(
            """
            SELECT count(DISTINCT variant_key) FROM read_parquet(?)
            WHERE uniprot_accession = 'P00533' AND effect_scope = 'canonical'
            """,
            [str(generated_root / "variant" / "effect" / f"accession_bucket={bucket}" / "*.parquet")],
        ).fetchone()[0]
    finally:
        connection.close()

    assert body["total"]["value"] == expected_total
    assert body["total"]["record_grain"] == "distinct_variant_key"
    assert body["total"]["categories_overlap"] is False
    assert all(facet["record_grain"] == "distinct_variant_key" for facet in (
        body["protein_forms"], body["consequences"], body["clinvar_pathogenicity"],
    ))
    assert all(facet["categories_overlap"] is True for facet in (
        body["protein_forms"], body["consequences"], body["clinvar_pathogenicity"],
    ))
    assert body["protein_forms"]["items"][0]["category"] == "canonical"
    assert body["protein_forms"]["items"][0]["variant_count"] == expected_canonical
    assert {item["category"]: item["variant_count"] for item in body["consequences"]["items"]} == {
        item["value"]: item["variant_count"] for item in options["consequences"]
    }
    assert {item["category"] for item in body["clinvar_pathogenicity"]["items"]} == {
        "benign", "pathogenic", "uncertain", "conflicting", "other", "unclassified",
    }
    assert body["response_bounds"] == {
        "strategy": "one_accession_bucket_single_grouped_query", "runtime_external_requests": 0,
    }
    assert any(route.path == "/api/v1/proteins/{acc}/variants/summary" for route in app.routes)


def test_variant_catalog_summary_keeps_existing_unknown_accession_semantics() -> None:
    connection = duckdb.connect("data/generated/memvar_core.duckdb", read_only=True)
    try:
        with pytest.raises(HTTPException) as error:
            variant_catalog_summary("NOT_A_PROTEIN", connection)
    finally:
        connection.close()
    assert error.value.status_code == 404


def test_egfr_sequence_returns_a_bounded_canonical_window() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/sequence",
        params={"start": 700, "end": 760, "tracks": "feature,variant"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["length"] == 1210
    assert body["sequence_version"] == 2
    assert body["coordinate_basis"] == "canonical_1_based_closed"
    assert body["window"] == {
        "start": 700,
        "end": 760,
        "sequence": "NQALLRILKETEFKKIKVLGSGAFGTVYKGLWIPEGEKVKIPVAIKELREATSPKANKEIL",
    }
    assert [track["track"] for track in body["tracks"]] == ["feature", "variant"]
    assert body["build_context"]["scope"] == "all"


def test_site_detail_is_drawable_and_never_projects_isoforms() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/sites",
        params={"start": 400, "end": 410, "tracks": "feature,ptm,pfam,conservation,covalent,variant"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["region"] == {"start": 400, "end": 410}
    assert body["density"]
    assert body["summary"]["conservation"] == 11
    assert all(item["status"] == "drawable" for item in body["tracks"]["variant"])
    assert all(item["effect_scope"] == "canonical" for item in body["tracks"]["variant"])
    assert all(item["coordinate_basis"] == "canonical_1_based_closed" for item in body["tracks"]["variant"])

    # This variant has an EGFR isoform effect at 404 but no canonical effect.
    isoform_only = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"scope": "isoform", "start": 404, "end": 404, "limit": 200},
    )
    assert isoform_only.status_code == 200
    assert any(item["variant_key"] == "7-55156831-A-AG" for item in isoform_only.json()["items"])
    assert all(item["variant_key"] != "7-55156831-A-AG" for item in body["tracks"]["variant"])


def test_variant_keyset_pagination_is_stable_and_filter_bound() -> None:
    first = client.get("/api/v1/proteins/P00533/variants", params={"limit": 2})
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 2
    assert first_body["next_cursor"]
    assert first_body["total_or_estimate"]["kind"] == "exact"
    assert all(item["primary_effect"]["effect_scope"] == "canonical" for item in first_body["items"])

    second = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"limit": 2, "cursor": first_body["next_cursor"]},
    )
    assert second.status_code == 200
    assert {item["variant_key"] for item in first_body["items"]}.isdisjoint(
        item["variant_key"] for item in second.json()["items"]
    )

    mismatched_filter = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"limit": 2, "scope": "all", "cursor": first_body["next_cursor"]},
    )
    assert mismatched_filter.status_code == 400


def test_variant_primary_effect_is_selected_from_the_filtered_effects() -> None:
    isoform = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"scope": "isoform", "limit": 20},
    )
    assert isoform.status_code == 200
    assert isoform.json()["items"]
    assert all(
        item["primary_effect"]["effect_scope"] == "isoform"
        for item in isoform.json()["items"]
    )

    consequence = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"scope": "all", "consequence": "start_lost", "limit": 20},
    )
    assert consequence.status_code == 200
    assert consequence.json()["items"]
    assert all(
        "start_lost" in {
            term.strip().lower()
            for term in item["primary_effect"]["consequence"].split(",")
        }
        for item in consequence.json()["items"]
    )

    site = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"scope": "all", "start": 404, "end": 404, "limit": 20},
    )
    assert site.status_code == 200
    assert site.json()["items"]
    assert all(
        item["primary_effect"]["protein_start"] <= 404
        and item["primary_effect"]["protein_end"] >= 404
        for item in site.json()["items"]
    )


def test_source_filter_matches_complete_badges_case_insensitively() -> None:
    exact = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"source": "GnOmAd", "limit": 1},
    )
    assert exact.status_code == 200
    assert exact.json()["items"]
    assert "gnomAD" in exact.json()["items"][0]["source_badges"]

    substring = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"source": "noMAD", "limit": 1},
    )
    assert substring.status_code == 200
    assert substring.json()["items"] == []
    assert substring.json()["total_or_estimate"]["value"] == 0


def test_variant_filter_options_are_complete_scoped_terms_and_sources() -> None:
    canonical = client.get(
        "/api/v1/proteins/P00533/variants/options",
        params={"scope": "canonical"},
    )
    assert canonical.status_code == 200
    body = canonical.json()
    assert body["uniprot_accession"] == "P00533"
    assert body["scope"] == "canonical"
    assert body["complete"] is True
    assert body["response_bounds"] == {
        "strategy": "complete_accession_bucket_distinct_values",
        "fact_rows_returned": 0,
        "counts": "exact_distinct_variants",
        "consequence_semantics": "comma_separated_term_membership",
        "source_semantics": "semicolon_separated_badge_membership",
    }
    consequences = {item["value"]: item["variant_count"] for item in body["consequences"]}
    sources = {item["value"]: item["variant_count"] for item in body["sources"]}
    assert "missense_variant" in consequences
    assert "splice_region_variant" in consequences
    assert all("," not in value for value in consequences)
    assert set(sources) == {"ClinVar", "Cosmic", "dbSNP", "gnomAD"}
    assert all(";" not in value for value in sources)
    assert all(count > 0 for count in [*consequences.values(), *sources.values()])

    isoform = client.get(
        "/api/v1/proteins/P00533/variants/options",
        params={"scope": "isoform"},
    )
    assert isoform.status_code == 200
    assert isoform.json()["scope"] == "isoform"

    empty = client.get("/api/v1/proteins/A0A087X1C5/variants/options")
    assert empty.status_code == 200
    assert empty.json()["consequences"] == []
    assert empty.json()["sources"] == []


def test_composite_consequence_filter_matches_term_membership() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/variants",
        params={"scope": "all", "consequence": "splice_region_variant", "limit": 200},
    )
    assert response.status_code == 200
    assert response.json()["items"]
    assert all(
        "splice_region_variant" in {
            term.strip().lower()
            for term in item["primary_effect"]["consequence"].split(",")
        }
        for item in response.json()["items"]
    )


def test_variant_evidence_branches_only_resolve_their_own_source_bucket(monkeypatch) -> None:
    variant_key = "7-55019282-G-A"
    original_bucket_glob = m2.bucket_glob
    original_optional_bucket_glob = m2.optional_bucket_glob
    calls: list[tuple[str, ...]] = []

    def tracked_bucket_glob(accession: str, *parts: str) -> str:
        calls.append(parts)
        return original_bucket_glob(accession, *parts)

    def tracked_optional_bucket_glob(accession: str, *parts: str) -> str | None:
        calls.append(parts)
        return original_optional_bucket_glob(accession, *parts)

    monkeypatch.setattr(m2, "bucket_glob", tracked_bucket_glob)
    monkeypatch.setattr(m2, "optional_bucket_glob", tracked_optional_bucket_glob)

    expected = {
        "facts": ("variant", "core"),
        "effects": ("variant", "effect"),
        "clinvar": ("variant", "source", "clinvar"),
        "cosmic": ("variant", "source", "cosmic"),
        "stability": ("variant", "source", "thermompnn"),
    }
    for branch, source_bucket in expected.items():
        calls.clear()
        response = client.get(
            f"/api/v1/variants/{variant_key}/evidence/{branch}",
            params={"protein_accession": "P00533"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["uniprot_accession"] == "P00533"
        assert body["variant_key"] == variant_key
        assert body["branch"] == branch
        assert calls == [("variant", "core")] + ([] if branch == "facts" else [source_bucket])
        if branch == "clinvar":
            assert {"source_release", "evidence_grain"} <= set(body["assertions"][0])

    empty_clinvar = client.get(
        "/api/v1/variants/7-55019278-A-G/evidence/clinvar",
        params={"protein_accession": "P00533"},
    )
    assert empty_clinvar.status_code == 200
    assert empty_clinvar.json()["assertions"] == []

    assert client.get(f"/api/v1/variants/{variant_key}").status_code == 404
    assert client.get(f"/api/v1/variants/{variant_key}/evidence/facts").status_code == 422
    assert client.get(
        f"/api/v1/variants/{variant_key}/evidence/facts",
        params={"protein_accession": "Q9Y2D0"},
    ).status_code == 404


def test_gnomad_population_frequency_is_local_bounded_and_never_mixes_callsets(monkeypatch, tmp_path) -> None:
    variant_key = "7-55198724-T-C"
    populations = ("afr", "ami", "amr", "asj", "eas", "fin", "mid", "nfe", "remaining", "sas")
    row: dict[str, str | float | None] = {"variant_key": variant_key}
    for callset in ("exome", "genome", "joint"):
        for population in populations:
            if callset == "exome" and population == "ami":
                continue
            row[f"{callset}_{population}_af"] = None
    row["exome_afr_af"] = 0.0
    row["exome_nfe_af"] = 1e-5
    row["joint_afr_af"] = 0.25
    row["joint_nfe_af"] = 2e-6
    bucket = tmp_path / f"variant_bucket={variant_key_bucket(variant_key):03d}"
    bucket.mkdir()
    pq.write_table(pa.Table.from_pylist([row]), bucket / "data_0.parquet", compression="zstd")
    monkeypatch.setattr("app.m2.population_frequency_root", lambda: tmp_path)

    matched = client.get(
        f"/api/v1/variants/{variant_key}/population-frequency",
        params={"protein_accession": "P00533"},
    )
    assert matched.status_code == 200
    body = matched.json()
    assert body["availability"] == "matched"
    assert body["dataset"] == "gnomad_r4"
    assert body["source_release"] == "v4.1"
    assert body["genome_build"] == "GRCh38"
    assert body["population_scope"] == "genetic_ancestry_group"
    assert body["callset"] == "joint"
    assert body["available_callsets"] == ["exome", "genome", "joint"]
    assert body["total_or_estimate"] == {"value": 10, "kind": "exact"}
    assert {item["ancestry_group"] for item in body["groups"]} == {
        "afr", "amr", "asj", "eas", "fin", "mid", "nfe", "sas", "ami", "remaining",
    }
    assert next(item for item in body["groups"] if item["ancestry_group"] == "afr")["allele_frequency"] == 0.25
    assert next(item for item in body["groups"] if item["ancestry_group"] == "ami")["allele_frequency"] is None
    assert body["unavailable_fields"] == ["ac", "an", "homozygote_count", "hemizygote_count"]
    assert body["response_bounds"]["runtime_external_requests"] == 0

    exome = client.get(
        f"/api/v1/variants/{variant_key}/population-frequency",
        params={"protein_accession": "P00533", "callset": "exome"},
    )
    assert exome.status_code == 200
    assert exome.json()["total_or_estimate"] == {"value": 9, "kind": "exact"}
    assert next(item for item in exome.json()["groups"] if item["ancestry_group"] == "afr")["allele_frequency"] == 0.0
    assert all(item["ancestry_group"] != "ami" for item in exome.json()["groups"])

    missing = client.get(
        "/api/v1/variants/7-55143418-C-T/population-frequency",
        params={"protein_accession": "P00533"},
    )
    assert missing.status_code == 200
    assert missing.json()["availability"] == "not_found_in_gnomad"
    assert missing.json()["groups"] == []


def test_default_variant_page_has_direct_gnomad_actions() -> None:
    page = client.get(
        "/api/v1/proteins/P00533/variants", params={"limit": 12}
    )
    assert page.status_code == 200
    items = page.json()["items"]
    assert len(items) == 12
    assert all("gnomAD" in item["source_badges"] for item in items)


def test_cosmic_cgc_evidence_is_typed_deduplicated_and_gene_level() -> None:
    response = client.get(
        "/api/v1/variants/7-55019282-G-A/evidence/cosmic",
        params={"protein_accession": "P00533"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["records"] == [{
        "genome_screen_sample_count": 2,
        "mondo_ids": ["MONDO:0045024"],
        "disease_categories": ["cancer or benign tumor"],
        "cgc_tier": 1,
        "cgc_roles": ["oncogene"],
    }]
    assert set(body["records"][0]) == {
        "genome_screen_sample_count", "mondo_ids", "disease_categories",
        "cgc_tier", "cgc_roles",
    }

    # Source spelling/order is normalized, but CGC roles remain gene-level
    # evidence and are not fed into the ClinVar P/LP density implementation.
    assert cosmic_roles(" fusion, oncogene, TSG, oncogene ") == [
        "oncogene", "TSG", "fusion",
    ]
    assert source_list("MONDO:1; MONDO:2;MONDO:1") == ["MONDO:1", "MONDO:2"]

    empty = client.get("/api/v1/proteins/P43627/variants")
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total_or_estimate"]["value"] == 0


def test_invalid_ranges_cursor_missing_and_empty_states() -> None:
    assert client.get(
        "/api/v1/proteins/P00533/sequence", params={"start": 0, "end": 5}
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/P00533/sequence", params={"start": 1, "end": 501}
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/P00533/sites", params={"start": 30, "end": 20}
    ).status_code == 400
    assert client.get(
        "/api/v1/proteins/P00533/variants", params={"cursor": "not-a-cursor"}
    ).status_code == 400
    assert client.get("/api/v1/proteins/NOT_A_PROTEIN/sequence").status_code == 404

    empty = client.get("/api/v1/proteins/A0A087X1C5/variants")
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total_or_estimate"]["value"] == 0
