from collections import Counter

import duckdb
from fastapi.testclient import TestClient

from app.main import app
from app import m2


client = TestClient(app)


def get_overview(accession: str, bins: int | None = None):
    params = {} if bins is None else {"bins": bins}
    return client.get(f"/api/v1/proteins/{accession}/sequence/overview", params=params)


def assert_bin_partition(body: dict) -> None:
    bins = body["density_bins"]
    assert bins[0]["start"] == 1
    assert bins[-1]["end"] == body["canonical_length"]
    assert all(left["end"] + 1 == right["start"] for left, right in zip(bins, bins[1:]))
    assert all(item["index"] == index and item["start"] <= item["end"] for index, item in enumerate(bins))


def test_egfr_overview_is_canonical_bounded_and_count_conserving() -> None:
    response = get_overview("P00533")
    assert response.status_code == 200
    body = response.json()

    assert body["uniprot_accession"] == "P00533"
    assert body["sequence_id"] == "P00533"
    assert body["canonical_length"] == 1210
    assert body["sequence_version"] == 2
    assert body["coordinate_basis"] == "canonical_1_based_closed"
    assert body["response_bounds"] == {
        "requested_bins": 400,
        "returned_bins": 400,
        "max_bins": 1000,
        "interval_sets_complete": True,
        "variant_fact_rows_returned": 0,
        "variant_bin_semantics": "one_per_canonical_drawable_variant_anchored_at_min_start",
        "secondary_structure_intervals_returned": 146,
        "max_secondary_structure_intervals": 512,
        "secondary_structure_intervals_complete": True,
    }
    assert_bin_partition(body)

    totals = body["totals"]
    assert totals == {
        "topology_intervals": len(body["topology_intervals"]),
        "pfam_intervals": len(body["pfam_intervals"]),
        "functional_intervals": len(body["functional_intervals"]),
        "secondary_structure_intervals": len(body["secondary_structure_intervals"]),
        "conservation_positions": 1210,
        "ptm_records": 136,
        "ptm_drawable_records": 136,
        "canonical_variants": 4385,
        "canonical_drawable_variants": 4381,
    }
    assert sum(item["conservation"]["observation_count"] for item in body["density_bins"]) == totals["conservation_positions"]
    assert sum(item["ptm_count"] for item in body["density_bins"]) == totals["ptm_records"]
    assert sum(item["variant_count"] for item in body["density_bins"]) == totals["canonical_drawable_variants"]
    assert "variant_key" not in response.text
    assert "hgvsp" not in response.text.lower()


def test_intervals_and_jsd_obey_canonical_coordinate_contract() -> None:
    body = get_overview("P00533", 73).json()
    length = body["canonical_length"]
    for collection in (
        "topology_intervals", "pfam_intervals", "functional_intervals",
        "secondary_structure_intervals",
    ):
        assert all(1 <= item["start"] <= item["end"] <= length for item in body[collection])

    secondary = body["secondary_structure_intervals"]
    assert Counter(item["feature_type"] for item in secondary) == {
        "Helix": 56,
        "Beta strand": 76,
        "Turn": 14,
    }
    assert all(item["source"] == "UniProt" for item in secondary)
    assert all(
        set(item) == {
            "feature_type", "start", "end", "description", "feature_id",
            "start_modifier", "end_modifier", "source",
        }
        for item in secondary
    )

    observed = 0
    for item in body["density_bins"]:
        conservation = item["conservation"]
        observed += conservation["observation_count"]
        if conservation["observation_count"]:
            assert conservation["jsd_min"] <= conservation["jsd_mean"] <= conservation["jsd_max"]
            assert sum(conservation["confidence_counts"].values()) + conservation["confidence_missing_count"] == conservation["observation_count"]
        else:
            assert conservation["jsd_mean"] is None
            assert conservation["jsd_min"] is None
            assert conservation["jsd_max"] is None
    assert observed == body["totals"]["conservation_positions"]


def test_long_dense_protein_remains_a_small_fixed_bin_response() -> None:
    response = get_overview("Q8WXI7")
    assert response.status_code == 200
    body = response.json()
    assert body["canonical_length"] == 14507
    assert len(body["density_bins"]) == 400
    assert body["totals"]["canonical_drawable_variants"] == 42517
    assert body["totals"]["canonical_variants"] == 42522
    assert sum(item["variant_count"] for item in body["density_bins"]) == 42517
    # M15 adds a fixed 400-bin stability distribution without fact rows.
    assert len(response.content) < 400_000
    assert_bin_partition(body)


def test_sparse_and_empty_tracks_are_explicit_zeroes() -> None:
    sparse = get_overview("A0A087X1C5", 100)
    assert sparse.status_code == 200
    sparse_body = sparse.json()
    assert sparse_body["totals"]["canonical_drawable_variants"] == 0
    assert all(item["variant_count"] == 0 for item in sparse_body["density_bins"])

    no_ptm_or_variant = get_overview("A0A0G2JS06", 400)
    assert no_ptm_or_variant.status_code == 200
    empty_body = no_ptm_or_variant.json()
    assert empty_body["response_bounds"]["returned_bins"] == empty_body["canonical_length"] == 123
    assert empty_body["totals"]["ptm_records"] == 0
    assert empty_body["totals"]["canonical_drawable_variants"] == 0
    assert all(item["ptm_count"] == item["variant_count"] == 0 for item in empty_body["density_bins"])
    assert empty_body["secondary_structure_intervals"] == []
    assert empty_body["totals"]["secondary_structure_intervals"] == 0
    assert empty_body["response_bounds"]["secondary_structure_intervals_complete"] is True


def test_secondary_structure_intervals_are_typed_canonical_and_bounded(
    tmp_path, monkeypatch
) -> None:
    feature_path = tmp_path / "feature_interval.parquet"
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE feature_interval (
          uniprot_accession VARCHAR, coordinate_basis VARCHAR, track_group VARCHAR,
          feature_type VARCHAR, start_position DOUBLE, end_position DOUBLE,
          description VARCHAR, feature_id VARCHAR, start_modifier VARCHAR,
          end_modifier VARCHAR
        )
        """
    )
    rows = [
        ("TEST1", "canonical", "secondary_structure", "Helix", 1, 4,
         "kept", "0000", "EXACT", "UNCERTAIN"),
        ("TEST1", "canonical", "secondary_structure", "Strand", 5, 8,
         "not a supported type", "bad-type", "EXACT", "EXACT"),
        ("TEST1", "isoform", "secondary_structure", "Turn", 5, 8,
         "not canonical", "bad-coordinate", "EXACT", "EXACT"),
        ("TEST1", "canonical", "secondary_structure", "Beta strand", 0, 8,
         "out of bounds", "bad-start", "EXACT", "EXACT"),
    ]
    rows.extend(
        ("TEST1", "canonical", "secondary_structure", "Turn", 10, 10,
         None, f"z-{index:04d}", "EXACT", "EXACT")
        for index in range(m2.MAX_OVERVIEW_SECONDARY_STRUCTURE_INTERVALS)
    )
    connection.executemany(
        "INSERT INTO feature_interval VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
    )
    connection.execute(f"COPY feature_interval TO '{feature_path}' (FORMAT PARQUET)")
    monkeypatch.setattr(m2, "bucket_glob", lambda *_args: str(feature_path))

    intervals, total = m2.overview_secondary_structure_intervals(connection, "TEST1", 10)

    assert total == m2.MAX_OVERVIEW_SECONDARY_STRUCTURE_INTERVALS + 1
    assert len(intervals) == m2.MAX_OVERVIEW_SECONDARY_STRUCTURE_INTERVALS
    assert intervals[0].model_dump() == {
        "feature_type": "Helix",
        "start": 1,
        "end": 4,
        "description": "kept",
        "feature_id": "0000",
        "start_modifier": "EXACT",
        "end_modifier": "UNCERTAIN",
        "source": "UniProt",
    }
    assert all(item.feature_type in {"Helix", "Beta strand", "Turn"} for item in intervals)
    assert all(1 <= item.start <= item.end <= 10 for item in intervals)
    connection.close()


def test_bins_bounds_and_missing_protein() -> None:
    one = get_overview("P00533", 1)
    assert one.status_code == 200
    assert len(one.json()["density_bins"]) == 1
    assert one.json()["density_bins"][0]["start"] == 1
    assert one.json()["density_bins"][0]["end"] == 1210

    maximum = get_overview("P00533", 1000)
    assert maximum.status_code == 200
    assert len(maximum.json()["density_bins"]) == 1000
    assert get_overview("P00533", 0).status_code == 422
    assert get_overview("P00533", 1001).status_code == 422
    assert get_overview("NOT_A_PROTEIN").status_code == 404


def test_overview_reads_only_the_exact_accession_bucket(monkeypatch) -> None:
    resolved_paths: list[str] = []
    original = m2.bucket_glob

    def recording_bucket_glob(accession: str, *parts: str) -> str:
        path = original(accession, *parts)
        resolved_paths.append(path)
        return path

    monkeypatch.setattr(m2, "bucket_glob", recording_bucket_glob)
    response = get_overview("P00533", 20)
    assert response.status_code == 200
    # Secondary structure reads the same exact feature bucket independently;
    # M15 also reads one effect bucket for drawable stability memberships.
    assert len(resolved_paths) == 10
    assert all("accession_bucket=5/*.parquet" in path for path in resolved_paths)
    assert all("accession_bucket=*" not in path for path in resolved_paths)
