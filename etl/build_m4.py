#!/usr/bin/env python3
"""Build M4 protein-scoped interaction and disease data from immutable View.

Interaction summaries and disease source tables are stored in
``memvar_m4.duckdb``. BioGRID and IntAct membership evidence, plus IntAct
mutation effects, are written as source/accession-bucketed ZSTD Parquet.
Earlier milestone artifacts are neither read as scientific sources nor
replaced by this build.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import time
import uuid

import duckdb

from build_core import DEFAULT_OUTPUT_ROOT, DEFAULT_VIEW_ROOT, fail, path_is_within
from build_m2 import bucket_sql


SOURCES: dict[str, set[str]] = {
    "Basic_info/protein_basic.parquet": {"uniprot_accession"},
    "Basic_info/gene_identifier_bridge.parquet": {
        "uniprot_accession", "identifier_database", "identifier_base",
    },
    "Interaction/biogrid_project_interaction_evidence.parquet": {
        "#BioGRID Interaction ID", "Entrez Gene Interactor A",
        "Entrez Gene Interactor B", "Official Symbol Interactor A",
        "Official Symbol Interactor B", "SWISS-PROT Accessions Interactor A",
        "SWISS-PROT Accessions Interactor B", "Organism ID Interactor A",
        "Organism ID Interactor B", "Experimental System",
        "Experimental System Type", "Throughput", "Publication Source", "Score",
        "Modification", "Qualifications", "Tags", "Ontology Term IDs",
        "Ontology Term Names", "Ontology Term Categories",
        "Ontology Term Qualifier IDs", "Ontology Term Qualifier Names",
        "Ontology Term Types", "mapped_membrane_gene_id_interactor_a",
        "mapped_membrane_gene_id_interactor_b", "project_context", "context_class",
    },
    "Interaction/intact_context_interaction_evidence.parquet": {
        "#ID(s) interactor A", "ID(s) interactor B", "Alt. ID(s) interactor A",
        "Alt. ID(s) interactor B", "Alias(es) interactor A",
        "Alias(es) interactor B", "Interaction detection method(s)",
        "Publication 1st author(s)", "Publication Identifier(s)",
        "Taxid interactor A", "Taxid interactor B", "Interaction type(s)",
        "Source database(s)", "Interaction identifier(s)", "Confidence value(s)",
        "Expansion method(s)", "Biological role(s) interactor A",
        "Biological role(s) interactor B", "Experimental role(s) interactor A",
        "Experimental role(s) interactor B", "Type(s) interactor A",
        "Type(s) interactor B", "Annotation(s) interactor A",
        "Annotation(s) interactor B", "Interaction annotation(s)",
        "Host organism(s)", "Interaction parameter(s)", "Creation date",
        "Update date", "Negative", "Feature(s) interactor A",
        "Feature(s) interactor B", "Stoichiometry(s) interactor A",
        "Stoichiometry(s) interactor B", "Identification method participant A",
        "Identification method participant B",
        "source_uniprotkb_accession_interactor_a",
        "source_uniprotkb_accession_interactor_b",
        "mapped_membrane_accession_interactor_a",
        "mapped_membrane_accession_interactor_b", "context", "context_class",
    },
    "Interaction/intact_mutation_effect.parquet": {
        "#Feature AC", "Feature short label", "Feature range(s)",
        "Original sequence", "Resulting sequence", "Feature type",
        "Feature annotation", "Affected protein AC", "Affected protein symbol",
        "Affected protein full name", "Affected protein organism",
        "Interaction participants", "PubMedID", "Figure legend", "Interaction AC",
        "mapped_membrane_accession",
    },
    "Disease/clingen_gene_disease_validity.parquet": {
        "hgnc_id", "gene_symbol", "disease_id", "disease_name", "moi",
        "sop_version", "classification", "report_url", "classification_date",
        "expert_panel", "mapped_accessions", "mapped_accession_count",
    },
    "Disease/clingen_dosage.parquet": {
        "hgnc_id", "gene_symbol", "haploinsufficiency", "triplosensitivity",
        "report_url", "curation_date", "mapped_accessions",
        "mapped_accession_count",
    },
    "Disease/gencc_assertion.parquet": {
        "assertion_id", "assertion_version", "hgnc_id", "gene_symbol",
        "disease_id", "disease_name", "source_disease_id", "source_disease_name",
        "classification_id", "classification", "moi_id", "moi", "submitter_id",
        "submitter", "assertion_date", "pmids", "public_report_url",
        "criteria_url", "source_submission_id", "mapped_accessions",
        "mapped_accession_count",
    },
    "Disease/omim_gene_disease.parquet": {
        "chromosome", "cyto_location", "locus_mim_number", "gene_id",
        "ensembl_gene_id", "gene_symbol", "disease_id", "disease_name",
        "inheritance", "mapping_key", "relationship_status", "disease_id_source",
    },
    "Disease/hpo_gene_disease.parquet": {
        "gene_id", "gene_symbol", "disease_id", "disease_name",
        "unique_source_hpo_count", "hpo_annotation_evidence_count",
        "explicitly_absent_annotation_count",
    },
    "Disease/hpo_disease_phenotype.parquet": {
        "disease_id", "disease_name", "qualifier", "hpo_name", "hpo_id",
        "reference", "evidence_code", "onset", "frequency", "sex", "modifier",
        "aspect", "biocuration", "phenotype_status",
    },
    "Disease/mondo_term.parquet": {"mondo_id", "name", "is_obsolete", "replaced_by"},
    "Disease/mondo_xref.parquet": {
        "mondo_id", "external_id", "xref_raw", "xref_relation",
        "eligible_for_unique_merge",
    },
    "Disease/mondo_category36_rollup.parquet": {
        "mondo_id", "category_mondo_id", "category_name", "category_axis",
        "is_hereditary", "is_neoplastic",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view-root", type=Path, default=DEFAULT_VIEW_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--accession", action="append", default=[])
    parser.add_argument("--threads", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    return parser.parse_args()


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def source(view_root: Path, relative: str) -> str:
    return sql_path(view_root / relative)


def validate_paths(view_root: Path, output_root: Path) -> tuple[Path, Path]:
    view_root = view_root.resolve()
    output_root = output_root.resolve()
    allowed = DEFAULT_OUTPUT_ROOT.resolve()
    if not view_root.is_dir():
        fail(f"View root does not exist: {view_root}")
    if output_root == view_root or path_is_within(output_root, view_root):
        fail(f"Refusing output in immutable View tree: {output_root}")
    if not path_is_within(output_root, allowed):
        fail(f"Output must stay under {allowed}: {output_root}")
    return view_root, output_root


def actual_columns(con: duckdb.DuckDBPyConnection, path: Path) -> set[str]:
    return {row[0] for row in con.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]
    ).fetchall()}


def validate_sources(con: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    for relative, required in SOURCES.items():
        path = view_root / relative
        if not path.is_file():
            fail(f"Required source file is missing: {path}")
        missing = sorted(required - actual_columns(con, path))
        if missing:
            fail(f"{path} is missing required columns: {', '.join(missing)}")
    quarantine = {
        path.name for path in (view_root / "Disease").glob("*quarantine*.parquet")
    }
    expected = {
        "clingen_gene_disease_validity_quarantine.parquet",
        "clingen_dosage_quarantine.parquet",
    }
    if quarantine != expected:
        fail(f"ClinGen quarantine contract changed: {sorted(quarantine)}")


def accession_predicate(accessions: list[str], alias: str = "") -> str:
    if not accessions:
        return "TRUE"
    prefix = f"{alias}." if alias else ""
    values = ", ".join("'" + value.replace("'", "''") + "'" for value in accessions)
    return f"{prefix}uniprot_accession IN ({values})"


def create_scope_and_bridge(
    con: duckdb.DuckDBPyConnection, view_root: Path, accessions: list[str]
) -> None:
    basic = source(view_root, "Basic_info/protein_basic.parquet")
    bridge = source(view_root, "Basic_info/gene_identifier_bridge.parquet")
    con.execute(f"""
        CREATE TEMP TABLE protein_scope AS
        SELECT uniprot_accession FROM read_parquet('{basic}')
        WHERE {accession_predicate(accessions)};

        CREATE TEMP TABLE geneid_protein_bridge AS
        SELECT DISTINCT g.identifier_base AS gene_id, g.uniprot_accession
        FROM read_parquet('{bridge}') g
        JOIN protein_scope s USING (uniprot_accession)
        WHERE g.identifier_database = 'GeneID' AND g.identifier_base IS NOT NULL;
    """)
    found = {row[0] for row in con.execute(
        "SELECT uniprot_accession FROM protein_scope"
    ).fetchall()}
    if not found:
        fail("No requested accession exists in protein_basic")
    missing = sorted(set(accessions) - found)
    if missing:
        fail(f"Unknown accession(s): {', '.join(missing)}")


def copy_partitioned(
    con: duckdb.DuckDBPyConnection, query: str, target: Path
) -> None:
    target.mkdir(parents=True, exist_ok=False)
    con.execute(
        f"COPY ({query}) TO '{sql_path(target)}' "
        "(FORMAT PARQUET, PARTITION_BY (accession_bucket), COMPRESSION ZSTD, "
        "ROW_GROUP_SIZE 100000)"
    )


def build_biogrid(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> None:
    path = source(view_root, "Interaction/biogrid_project_interaction_evidence.parquet")
    con.execute(f"""
        CREATE TEMP TABLE biogrid_source AS
        SELECT row_number() OVER () AS source_row_number, *
        FROM read_parquet('{path}');

        CREATE TEMP TABLE biogrid_membership AS
        WITH endpoint_membership AS (
          SELECT x.source_row_number, b.uniprot_accession, 'A' AS endpoint
          FROM biogrid_source x JOIN geneid_protein_bridge b
            ON nullif(x.mapped_membrane_gene_id_interactor_a, '') = b.gene_id
          UNION ALL
          SELECT x.source_row_number, b.uniprot_accession, 'B' AS endpoint
          FROM biogrid_source x JOIN geneid_protein_bridge b
            ON nullif(x.mapped_membrane_gene_id_interactor_b, '') = b.gene_id
        )
        SELECT source_row_number, uniprot_accession,
          CASE WHEN count(DISTINCT endpoint) = 2 THEN 'both'
               ELSE lower(min(endpoint)) END AS page_role
        FROM endpoint_membership
        GROUP BY source_row_number, uniprot_accession;
    """)
    relation = f"""
        SELECT m.uniprot_accession, 'BioGRID'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release,
          'evidence membership by project context'::VARCHAR AS evidence_grain,
          m.page_role, x."#BioGRID Interaction ID" AS native_interaction_id,
          CASE WHEN m.page_role = 'a' THEN nullif(x."Entrez Gene Interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."Entrez Gene Interactor A", '')
               ELSE concat_ws(' | ', nullif(x."Entrez Gene Interactor A", ''),
                    nullif(x."Entrez Gene Interactor B", '')) END AS partner_gene_id,
          CASE WHEN m.page_role = 'a' THEN nullif(x."Official Symbol Interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."Official Symbol Interactor A", '')
               ELSE concat_ws(' | ', nullif(x."Official Symbol Interactor A", ''),
                    nullif(x."Official Symbol Interactor B", '')) END AS partner_symbol,
          CASE WHEN m.page_role = 'a' THEN nullif(x."SWISS-PROT Accessions Interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."SWISS-PROT Accessions Interactor A", '')
               ELSE concat_ws(' | ', nullif(x."SWISS-PROT Accessions Interactor A", ''),
                    nullif(x."SWISS-PROT Accessions Interactor B", '')) END AS partner_swissprot_accessions,
          CASE WHEN m.page_role = 'a' THEN nullif(x."Organism ID Interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."Organism ID Interactor A", '')
               ELSE concat_ws(' | ', nullif(x."Organism ID Interactor A", ''),
                    nullif(x."Organism ID Interactor B", '')) END AS partner_taxid,
          nullif(x."Entrez Gene Interactor A", '') AS interactor_a_gene_id,
          nullif(x."Entrez Gene Interactor B", '') AS interactor_b_gene_id,
          nullif(x."Official Symbol Interactor A", '') AS interactor_a_symbol,
          nullif(x."Official Symbol Interactor B", '') AS interactor_b_symbol,
          nullif(x."SWISS-PROT Accessions Interactor A", '') AS interactor_a_swissprot_accessions,
          nullif(x."SWISS-PROT Accessions Interactor B", '') AS interactor_b_swissprot_accessions,
          nullif(x."Organism ID Interactor A", '') AS interactor_a_taxid,
          nullif(x."Organism ID Interactor B", '') AS interactor_b_taxid,
          nullif(x.mapped_membrane_gene_id_interactor_a, '') AS mapped_membrane_gene_id_a,
          nullif(x.mapped_membrane_gene_id_interactor_b, '') AS mapped_membrane_gene_id_b,
          nullif(x."Experimental System", '') AS experimental_system,
          nullif(x."Experimental System Type", '') AS interaction_category,
          nullif(x."Throughput", '') AS throughput,
          nullif(x."Publication Source", '') AS publication,
          nullif(x."Score", '') AS score, nullif(x."Modification", '') AS modification,
          nullif(x."Qualifications", '') AS qualifications,
          nullif(x."Tags", '') AS tags,
          nullif(x."Ontology Term IDs", '') AS ontology_term_ids,
          nullif(x."Ontology Term Names", '') AS ontology_term_names,
          nullif(x."Ontology Term Categories", '') AS ontology_term_categories,
          nullif(x."Ontology Term Qualifier IDs", '') AS ontology_term_qualifier_ids,
          nullif(x."Ontology Term Qualifier Names", '') AS ontology_term_qualifier_names,
          nullif(x."Ontology Term Types", '') AS ontology_term_types,
          nullif(x.project_context, '') AS context,
          nullif(x.context_class, '') AS context_class,
          {bucket_sql('m.uniprot_accession')} AS accession_bucket
        FROM biogrid_source x JOIN biogrid_membership m USING (source_row_number)
    """
    copy_partitioned(
        con, relation + " ORDER BY accession_bucket, m.uniprot_accession, "
        "x.context_class, x.project_context, x.\"#BioGRID Interaction ID\"",
        root / "interaction" / "source=BioGRID",
    )


def build_intact(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> None:
    path = source(view_root, "Interaction/intact_context_interaction_evidence.parquet")
    con.execute(f"""
        CREATE TEMP TABLE intact_source AS
        SELECT row_number() OVER () AS source_row_number, *
        FROM read_parquet('{path}');

        CREATE TEMP TABLE intact_membership AS
        WITH endpoint_membership AS (
          SELECT x.source_row_number, x.mapped_membrane_accession_interactor_a
            AS uniprot_accession, 'A' AS endpoint
          FROM intact_source x JOIN protein_scope s
            ON nullif(x.mapped_membrane_accession_interactor_a, '') = s.uniprot_accession
          UNION ALL
          SELECT x.source_row_number, x.mapped_membrane_accession_interactor_b,
            'B' AS endpoint
          FROM intact_source x JOIN protein_scope s
            ON nullif(x.mapped_membrane_accession_interactor_b, '') = s.uniprot_accession
        )
        SELECT source_row_number, uniprot_accession,
          CASE WHEN count(DISTINCT endpoint) = 2 THEN 'both'
               ELSE lower(min(endpoint)) END AS page_role
        FROM endpoint_membership
        GROUP BY source_row_number, uniprot_accession;
    """)
    relation = f"""
        SELECT m.uniprot_accession, 'IntAct'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release,
          'evidence membership by curation context'::VARCHAR AS evidence_grain,
          m.page_role, nullif(x."Interaction identifier(s)", '') AS native_interaction_id,
          CASE WHEN m.page_role = 'a' THEN nullif(x."ID(s) interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."#ID(s) interactor A", '')
               ELSE concat_ws(' | ', nullif(x."#ID(s) interactor A", ''),
                    nullif(x."ID(s) interactor B", '')) END AS partner_raw_id,
          CASE WHEN m.page_role = 'a' THEN nullif(x."Alias(es) interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."Alias(es) interactor A", '')
               ELSE concat_ws(' | ', nullif(x."Alias(es) interactor A", ''),
                    nullif(x."Alias(es) interactor B", '')) END AS partner_alias,
          CASE WHEN m.page_role = 'a' THEN nullif(x."Taxid interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."Taxid interactor A", '')
               ELSE concat_ws(' | ', nullif(x."Taxid interactor A", ''),
                    nullif(x."Taxid interactor B", '')) END AS partner_taxid,
          CASE WHEN m.page_role = 'a' THEN nullif(x."Type(s) interactor B", '')
               WHEN m.page_role = 'b' THEN nullif(x."Type(s) interactor A", '')
               ELSE concat_ws(' | ', nullif(x."Type(s) interactor A", ''),
                    nullif(x."Type(s) interactor B", '')) END AS partner_type,
          nullif(x."#ID(s) interactor A", '') AS interactor_a_raw_id,
          nullif(x."ID(s) interactor B", '') AS interactor_b_raw_id,
          nullif(x."Alt. ID(s) interactor A", '') AS interactor_a_alt_id,
          nullif(x."Alt. ID(s) interactor B", '') AS interactor_b_alt_id,
          nullif(x."Alias(es) interactor A", '') AS interactor_a_alias,
          nullif(x."Alias(es) interactor B", '') AS interactor_b_alias,
          nullif(x."Taxid interactor A", '') AS interactor_a_taxid,
          nullif(x."Taxid interactor B", '') AS interactor_b_taxid,
          nullif(x."Type(s) interactor A", '') AS interactor_a_type,
          nullif(x."Type(s) interactor B", '') AS interactor_b_type,
          nullif(x.source_uniprotkb_accession_interactor_a, '') AS source_uniprot_accession_a,
          nullif(x.source_uniprotkb_accession_interactor_b, '') AS source_uniprot_accession_b,
          nullif(x.mapped_membrane_accession_interactor_a, '') AS mapped_membrane_accession_a,
          nullif(x.mapped_membrane_accession_interactor_b, '') AS mapped_membrane_accession_b,
          nullif(x."Interaction detection method(s)", '') AS detection_method,
          nullif(x."Interaction type(s)", '') AS interaction_type,
          CASE WHEN lower(nullif(x."Negative", '')) = 'true' THEN 'negative'
               ELSE 'positive' END AS interaction_category,
          nullif(x."Publication 1st author(s)", '') AS publication_first_author,
          nullif(x."Publication Identifier(s)", '') AS publication,
          nullif(x."Source database(s)", '') AS source_database_raw,
          nullif(x."Confidence value(s)", '') AS confidence,
          nullif(x."Expansion method(s)", '') AS expansion_method,
          nullif(x."Biological role(s) interactor A", '') AS biological_role_a,
          nullif(x."Biological role(s) interactor B", '') AS biological_role_b,
          nullif(x."Experimental role(s) interactor A", '') AS experimental_role_a,
          nullif(x."Experimental role(s) interactor B", '') AS experimental_role_b,
          nullif(x."Annotation(s) interactor A", '') AS annotation_a,
          nullif(x."Annotation(s) interactor B", '') AS annotation_b,
          nullif(x."Interaction annotation(s)", '') AS interaction_annotation,
          nullif(x."Host organism(s)", '') AS host_organism,
          nullif(x."Interaction parameter(s)", '') AS interaction_parameters,
          nullif(x."Creation date", '') AS creation_date,
          nullif(x."Update date", '') AS update_date,
          CASE WHEN lower(nullif(x."Negative", '')) = 'true' THEN true
               WHEN lower(nullif(x."Negative", '')) = 'false' THEN false
               ELSE NULL END AS is_negative,
          nullif(x."Feature(s) interactor A", '') AS features_a,
          nullif(x."Feature(s) interactor B", '') AS features_b,
          nullif(x."Stoichiometry(s) interactor A", '') AS stoichiometry_a,
          nullif(x."Stoichiometry(s) interactor B", '') AS stoichiometry_b,
          nullif(x."Identification method participant A", '') AS identification_method_a,
          nullif(x."Identification method participant B", '') AS identification_method_b,
          nullif(x.context, '') AS context, nullif(x.context_class, '') AS context_class,
          {bucket_sql('m.uniprot_accession')} AS accession_bucket
        FROM intact_source x JOIN intact_membership m USING (source_row_number)
    """
    copy_partitioned(
        con, relation + " ORDER BY accession_bucket, m.uniprot_accession, "
        "x.context_class, x.context, x.\"Interaction identifier(s)\"",
        root / "interaction" / "source=IntAct",
    )


def build_mutation_effect(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> None:
    path = source(view_root, "Interaction/intact_mutation_effect.parquet")
    relation = f"""
        SELECT x.mapped_membrane_accession AS uniprot_accession,
          'IntAct'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release,
          'mutation feature row; excluded from general interaction counts'::VARCHAR
            AS evidence_grain,
          nullif(x."#Feature AC", '') AS feature_ac,
          nullif(x."Feature short label", '') AS feature_short_label,
          nullif(x."Feature range(s)", '') AS feature_ranges,
          nullif(x."Original sequence", '') AS original_sequence,
          nullif(x."Resulting sequence", '') AS resulting_sequence,
          nullif(x."Feature type", '') AS feature_type,
          nullif(x."Feature annotation", '') AS feature_annotation,
          nullif(x."Affected protein AC", '') AS affected_protein_ac,
          nullif(x."Affected protein symbol", '') AS affected_protein_symbol,
          nullif(x."Affected protein full name", '') AS affected_protein_full_name,
          nullif(x."Affected protein organism", '') AS affected_protein_organism,
          nullif(x."Interaction participants", '') AS interaction_participants,
          nullif(x."PubMedID", '') AS pubmed_id,
          nullif(x."Figure legend", '') AS figure_legend,
          nullif(x."Interaction AC", '') AS interaction_ac,
          {bucket_sql('x.mapped_membrane_accession')} AS accession_bucket
        FROM read_parquet('{path}') x JOIN protein_scope s
          ON nullif(x.mapped_membrane_accession, '') = s.uniprot_accession
    """
    copy_partitioned(
        con, relation + " ORDER BY accession_bucket, x.mapped_membrane_accession, "
        "x.\"Interaction AC\", x.\"#Feature AC\"",
        root / "interaction_mutation" / "source=IntAct",
    )


def build_interaction_summary(con: duckdb.DuckDBPyConnection, root: Path) -> None:
    biogrid = sql_path(root / "interaction" / "source=BioGRID" / "**" / "*.parquet")
    intact = sql_path(root / "interaction" / "source=IntAct" / "**" / "*.parquet")
    con.execute(f"""
        CREATE TABLE interaction_summary AS
        SELECT uniprot_accession, source_database, context_class, context,
          interaction_category, count(*)::BIGINT AS evidence_record_count,
          count(DISTINCT native_interaction_id)::BIGINT
            AS distinct_native_interaction_count
        FROM read_parquet(['{biogrid}', '{intact}'], hive_partitioning=true,
          union_by_name=true)
        GROUP BY uniprot_accession, source_database, context_class, context,
          interaction_category
        ORDER BY uniprot_accession, source_database, context_class, context,
          interaction_category;

        CREATE TABLE interaction_source_semantics AS
        SELECT * FROM (VALUES
          ('BioGRID', 'evidence membership by project context',
            'Physical and genetic evidence remain separate; context is curation scope, not activity.'),
          ('IntAct', 'evidence membership by curation context',
            'Negative evidence and expansion context are retained; context is not activity.'),
          ('IntAct mutation', 'mutation feature row',
            'Mutation effects are independent and excluded from general interaction counts.')
        ) AS t(source_database, evidence_grain, caveat);
    """)


def split_mapped_source(
    con: duckdb.DuckDBPyConnection, view_root: Path, filename: str,
    table_name: str, source_database: str, evidence_grain: str,
) -> None:
    path = source(view_root, f"Disease/{filename}")
    con.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT trim(a.accession) AS uniprot_accession, x.*,
          '{source_database}'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release,
          '{evidence_grain}'::VARCHAR AS evidence_grain
        FROM read_parquet('{path}') x,
          unnest(string_split(x.mapped_accessions, ';')) AS a(accession)
        JOIN protein_scope s ON trim(a.accession) = s.uniprot_accession
        WHERE trim(a.accession) <> ''
        ORDER BY uniprot_accession;
    """)


def build_disease(con: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    split_mapped_source(
        con, view_root, "clingen_gene_disease_validity.parquet",
        "disease_clingen_validity", "ClinGen validity", "expert-panel assertion",
    )
    split_mapped_source(
        con, view_root, "clingen_dosage.parquet", "disease_clingen_dosage",
        "ClinGen dosage", "gene dosage curation",
    )
    split_mapped_source(
        con, view_root, "gencc_assertion.parquet", "disease_gencc_assertion",
        "GenCC", "submitter-specific assertion",
    )
    omim = source(view_root, "Disease/omim_gene_disease.parquet")
    hpo_gene = source(view_root, "Disease/hpo_gene_disease.parquet")
    hpo_pheno = source(view_root, "Disease/hpo_disease_phenotype.parquet")
    mondo_term = source(view_root, "Disease/mondo_term.parquet")
    mondo_xref = source(view_root, "Disease/mondo_xref.parquet")
    mondo_category = source(view_root, "Disease/mondo_category36_rollup.parquet")
    con.execute(f"""
        CREATE TABLE disease_omim_gene_disease AS
        SELECT b.uniprot_accession, x.*, 'OMIM'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release,
          'gene record phenotype relationship'::VARCHAR AS evidence_grain
        FROM read_parquet('{omim}') x JOIN geneid_protein_bridge b USING (gene_id)
        ORDER BY b.uniprot_accession, x.disease_id, x.locus_mim_number;

        CREATE TABLE disease_hpo_gene AS
        SELECT b.uniprot_accession, x.*, 'HPO'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release,
          'GeneID-disease relationship'::VARCHAR AS evidence_grain
        FROM read_parquet('{hpo_gene}') x JOIN geneid_protein_bridge b USING (gene_id)
        ORDER BY b.uniprot_accession, x.disease_id, x.gene_id;

        CREATE TEMP TABLE hpo_protein_evidence AS
        SELECT g.uniprot_accession, g.gene_id, g.gene_symbol,
          p.*, 'HPO'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release,
          'disease-phenotype annotation evidence'::VARCHAR AS evidence_grain
        FROM disease_hpo_gene g JOIN read_parquet('{hpo_pheno}') p USING (disease_id);

        CREATE TABLE disease_hpo_observed AS
        SELECT * FROM hpo_protein_evidence
        WHERE phenotype_status = 'observed' AND coalesce(aspect, '') <> 'I'
        ORDER BY uniprot_accession, disease_id, hpo_id;

        CREATE TABLE disease_hpo_explicitly_absent AS
        SELECT * FROM hpo_protein_evidence
        WHERE (phenotype_status = 'explicitly_absent' OR qualifier = 'NOT')
          AND coalesce(aspect, '') <> 'I'
        ORDER BY uniprot_accession, disease_id, hpo_id;

        CREATE TABLE disease_hpo_inheritance AS
        SELECT * FROM hpo_protein_evidence WHERE aspect = 'I'
        ORDER BY uniprot_accession, disease_id, hpo_id;

        CREATE TEMP TABLE public_disease_ids AS
        SELECT DISTINCT disease_id AS source_disease_id FROM disease_clingen_validity
        WHERE disease_id IS NOT NULL
        UNION SELECT DISTINCT disease_id FROM disease_gencc_assertion WHERE disease_id IS NOT NULL
        UNION SELECT DISTINCT source_disease_id FROM disease_gencc_assertion
          WHERE source_disease_id IS NOT NULL
        UNION SELECT DISTINCT disease_id FROM disease_omim_gene_disease WHERE disease_id IS NOT NULL
        UNION SELECT DISTINCT disease_id FROM disease_hpo_gene WHERE disease_id IS NOT NULL;

        CREATE TABLE disease_mondo_exact AS
        WITH exact_map AS (
          SELECT d.source_disease_id, d.source_disease_id AS mondo_id,
            'direct MONDO identifier'::VARCHAR AS mapping_basis
          FROM public_disease_ids d JOIN read_parquet('{mondo_term}') t
            ON d.source_disease_id = t.mondo_id
          UNION
          SELECT d.source_disease_id, x.mondo_id,
            'eligible exact MONDO xref'::VARCHAR AS mapping_basis
          FROM public_disease_ids d JOIN read_parquet('{mondo_xref}') x
            ON d.source_disease_id = x.external_id
          WHERE lower(x.eligible_for_unique_merge) = 'true'
        )
        SELECT e.source_disease_id, e.mondo_id, t.name AS mondo_name,
          CASE WHEN lower(t.is_obsolete) = 'true' THEN true ELSE false END AS is_obsolete,
          nullif(t.replaced_by, '') AS replaced_by, e.mapping_basis
        FROM exact_map e JOIN read_parquet('{mondo_term}') t USING (mondo_id)
        ORDER BY source_disease_id, mondo_id;

        CREATE TABLE disease_mondo_category AS
        SELECT e.source_disease_id, e.mondo_id, c.category_mondo_id,
          c.category_name, c.category_axis,
          CASE WHEN lower(c.is_hereditary) = 'true' THEN true ELSE false END AS is_hereditary,
          CASE WHEN lower(c.is_neoplastic) = 'true' THEN true ELSE false END AS is_neoplastic
        FROM disease_mondo_exact e JOIN read_parquet('{mondo_category}') c USING (mondo_id)
        ORDER BY e.source_disease_id, e.mondo_id, c.category_axis, c.category_mondo_id;

        CREATE TABLE disease_source_semantics AS
        SELECT * FROM (VALUES
          ('ClinGen validity', 'expert-panel assertion',
            'Disputed and Refuted are conflict states, not weak positive evidence.'),
          ('ClinGen dosage', 'gene dosage curation',
            'Haploinsufficiency and triplosensitivity are retained independently.'),
          ('GenCC', 'submitter-specific assertion',
            'Assertions remain independent by submitter and are not voted across sources.'),
          ('OMIM', 'gene record phenotype relationship',
            'Inheritance, mapping key, relationship status, and cytogenetic location are retained.'),
          ('HPO', 'disease-phenotype annotation evidence',
            'Observed, explicitly absent, and inheritance-aspect records are separate.')
        ) AS t(source_database, evidence_grain, caveat);
    """)


def finalize_database(con: duckdb.DuckDBPyConnection, accessions: list[str]) -> None:
    scope = ",".join(accessions) if accessions else "all"
    con.execute(f"""
        CREATE TABLE build_scope AS SELECT
          '{scope.replace(chr(39), chr(39) * 2)}'::VARCHAR AS scope,
          128::INTEGER AS accession_bucket_count;
        CHECKPOINT;
    """)


def parquet_count(con: duckdb.DuckDBPyConnection, path: Path) -> int:
    files = list(path.glob("**/*.parquet"))
    if not files:
        return 0
    glob = sql_path(path / "**" / "*.parquet")
    return int(con.execute(
        f"SELECT count(*) FROM read_parquet('{glob}', hive_partitioning=true)"
    ).fetchone()[0])


def validate_build(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> dict[str, int]:
    counts: dict[str, int] = {}
    full_scope = con.execute("SELECT count(*) FROM protein_scope").fetchone()[0] == 7728
    paths = {
        "interaction_BioGRID": root / "interaction" / "source=BioGRID",
        "interaction_IntAct": root / "interaction" / "source=IntAct",
        "interaction_IntAct_mutation": root / "interaction_mutation" / "source=IntAct",
    }
    for name, path in paths.items():
        counts[name] = parquet_count(con, path)
        if not counts[name] and full_scope:
            fail(f"{name} output is unexpectedly empty")

    for source_name in ("BioGRID", "IntAct"):
        path = paths[f"interaction_{source_name}"]
        glob = sql_path(path / "**" / "*.parquet")
        if not list(path.glob("**/*.parquet")):
            continue
        bad = con.execute(f"""
            SELECT count(*) FROM read_parquet('{glob}', hive_partitioning=true)
            WHERE accession_bucket < 0 OR accession_bucket >= 128
              OR nullif(native_interaction_id, '') IS NULL
        """).fetchone()[0]
        if bad:
            fail(f"{source_name} detail violates bucket/native ID contract ({bad:,})")
        if source_name == "BioGRID":
            bad_category = con.execute(f"""
                SELECT count(*) FROM read_parquet('{glob}', hive_partitioning=true)
                WHERE interaction_category NOT IN ('physical', 'genetic')
            """).fetchone()[0]
            if bad_category:
                fail(f"BioGRID physical/genetic contract violated ({bad_category:,})")
        else:
            source_negative = con.execute(
                f"SELECT count(*) FROM read_parquet('{glob}', hive_partitioning=true) "
                "WHERE is_negative"
            ).fetchone()[0]
            if full_scope and source_negative == 0:
                fail("IntAct negative evidence was lost")

    summary_total = {row[0]: int(row[1]) for row in con.execute(
        "SELECT source_database, sum(evidence_record_count) "
        "FROM interaction_summary GROUP BY source_database"
    ).fetchall()}
    for source_name in ("BioGRID", "IntAct"):
        if summary_total.get(source_name, 0) != counts[f"interaction_{source_name}"]:
            fail(f"{source_name} interaction summary/detail count mismatch")
    counts["interaction_summary"] = int(con.execute(
        "SELECT count(*) FROM interaction_summary"
    ).fetchone()[0])

    disease_tables = (
        "disease_clingen_validity", "disease_clingen_dosage",
        "disease_gencc_assertion", "disease_omim_gene_disease",
        "disease_hpo_gene", "disease_hpo_observed",
        "disease_hpo_explicitly_absent", "disease_hpo_inheritance",
        "disease_mondo_exact", "disease_mondo_category",
    )
    for table in disease_tables:
        counts[table] = int(con.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
    if full_scope and any(counts[name] == 0 for name in disease_tables):
        fail(f"Full-scope disease output unexpectedly empty: {counts}")

    quarantine_names = {row[0] for row in con.execute("SHOW TABLES").fetchall()
                        if "quarantine" in row[0].lower()}
    if quarantine_names:
        fail(f"Quarantine tables entered public database: {sorted(quarantine_names)}")
    bad_absent = con.execute("""
        SELECT count(*) FROM disease_hpo_explicitly_absent
        WHERE phenotype_status <> 'explicitly_absent' AND qualifier <> 'NOT'
    """).fetchone()[0]
    bad_observed = con.execute("""
        SELECT count(*) FROM disease_hpo_observed
        WHERE phenotype_status <> 'observed' OR aspect = 'I' OR qualifier = 'NOT'
    """).fetchone()[0]
    bad_inheritance = con.execute(
        "SELECT count(*) FROM disease_hpo_inheritance WHERE aspect <> 'I'"
    ).fetchone()[0]
    if bad_absent or bad_observed or bad_inheritance:
        fail("HPO observed/absent/inheritance separation contract violated")
    noneligible = con.execute(f"""
        SELECT count(*) FROM disease_mondo_exact d
        WHERE d.mapping_basis = 'eligible exact MONDO xref' AND NOT EXISTS (
          SELECT 1 FROM read_parquet('{source(view_root, 'Disease/mondo_xref.parquet')}') x
          WHERE x.external_id = d.source_disease_id AND x.mondo_id = d.mondo_id
            AND lower(x.eligible_for_unique_merge) = 'true')
    """).fetchone()[0]
    if noneligible:
        fail(f"Non-eligible MONDO mappings entered public bridge ({noneligible:,})")
    return counts


def install_build(temp: Path, output_root: Path) -> None:
    names = ("interaction", "interaction_mutation", "memvar_m4.duckdb")
    backup = output_root / f".m4-backup-{uuid.uuid4().hex}"
    backup.mkdir()
    installed: list[str] = []
    moved_old: list[str] = []
    try:
        for name in names:
            destination = output_root / name
            if destination.exists():
                os.replace(destination, backup / name)
                moved_old.append(name)
        for name in names:
            os.replace(temp / name, output_root / name)
            installed.append(name)
    except OSError:
        for name in reversed(installed):
            destination = output_root / name
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()
        for name in moved_old:
            if (backup / name).exists():
                os.replace(backup / name, output_root / name)
        raise
    finally:
        if backup.exists():
            shutil.rmtree(backup)
    temp.rmdir()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    con: duckdb.DuckDBPyConnection | None = None
    temp: Path | None = None
    try:
        view_root, output_root = validate_paths(args.view_root, args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        accessions = sorted(set(value.strip().upper() for value in args.accession if value.strip()))
        temp = output_root / f".m4-build-{uuid.uuid4().hex}"
        temp.mkdir()
        con = duckdb.connect(str(temp / "memvar_m4.duckdb"))
        con.execute(f"SET threads={args.threads}")
        con.execute(f"SET temp_directory='{sql_path(temp / 'duckdb-tmp')}'")
        validate_sources(con, view_root)
        create_scope_and_bridge(con, view_root, accessions)
        build_biogrid(con, view_root, temp)
        build_intact(con, view_root, temp)
        build_mutation_effect(con, view_root, temp)
        build_interaction_summary(con, temp)
        build_disease(con, view_root)
        finalize_database(con, accessions)
        counts = validate_build(con, view_root, temp)
        scope = ",".join(accessions) if accessions else "all"
        con.close()
        con = None
        install_build(temp, output_root)
        temp = None
    except (RuntimeError, OSError, ValueError, duckdb.Error) as error:
        print(f"build_m4 failed: {error}", file=sys.stderr)
        return 1
    finally:
        if con is not None:
            con.close()
        if temp is not None and temp.exists():
            shutil.rmtree(temp)
    elapsed = time.monotonic() - started
    print(f"Built M4 scope: {scope}")
    for name, count in counts.items():
        print(f"{name}: {count:,}")
    print(f"elapsed_seconds: {elapsed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
