from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_p00533_summary_is_dataset_grouped_and_source_significant() -> None:
    response = client.get("/api/v1/proteins/p00533/differential-expression/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["uniprot_accession"] == "P00533"
    assert body["gene_symbol"] == "EGFR"
    assert body["dataset_total"] == 6
    assert body["contrast_total"] == 15
    assert body["mapping"] == {
        "method": "trim_casefold_exact_gene_symbol",
        "summary_membership": "source_is_significant_with_effect",
        "fdr_threshold": 0.05,
        "absolute_log2fc_threshold": 1.0,
    }
    assert len({item["dataset_id"] for item in body["datasets"]}) == body["dataset_total"]
    contrasts = [contrast for item in body["datasets"] for contrast in item["contrasts"]]
    assert len(contrasts) == body["contrast_total"]
    assert all(item["target_result_total"] == 1 for item in contrasts)
    assert all(item["mapping_status"] == "unique_gene_row" for item in contrasts)
    assert all(
        target["fdr"] < 0.05 and abs(target["log2fc"]) >= 1
        for item in contrasts for target in item["target_results"]
    )


def test_same_symbol_multiple_ensembl_rows_are_preserved_without_duplicate_contrast() -> None:
    response = client.get("/api/v1/proteins/P19440/differential-expression/summary")
    assert response.status_code == 200
    body = response.json()
    matches = [
        contrast
        for dataset in body["datasets"]
        for contrast in dataset["contrasts"]
        if contrast["contrast_id"] == "GEND000503_lusc_late_tumor_vs_adjacent"
    ]
    assert len(matches) == 1
    match = matches[0]
    assert match["mapping_status"] == "multiple_gene_rows_same_symbol"
    assert match["target_result_total"] == 2
    assert {
        (item["ensembl_gene_id"], item["direction"])
        for item in match["target_results"]
    } == {("ENSG00000100031", "down"), ("ENSG00000286070", "up")}


def test_sparse_and_empty_protein_states_are_explicit() -> None:
    sparse = client.get("/api/v1/proteins/A0A075B6J1/differential-expression/summary")
    assert sparse.status_code == 200
    assert sparse.json()["dataset_total"] == sparse.json()["contrast_total"] == 1

    empty = client.get("/api/v1/proteins/A0PK11/differential-expression/summary")
    assert empty.status_code == 200
    assert empty.json()["dataset_total"] == empty.json()["contrast_total"] == 0
    assert empty.json()["datasets"] == []


def test_volcano_has_exact_counts_flags_and_current_target() -> None:
    contrast_id = "GEND000023_clear_cell_renal_cell_carcinoma_vs_control"
    response = client.get(
        f"/api/v1/differential-expression/contrasts/{contrast_id}/volcano",
        params={"accession": "P00533"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["contrast"]["contrast_id"] == contrast_id
    assert body["counts"]["plotted"] + body["counts"]["unplottable"] == body["counts"]["tested"]
    assert len(body["points"]) == body["counts"]["plotted"]
    assert body["point_columns"][-2:] == ["is_membrane_mapped", "is_current_target"]
    targets = [point for point in body["points"] if point[-1]]
    assert targets and {point[2] for point in targets} == {"EGFR"}
    assert all(point[0] is not None and point[1] is not None and point[5] is not None for point in body["points"])
    for point in body["points"]:
        if point[5] == 0:
            assert point[1] == 300.0


def test_invalid_contrast_and_protein_cannot_resolve_arbitrary_paths() -> None:
    assert client.get(
        "/api/v1/differential-expression/contrasts/../../etc/passwd/volcano",
        params={"accession": "P00533"},
    ).status_code in {404, 405}
    assert client.get(
        "/api/v1/differential-expression/contrasts/not-a-real-contrast/volcano",
        params={"accession": "P00533"},
    ).status_code == 404
    assert client.get(
        "/api/v1/differential-expression/contrasts/GEND000023_clear_cell_renal_cell_carcinoma_vs_control/volcano",
        params={"accession": "NOT_A_PROTEIN"},
    ).status_code == 404
