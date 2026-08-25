import duckdb
from fastapi.testclient import TestClient

from app.main import app
from app import m2


client = TestClient(app)


def test_strict_clinvar_plp_density_ignores_predictions_and_conflicts(
    tmp_path, monkeypatch
) -> None:
    effect_path = tmp_path / "effect.parquet"
    clinvar_path = tmp_path / "clinvar.parquet"
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE effect (
          uniprot_accession VARCHAR, variant_key VARCHAR, effect_scope VARCHAR,
          protein_start BIGINT, is_drawable BOOLEAN, Consequence VARCHAR,
          am_class VARCHAR
        )
        """
    )
    connection.executemany(
        "INSERT INTO effect VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("TEST1", "p", "canonical", 10, True, "missense_variant", None),
            ("TEST1", "p", "canonical", 20, True, "missense_variant", None),
            ("TEST1", "lp", "canonical", 10, True, "missense_variant", None),
            ("TEST1", "combo", "canonical", 11, True, "missense_variant", None),
            ("TEST1", "low", "canonical", 11, True, "missense_variant", None),
            ("TEST1", "semicolon", "canonical", 12, True, "missense_variant", None),
            ("TEST1", "conflict", "canonical", 12, True, "missense_variant", None),
            ("TEST1", "prediction-trap", "canonical", 13, True, "pathogenic", "pathogenic"),
            ("TEST1", "vus", "canonical", 13, True, "missense_variant", None),
            ("TEST1", "risk-mix", "canonical", 14, True, "missense_variant", None),
            ("TEST1", "isoform", "isoform", 10, True, "missense_variant", None),
            ("TEST1", "not-drawable", "canonical", 10, False, "missense_variant", None),
        ],
    )
    connection.execute(f"COPY effect TO '{effect_path}' (FORMAT PARQUET)")
    connection.execute(
        """
        CREATE TABLE clinvar (
          page_accession VARCHAR, variant_key VARCHAR, ClinicalSignificance VARCHAR
        )
        """
    )
    connection.executemany(
        "INSERT INTO clinvar VALUES (?, ?, ?)",
        [
            ("TEST1", "p", "Pathogenic"),
            ("TEST1", "lp", "Likely pathogenic"),
            ("TEST1", "lp", "Conflicting classifications of pathogenicity"),
            ("TEST1", "combo", "Pathogenic/Likely pathogenic"),
            ("TEST1", "low", "Likely pathogenic/Pathogenic, low penetrance"),
            ("TEST1", "semicolon", "Pathogenic; drug response"),
            ("TEST1", "conflict", "Conflicting classifications of pathogenicity"),
            ("TEST1", "prediction-trap", None),
            ("TEST1", "vus", "Uncertain significance"),
            ("TEST1", "risk-mix", "Likely pathogenic/Likely risk allele"),
        ],
    )
    connection.execute(f"COPY clinvar TO '{clinvar_path}' (FORMAT PARQUET)")

    def paths(_accession: str, *parts: str) -> str:
        return str(clinvar_path if parts[-1] == "clinvar" else effect_path)

    monkeypatch.setattr(m2, "bucket_glob", paths)
    density, canonical_total = m2.overview_variant_site_density(
        connection, "TEST1", 25
    )

    assert canonical_total == 10
    assert sum(density.total_counts) == 9
    assert sum(density.clinvar_plp_counts) == 5
    assert density.total_counts[9:14] == [2, 2, 2, 2, 1]
    assert density.clinvar_plp_counts[9:14] == [2, 2, 1, 0, 0]
    assert all(
        0 <= plp <= total
        for total, plp in zip(
            density.total_counts, density.clinvar_plp_counts, strict=True
        )
    )
    connection.close()


def test_egfr_overview_supplies_single_panel_data_with_count_conservation() -> None:
    response = client.get("/api/v1/proteins/P00533/sequence/overview")
    assert response.status_code == 200
    body = response.json()

    assert len(body["canonical_sequence"]) == body["canonical_length"] == 1210
    site_density = body["variant_site_density"]
    assert site_density["start"] == 1
    assert site_density["end"] == 1210
    assert len(site_density["total_counts"]) == 1210
    assert len(site_density["clinvar_plp_counts"]) == 1210
    assert sum(site_density["total_counts"]) == 4381
    assert sum(site_density["clinvar_plp_counts"]) == 87
    assert (site_density["total_counts"][745], site_density["clinvar_plp_counts"][745]) == (22, 4)
    assert (site_density["total_counts"][746], site_density["clinvar_plp_counts"][746]) == (20, 5)
    assert (site_density["total_counts"][772], site_density["clinvar_plp_counts"][772]) == (16, 5)
    assert all(
        0 <= plp <= total
        for total, plp in zip(
            site_density["total_counts"], site_density["clinvar_plp_counts"], strict=True
        )
    )
    assert sum(item["total_count"] for item in body["ptm_sites"]) == body["totals"]["ptm_drawable_records"]
    assert sum(item["count"] for item in body["ptm_type_counts"]) == body["totals"]["ptm_drawable_records"]
    assert body["totals"]["secondary_structure_intervals"] == len(body["secondary_structure_intervals"])
    assert body["response_bounds"]["secondary_structure_intervals_returned"] == len(body["secondary_structure_intervals"])
    assert body["covalent_pairs"]
    assert "variant_key" not in response.text
    assert "ClinicalSignificance" not in response.text


def test_variant_site_density_projection_matches_overview_without_unrelated_projection_reads(monkeypatch) -> None:
    overview = client.get("/api/v1/proteins/P00533/sequence/overview")
    assert overview.status_code == 200
    expected = overview.json()

    def unexpected_overview_read(*_args, **_kwargs):
        raise AssertionError("variant density endpoint must not build the complete sequence overview")

    for helper in (
        "overview_feature_intervals",
        "overview_secondary_structure_intervals",
        "overview_pfam_intervals",
        "overview_ptm_sites",
        "overview_covalent_pairs",
        "overview_density_bins",
        "overview_stability_bins",
    ):
        monkeypatch.setattr(m2, helper, unexpected_overview_read)

    response = client.get("/api/v1/proteins/P00533/sequence/variant-site-density")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "uniprot_accession", "canonical_length", "sequence_version",
        "coordinate_basis", "variant_site_density",
    }
    assert body["uniprot_accession"] == expected["uniprot_accession"]
    assert body["canonical_length"] == expected["canonical_length"]
    assert body["sequence_version"] == expected["sequence_version"]
    assert body["coordinate_basis"] == expected["coordinate_basis"]
    assert body["variant_site_density"] == expected["variant_site_density"]


def test_long_and_empty_proteins_have_length_bounded_arrays() -> None:
    dense = client.get("/api/v1/proteins/Q8WXI7/sequence/overview")
    assert dense.status_code == 200
    dense_body = dense.json()
    assert len(dense_body["canonical_sequence"]) == 14507
    assert len(dense_body["variant_site_density"]["total_counts"]) == 14507
    assert len(dense_body["variant_site_density"]["clinvar_plp_counts"]) == 14507
    assert sum(dense_body["variant_site_density"]["total_counts"]) == 42517
    # M15 adds a bounded 400-bin stability distribution (no substitution facts).
    assert len(dense.content) < 400_000

    empty = client.get("/api/v1/proteins/P43627/sequence/overview")
    assert empty.status_code == 200
    empty_body = empty.json()
    assert all(value == 0 for value in empty_body["variant_site_density"]["total_counts"])
    assert all(value == 0 for value in empty_body["variant_site_density"]["clinvar_plp_counts"])


def test_site_preview_is_exact_strict_and_bounded() -> None:
    response = client.get(
        "/api/v1/proteins/P00533/variants/site-preview",
        params={"position": 746, "limit": 6},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["position"] == 746
    assert body["total"] == 22
    assert body["clinvar_plp_count"] == 4
    assert body["showing"] == len(body["items"]) == 6
    assert body["limit"] == 6
    assert body["has_more"] is True
    assert sum(item["has_clinvar_plp_evidence"] for item in body["items"]) == 4
    assert all(set(item) == {
        "variant_key", "hgvsp", "consequence", "source_badges",
        "has_clinvar_plp_evidence", "stability_prediction",
    } for item in body["items"])
    assert body["variant_table_query"] == {
        "scope": "canonical", "start": 746, "end": 746,
    }

    complete = client.get(
        "/api/v1/proteins/P00533/variants/site-preview",
        params={"position": 747, "limit": 12},
    ).json()
    assert complete["total"] == 20
    assert complete["clinvar_plp_count"] == 5
    assert complete["showing"] == 12
    assert complete["has_more"] is True

    no_variants = client.get(
        "/api/v1/proteins/P43627/variants/site-preview",
        params={"position": 1},
    ).json()
    assert no_variants["total"] == no_variants["clinvar_plp_count"] == 0
    assert no_variants["items"] == []
    assert no_variants["has_more"] is False

    assert client.get(
        "/api/v1/proteins/P00533/variants/site-preview",
        params={"position": 746, "limit": 13},
    ).status_code == 422
    assert client.get(
        "/api/v1/proteins/P00533/variants/site-preview",
        params={"position": 1211},
    ).status_code == 400
