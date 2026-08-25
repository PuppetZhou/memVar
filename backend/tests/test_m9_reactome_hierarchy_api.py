from fastapi.testclient import TestClient

from app.main import app
from app.store import read_connection


client = TestClient(app)


def node_map(body: dict[str, object]) -> dict[str, dict[str, object]]:
    return {node["pathway_id"]: node for node in body["nodes"]}


def assert_normalized_dag(body: dict[str, object]) -> None:
    nodes = body["nodes"]
    by_id = node_map(body)
    node_ids = [node["pathway_id"] for node in nodes]

    assert len(node_ids) == len(set(node_ids)) == body["node_total"]
    assert len(body["roots"]) == body["root_total"]
    assert set(body["roots"]) <= set(node_ids)
    assert body["shared_node_total"] == sum(len(node["parent_ids"]) > 1 for node in nodes)

    def sort_key(pathway_id: str) -> tuple[bool, str, str]:
        name = by_id[pathway_id]["pathway_name"]
        return name is None, name or "", pathway_id

    assert node_ids == sorted(node_ids, key=sort_key)
    assert body["roots"] == sorted(body["roots"], key=sort_key)

    edges: set[tuple[str, str]] = set()
    for node in nodes:
        pathway_id = node["pathway_id"]
        assert node["parent_ids"] == sorted(node["parent_ids"], key=sort_key)
        assert node["child_ids"] == sorted(node["child_ids"], key=sort_key)
        for parent_id in node["parent_ids"]:
            assert parent_id in by_id
            assert pathway_id in by_id[parent_id]["child_ids"]
        for child_id in node["child_ids"]:
            assert child_id in by_id
            assert pathway_id in by_id[child_id]["parent_ids"]
            edges.add((pathway_id, child_id))

    assert len(edges) == body["edge_total"]
    assert body["roots"] == [pathway_id for pathway_id in node_ids if not by_id[pathway_id]["parent_ids"]]


def test_generated_reactome_hierarchy_is_a_unique_direct_edge_table() -> None:
    with read_connection() as connection:
        row_count, distinct_count, invalid_count = connection.execute(
            """
            SELECT
                count(*),
                count(DISTINCT (parent_pathway_id, child_pathway_id)),
                count(*) FILTER (
                    WHERE parent_pathway_id IS NULL
                       OR child_pathway_id IS NULL
                       OR parent_pathway_id = child_pathway_id
                )
            FROM reactome_hierarchy_edge
            """
        ).fetchone()

    assert row_count == distinct_count == 2899
    assert invalid_count == 0


def test_p00533_reactome_hierarchy_preserves_the_normalized_dag() -> None:
    first = client.get("/api/v1/proteins/P00533/reactome-hierarchy")
    second = client.get("/api/v1/proteins/P00533/reactome-hierarchy")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()

    body = first.json()
    assert body["uniprot_accession"] == "P00533"
    assert body["node_total"] == 78
    assert body["edge_total"] == 74
    assert body["root_total"] == 5
    assert body["shared_node_total"] == 1
    assert body["edge_semantics"] == "direct_parent_child"
    assert body["node_semantics"] == "protein_pathway_membership"
    assert body["roots"] == [
        "R-HSA-1266738",
        "R-HSA-1643685",
        "R-HSA-74160",
        "R-HSA-162582",
        "R-HSA-5653656",
    ]
    assert_normalized_dag(body)

    by_id = node_map(body)
    assert by_id["R-HSA-8847993"]["parent_ids"] == ["R-HSA-1227986", "R-HSA-8848021"]
    chain = ["R-HSA-162582", "R-HSA-9006934", "R-HSA-177929", "R-HSA-182971"]
    assert all(child_id in by_id[parent_id]["child_ids"] for parent_id, child_id in zip(chain, chain[1:]))


def test_sparse_reactome_hierarchy_keeps_its_single_direct_relation() -> None:
    response = client.get("/api/v1/proteins/A0FGR8/reactome-hierarchy")
    assert response.status_code == 200
    body = response.json()
    assert body["node_total"] == 2
    assert body["edge_total"] == 1
    assert body["root_total"] == 1
    assert body["shared_node_total"] == 0
    assert body["roots"] == ["R-HSA-382551"]
    assert_normalized_dag(body)

    by_id = node_map(body)
    assert by_id["R-HSA-382551"]["child_ids"] == ["R-HSA-9845576"]
    assert by_id["R-HSA-9845576"]["parent_ids"] == ["R-HSA-382551"]


def test_empty_reactome_hierarchy_is_explicit_and_missing_protein_is_404() -> None:
    response = client.get("/api/v1/proteins/A0A075B6H7/reactome-hierarchy")
    assert response.status_code == 200
    assert response.json() == {
        "uniprot_accession": "A0A075B6H7",
        "nodes": [],
        "roots": [],
        "node_total": 0,
        "edge_total": 0,
        "root_total": 0,
        "shared_node_total": 0,
        "edge_semantics": "direct_parent_child",
        "node_semantics": "protein_pathway_membership",
    }

    missing = client.get("/api/v1/proteins/NOT_A_PROTEIN/reactome-hierarchy")
    assert missing.status_code == 404
