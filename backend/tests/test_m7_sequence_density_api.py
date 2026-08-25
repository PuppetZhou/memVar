import duckdb
from fastapi.testclient import TestClient

from app.main import app
from app import m2


client = TestClient(app)
SEMANTICS = "one_per_canonical_drawable_variant_anchored_at_min_start"


def test_variant_track_uses_one_global_min_start_anchor_per_variant_key(tmp_path, monkeypatch) -> None:
    parquet_path = tmp_path / "effect.parquet"
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE effect (
          uniprot_accession VARCHAR,
          variant_key VARCHAR,
          effect_scope VARCHAR,
          Consequence VARCHAR,
          HGVSp VARCHAR,
          protein_start BIGINT,
          protein_end BIGINT,
          ref_aa VARCHAR,
          alt_aa VARCHAR,
          site_parse_status VARCHAR,
          is_drawable BOOLEAN,
          is_representative_effect BOOLEAN
        )
        """
    )
    connection.executemany(
        "INSERT INTO effect VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("TEST1", "duplicate", "canonical", "missense_variant", "p.A10V", 10, 10, "A", "V", "drawable", True, False),
            ("TEST1", "duplicate", "canonical", "missense_variant", "p.A20V", 20, 20, "A", "V", "drawable", True, True),
            ("TEST1", "window-two", "canonical", "stop_gained", "p.Q20*", 20, 20, "Q", "*", "drawable", True, True),
            ("TEST1", "isoform-only", "isoform", "missense_variant", "p.A12V", 12, 12, "A", "V", "drawable", True, True),
            ("TEST1", "not-drawable", "canonical", "missense_variant", None, 14, 14, "A", "V", "unparsed", False, True),
        ],
    )
    connection.execute(f"COPY effect TO '{parquet_path}' (FORMAT PARQUET)")

    monkeypatch.setattr(m2, "bucket_glob", lambda accession, *parts: str(parquet_path))

    first = m2.site_track_rows(connection, "TEST1", "variant", 1, 15)
    second = m2.site_track_rows(connection, "TEST1", "variant", 16, 25)

    assert [(item["variant_key"], item["start"]) for item in first] == [("duplicate", 10)]
    assert [(item["variant_key"], item["start"]) for item in second] == [("window-two", 20)]
    assert all(item["variant_key"] != "duplicate" for item in second)
    connection.close()


def test_detail_variant_density_is_cross_window_unique_and_count_conserving() -> None:
    windows = [(1, 500), (501, 1000), (1001, 1210)]
    observed_keys: set[str] = set()
    observed_count = 0

    for start, end in windows:
        response = client.get(
            "/api/v1/proteins/P00533/sites",
            params={"start": start, "end": end, "tracks": "variant"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["variant_density_semantics"] == SEMANTICS
        keys = [item["variant_key"] for item in body["tracks"]["variant"]]
        assert len(keys) == len(set(keys))
        assert observed_keys.isdisjoint(keys)
        observed_keys.update(keys)

        density_count = sum(item["counts"]["variant"] for item in body["density"])
        assert density_count == body["summary"]["variant"] == len(keys)
        observed_count += density_count

    overview = client.get("/api/v1/proteins/P00533/sequence/overview")
    assert overview.status_code == 200
    overview_body = overview.json()
    assert overview_body["response_bounds"]["variant_bin_semantics"] == SEMANTICS
    assert observed_count == len(observed_keys) == overview_body["totals"]["canonical_drawable_variants"]
