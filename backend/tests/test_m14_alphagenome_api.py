from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_egfr_summary_is_reference_prediction_and_display_ready() -> None:
    response = client.get("/api/v1/proteins/p00533/alphagenome/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["uniprot_accession"] == "P00533"
    assert body["availability"] == "available"
    assert body["prediction_kind"] == "reference_sequence_tracks"
    assert body["genome_build"] == "GRCh38"
    assert body["has_variant_effect_scores"] is False
    assert body["local_output_subset"] is True
    assert body["missing_official_modalities"] == ["dnase", "chip_tf"]
    assert body["modality_track_counts"] == {
        "atac": 19, "cage": 34, "chip_histone": 135, "contact_maps": 2,
        "procap": 2, "rna_seq": 113, "splice_junctions": 61,
        "splice_site_usage": 122, "splice_sites": 4,
    }
    candidate = body["candidates"][0]
    assert candidate["ensembl_gene_id"] == "ENSG00000146648"
    assert candidate["mapping_status"] == "exact"
    assert candidate["display_ready"] is True
    assert candidate["tiles"][0]["tile_id"] == "tile_000"


def test_one_to_many_gene_mapping_is_preserved() -> None:
    response = client.get("/api/v1/proteins/A0A075B6P5/alphagenome/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["availability"] == "available"
    assert {item["ensembl_gene_id"] for item in body["candidates"]} == {
        "ENSG00000242534", "ENSG00000244116",
    }
    assert all(item["mapping_status"] == "ambiguous" and item["mapping_count"] == 2 for item in body["candidates"])


def test_no_prediction_and_no_ensembl_are_distinct_empty_states() -> None:
    no_prediction = client.get("/api/v1/proteins/A0A0G2JS06/alphagenome/summary")
    no_ensembl = client.get("/api/v1/proteins/A0A087X1C5/alphagenome/summary")
    assert no_prediction.status_code == no_ensembl.status_code == 200
    assert no_prediction.json()["availability"] == "unavailable"
    assert no_prediction.json()["candidates"][0]["mapping_status"] == "no_prediction"
    assert no_ensembl.json()["availability"] == "unavailable"
    assert no_ensembl.json()["candidates"][0]["mapping_status"] == "no_ensembl"


def test_track_catalog_signal_junction_and_contact_payloads_are_bounded() -> None:
    base = "/api/v1/proteins/P00533/alphagenome"
    shared = {"ensembl_gene_id": "ENSG00000146648", "tile_id": "tile_000"}
    tracks = client.get(f"{base}/tracks", params={"ensembl_gene_id": shared["ensembl_gene_id"], "modality": "rna_seq"})
    assert tracks.status_code == 200
    assert tracks.json()["total"] == len(tracks.json()["tracks"]) == 113

    signal = client.get(f"{base}/signals", params={**shared, "track_id": "rna_seq:000", "bins": 256})
    assert signal.status_code == 200
    signal_body = signal.json()
    assert signal_body["level_bins"] == 256
    assert signal_body["point_columns"] == ["mean", "max"]
    assert len(signal_body["values"]) == 256
    assert all(len(point) == 2 and point[1] >= point[0] for point in signal_body["values"])

    junctions = client.get(f"{base}/junctions", params={**shared, "track_id": "splice_junctions:000", "limit": 3})
    assert junctions.status_code == 200
    assert junctions.json()["returned_count"] <= 3
    assert junctions.json()["returned_count"] == len(junctions.json()["items"])

    contact = client.get(f"{base}/contact-map", params={**shared, "track_id": "contact_maps:000", "size": 128})
    assert contact.status_code == 200
    assert contact.json()["matrix_size"] == 128
    assert len(contact.json()["values"]) == 128 * 128

    cropped_contact = client.get(f"{base}/contact-map", params={
        **shared, "track_id": "contact_maps:000", "size": 128,
        "start": 55018819, "end": 55211628,
    })
    assert cropped_contact.status_code == 200
    cropped_body = cropped_contact.json()
    assert 1 < cropped_body["matrix_size"] < 128
    assert len(cropped_body["values"]) == cropped_body["matrix_size"] ** 2
    assert cropped_body["window_start_0based"] <= 55018819
    assert cropped_body["window_end_0based"] >= 55211628


def test_invalid_gene_track_window_and_bins_are_rejected() -> None:
    base = "/api/v1/proteins/P00533/alphagenome"
    assert client.get(f"{base}/tracks", params={"ensembl_gene_id": "ENSG00000000003", "modality": "rna_seq"}).status_code == 404
    assert client.get(f"{base}/tracks", params={"ensembl_gene_id": "ENSG00000146648", "modality": "dnase"}).status_code == 422
    assert client.get(f"{base}/signals", params={"ensembl_gene_id": "ENSG00000146648", "tile_id": "tile_000", "track_id": "rna_seq:000", "bins": 300}).status_code == 422
    assert client.get(f"{base}/signals", params={"ensembl_gene_id": "ENSG00000146648", "tile_id": "tile_000", "track_id": "rna_seq:000", "bins": 256, "start": 1, "end": 2}).status_code == 422
    assert client.get(f"{base}/contact-map", params={"ensembl_gene_id": "ENSG00000146648", "tile_id": "tile_000", "track_id": "contact_maps:000", "size": 128, "start": 1, "end": 2}).status_code == 422
    assert client.get("/api/v1/proteins/NOT_A_PROTEIN/alphagenome/summary").status_code == 404
