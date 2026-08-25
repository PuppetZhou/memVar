from __future__ import annotations

from pathlib import Path
import sys

import duckdb


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_core  # noqa: E402


def test_go_evidence_table_keeps_raw_evidence_fields_and_validates_core_membership(
    tmp_path: Path,
) -> None:
    source = tmp_path / "go_annotation.parquet"
    connection = duckdb.connect()
    connection.execute("CREATE TABLE protein_overview (uniprot_accession VARCHAR)")
    connection.execute("INSERT INTO protein_overview VALUES ('P00533')")
    connection.execute(
        """
        CREATE TABLE go_annotation AS
        SELECT * FROM (VALUES
          ('P00533', 'GO:0005006', 'epidermal growth factor receptor activity', 'MF',
           'molecular_function', 'enables', false, 'IDA', 'PMID:12828935', NULL,
           'UniProt', 'part_of(GO:0007169)', '20231211'),
          ('P00533', 'GO:0008150', 'biological_process', 'BP', 'biological_process',
           'NOT|involved_in', true, 'IEA', 'GO_REF:0000043', 'InterPro:IPR000719',
           'UniProt', NULL, '20240101'),
          ('OUTSIDE', 'GO:0005576', 'extracellular region', 'CC', 'cellular_component',
           'located_in', false, 'IEA', NULL, NULL, 'UniProt', NULL, '20240101')
        ) AS t(
          uniprot_accession, go_id, go_term_name, go_aspect, go_namespace,
          relation_qualifier, is_negated, evidence_code, reference_id, with_from,
          assigned_by, annotation_extension, annotation_date
        )
        """
    )
    connection.execute(f"COPY go_annotation TO '{source}' (FORMAT PARQUET)")

    build_core.create_go_evidence(connection, str(source))

    assert connection.execute("SELECT count(*) FROM go_evidence").fetchone()[0] == 2
    row = connection.execute(
        """
        SELECT go_id, qualifier, is_negated, evidence_code, reference_id, with_from,
               assigned_by, annotation_extension, annotation_date
        FROM go_evidence WHERE go_id = 'GO:0005006'
        """
    ).fetchone()
    assert row == (
        'GO:0005006', 'enables', False, 'IDA', 'PMID:12828935', None,
        'UniProt', 'part_of(GO:0007169)', '20231211',
    )
    assert connection.execute(
        "SELECT count(*) FROM go_evidence WHERE NOT regexp_full_match(go_id, 'GO:[0-9]{7}')"
    ).fetchone()[0] == 0
    assert connection.execute(
        """
        SELECT count(*) FROM go_evidence e LEFT JOIN protein_overview o USING (uniprot_accession)
        WHERE o.uniprot_accession IS NULL
        """
    ).fetchone()[0] == 0
    connection.close()
