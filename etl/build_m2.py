#!/usr/bin/env python3
"""Build M2 sequence/site and protein-scoped variant data from immutable View.

The output consists of accession-bucketed ZSTD Parquet datasets plus a small
DuckDB summary store.  Use one or more ``--accession`` options for a staged
slice (for example P00533), or omit the option for all reviewed proteins.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid

import duckdb

from build_core import DEFAULT_OUTPUT_ROOT, DEFAULT_VIEW_ROOT, fail, path_is_within


WEBSITE_ROOT = Path(__file__).resolve().parents[1]
TRACK_MAP_PATH = WEBSITE_ROOT / "config" / "feature_track_map.json"

SOURCES: dict[str, set[str]] = {
    "Basic_info/protein_basic.parquet": {"uniprot_accession", "canonical_length"},
    "Basic_info/protein_sequence.parquet": {
        "uniprot_accession", "sequence_id", "is_canonical", "length", "sequence",
        "parent_canonical_sequence_version",
    },
    "Annotation/uniprot_feature.parquet": {
        "uniprot_accession", "sequence_version", "feature_category", "feature_type",
        "start_position", "end_position", "start_modifier", "end_modifier",
        "description", "feature_id", "evidence_json", "coordinate_basis",
    },
    "PTMs/uniprot_ptm_feature.parquet": {
        "uniprot_accession", "sequence_version", "feature_category", "feature_type",
        "start_position", "end_position", "start_modifier", "end_modifier",
        "description", "feature_id", "evidence_json", "coordinate_basis",
    },
    "Annotation/uniprot_covalent_structure.parquet": {
        "uniprot_accession", "sequence_version", "feature_category", "feature_type",
        "start_position", "end_position", "start_modifier", "end_modifier",
        "description", "feature_id", "evidence_json", "coordinate_basis",
    },
    "Annotation/pfam_domain_membrane.parquet": {
        "uniprot_accession", "pfam_accession", "pfam_id", "pfam_description",
        "pfam_type", "clan_id", "clan_name", "env_start", "env_end", "ali_start",
        "ali_end", "hmm_start", "hmm_end", "domain_i_evalue", "domain_score",
        "pfam_release",
    },
    "PTMs/dbptm_site_evidence.parquet": {
        "uniprot_accession", "sequence_version", "position", "residue", "ptm_type",
        "pmid", "source_evidence_count",
    },
    "Annotation/conservation_site.parquet": {
        "uniprot_accession", "sequence_version", "position", "residue", "consensus_aa",
        "wt_frequency", "entropy_conservation", "jsd_conservation", "gap_frequency",
        "occupancy", "neff_site", "neff_protein", "alignment_scope", "confidence",
    },
    "Variant/represent_variant.parquet": {
        "variant_key", "VARIANT_CLASS", "Existing_variation", "Consequence", "Feature",
        "IMPACT", "HGVSp", "Codons", "am_pathogenicity", "am_class",
        "uniprot_accession", "protein_source", "joint_ac", "joint_an",
        "joint_homozygote_count", "joint_hemizygote_count", "joint_AF", "exome_AF",
        "genome_AF", "database_source", "database_id", "chrom", "pos", "ref", "alt",
        "n_sources", "gene_symbol", "hgnc_id",
    },
    "Variant/isoform_view.parquet": {
        "variant_key", "uniprot_accession", "uniprot_isoform_id",
        "is_uniprot_canonical", "Consequence", "HGVSp", "Codons", "transcript_ids",
    },
    "Variant/clinvar_branch.parquet": {
        "variant_key", "ClinicalSignificance", "RCVaccession", "PhenotypeList",
        "PhenotypeIDs", "ReviewStatus", "OriginSimple", "mondo_ids",
        "disease_categories",
    },
    "Variant/cosmic_branch.parquet": {
        "variant_key", "GENOME_SCREEN_SAMPLE_COUNT", "mondo_ids", "disease_categories",
        "CGC_TIER", "ONC_TSG",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view-root", type=Path, default=DEFAULT_VIEW_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--accession", action="append", default=[],
        help="Build only this accession; repeat for a multi-protein staged build.",
    )
    parser.add_argument("--threads", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    return parser.parse_args()


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


def validate_sources(con: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    for rel, required in SOURCES.items():
        path = view_root / rel
        if not path.is_file():
            fail(f"Required source file is missing: {path}")
        actual = {r[0] for r in con.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]
        ).fetchall()}
        missing = sorted(required - actual)
        if missing:
            fail(f"{path} is missing required columns: {', '.join(missing)}")
        if rel == "Variant/cosmic_branch.parquet":
            types = {row[0]: row[1] for row in con.execute(
                "DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]
            ).fetchall()}
            expected = {
                "variant_key": "VARCHAR",
                "GENOME_SCREEN_SAMPLE_COUNT": "BIGINT",
                "mondo_ids": "VARCHAR",
                "disease_categories": "VARCHAR",
                "CGC_TIER": "INTEGER",
                "ONC_TSG": "VARCHAR",
            }
            mismatches = [
                f"{name}={types.get(name)} (expected {kind})"
                for name, kind in expected.items() if types.get(name) != kind
            ]
            if mismatches:
                fail(f"{path} has invalid COSMIC types: {', '.join(mismatches)}")


def bucket_sql(column: str = "uniprot_accession") -> str:
    # A deliberately simple, fixed polynomial hash.  Unlike Python/DuckDB hash(),
    # its result does not depend on a process seed or engine implementation.
    terms = [
        f"CAST(coalesce(unicode(nullif(substr({column}, {i}, 1), '')), 0) AS BIGINT) * {31 ** (10 - i)}"
        for i in range(1, 11)
    ]
    return f"CAST(mod({' + '.join(terms)}, 128) AS INTEGER)"


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def source(view_root: Path, rel: str) -> str:
    return sql_path(view_root / rel)


def cosmic_facts_sql(cosmic_path: str) -> str:
    """Select unique six-column source facts without merging distinct counts."""
    return f"""
        SELECT DISTINCT variant_key, GENOME_SCREEN_SAMPLE_COUNT, mondo_ids,
          disease_categories, CGC_TIER, ONC_TSG
        FROM read_parquet('{cosmic_path}')
    """


def accession_predicate(accessions: list[str], alias: str = "") -> str:
    if not accessions:
        return "TRUE"
    prefix = f"{alias}." if alias else ""
    values = ", ".join("'" + a.replace("'", "''") + "'" for a in accessions)
    return f"{prefix}uniprot_accession IN ({values})"


def copy_partitioned(con: duckdb.DuckDBPyConnection, query: str, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    con.execute(
        f"COPY ({query}) TO '{sql_path(target)}' "
        "(FORMAT PARQUET, PARTITION_BY (accession_bucket), COMPRESSION ZSTD, "
        "ROW_GROUP_SIZE 100000)"
    )


def create_scope(con: duckdb.DuckDBPyConnection, view_root: Path, accessions: list[str]) -> None:
    basic = source(view_root, "Basic_info/protein_basic.parquet")
    con.execute(f"CREATE TEMP TABLE protein_scope AS SELECT uniprot_accession, canonical_length FROM read_parquet('{basic}') WHERE {accession_predicate(accessions)}")
    if not con.execute("SELECT count(*) FROM protein_scope").fetchone()[0]:
        fail("No requested accession exists in protein_basic")
    if accessions:
        found = {r[0] for r in con.execute("SELECT uniprot_accession FROM protein_scope").fetchall()}
        missing = sorted(set(accessions) - found)
        if missing:
            fail(f"Unknown accession(s): {', '.join(missing)}")


def build_sequence(con: duckdb.DuckDBPyConnection, view_root: Path, root: Path, track_map: dict) -> None:
    mapping = track_map["category"]
    default = track_map["default"]
    cases = " ".join(
        f"WHEN feature_category = '{k.replace(chr(39), chr(39) * 2)}' THEN '{v.replace(chr(39), chr(39) * 2)}'"
        for k, v in mapping.items()
    )
    bucket = bucket_sql("f.uniprot_accession")
    general = source(view_root, "Annotation/uniprot_feature.parquet")
    ptm = source(view_root, "PTMs/uniprot_ptm_feature.parquet")
    feature_query = f"""
        SELECT f.*, CASE {cases} ELSE '{default}' END AS track_group,
               {bucket} AS accession_bucket
        FROM (
          SELECT * FROM read_parquet('{general}')
          UNION ALL BY NAME
          SELECT * FROM read_parquet('{ptm}')
        ) f JOIN protein_scope s USING (uniprot_accession)
        ORDER BY accession_bucket, f.uniprot_accession, start_position NULLS LAST,
                 end_position NULLS LAST, feature_type
    """
    copy_partitioned(con, feature_query, root / "sequence" / "feature_interval")

    datasets = {
        "covalent_pair": ("Annotation/uniprot_covalent_structure.parquet", "start_position NULLS LAST, end_position NULLS LAST"),
        "pfam_interval": ("Annotation/pfam_domain_membrane.parquet", "env_start NULLS LAST, env_end NULLS LAST"),
        "ptm_site": ("PTMs/dbptm_site_evidence.parquet", "position NULLS LAST, ptm_type"),
        "conservation_tile": ("Annotation/conservation_site.parquet", "position"),
    }
    for name, (rel, order) in datasets.items():
        path = source(view_root, rel)
        query = f"""
            SELECT d.*, {bucket_sql('d.uniprot_accession')} AS accession_bucket
            FROM read_parquet('{path}') d JOIN protein_scope s USING (uniprot_accession)
            ORDER BY accession_bucket, d.uniprot_accession, {order}
        """
        copy_partitioned(con, query, root / "sequence" / name)


def create_aa_map(con: duckdb.DuckDBPyConnection) -> None:
    aa = {
        "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
        "Gln": "Q", "Glu": "E", "Gly": "G", "His": "H", "Ile": "I",
        "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
        "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
        "Ter": "*", "*": "*",
    }
    con.execute("CREATE TEMP TABLE aa_map(aa3 VARCHAR, aa1 VARCHAR)")
    con.executemany("INSERT INTO aa_map VALUES (?, ?)", list(aa.items()))


def build_variants(con: duckdb.DuckDBPyConnection, view_root: Path, root: Path) -> None:
    iso = source(view_root, "Variant/isoform_view.parquet")
    rep = source(view_root, "Variant/represent_variant.parquet")
    seq = source(view_root, "Basic_info/protein_sequence.parquet")
    create_aa_map(con)
    con.execute(f"""
        CREATE TEMP TABLE effect_raw AS
        SELECT i.*,
          CASE lower(trim(i.is_uniprot_canonical))
            WHEN 'true' THEN true WHEN 'false' THEN false ELSE NULL END AS canonical_flag,
          regexp_extract(i.HGVSp, '^p\\.([A-Z][a-z]{{2}}|Ter|\\*)([0-9]+)', 1) AS start_aa3,
          try_cast(nullif(regexp_extract(i.HGVSp, '^p\\.([A-Z][a-z]{{2}}|Ter|\\*)([0-9]+)', 2), '') AS BIGINT) AS parsed_start,
          regexp_extract(i.HGVSp, '_([A-Z][a-z]{{2}}|Ter|\\*)([0-9]+)', 1) AS end_aa3,
          try_cast(nullif(regexp_extract(i.HGVSp, '_([A-Z][a-z]{{2}}|Ter|\\*)([0-9]+)', 2), '') AS BIGINT) AS parsed_end,
          regexp_extract(i.HGVSp, '^p\\.(?:[A-Z][a-z]{{2}}|Ter|\\*)[0-9]+(?:_(?:[A-Z][a-z]{{2}}|Ter|\\*)[0-9]+)?([A-Z][a-z]{{2}}|Ter|\\*|=)', 1) AS alt_aa3
        FROM read_parquet('{iso}') i JOIN protein_scope s USING (uniprot_accession)
    """)
    con.execute(f"""
        CREATE TEMP TABLE effect_parsed AS
        SELECT e.variant_key, e.uniprot_accession, e.uniprot_isoform_id,
          e.is_uniprot_canonical, e.canonical_flag,
          CASE WHEN e.canonical_flag THEN 'canonical'
               WHEN e.canonical_flag = false THEN 'isoform' ELSE NULL END AS effect_scope,
          e.Consequence, e.HGVSp, e.Codons, e.transcript_ids,
          e.parsed_start AS protein_start,
          coalesce(e.parsed_end, e.parsed_start) AS protein_end,
          a1.aa1 AS ref_aa,
          CASE WHEN e.alt_aa3 = '=' THEN a1.aa1 ELSE a3.aa1 END AS alt_aa,
          e.end_aa3, a2.aa1 AS end_ref_aa,
          s.length AS canonical_length, s.sequence AS canonical_sequence,
          r.uniprot_accession AS representative_accession, r.HGVSp AS representative_hgvsp
        FROM effect_raw e
        LEFT JOIN aa_map a1 ON e.start_aa3 = a1.aa3
        LEFT JOIN aa_map a2 ON e.end_aa3 = a2.aa3
        LEFT JOIN aa_map a3 ON e.alt_aa3 = a3.aa3
        LEFT JOIN read_parquet('{seq}') s
          ON e.uniprot_accession = s.uniprot_accession AND s.is_canonical = true
        LEFT JOIN read_parquet('{rep}') r USING (variant_key)
    """)
    con.execute("""
        CREATE TEMP TABLE variant_effect AS
        SELECT variant_key, uniprot_accession, uniprot_isoform_id,
          is_uniprot_canonical, canonical_flag, effect_scope, Consequence, HGVSp,
          Codons, transcript_ids, protein_start, protein_end, ref_aa, alt_aa,
          CASE
            WHEN HGVSp IS NULL OR trim(HGVSp) = '' THEN 'missing_hgvsp'
            WHEN protein_start IS NULL OR ref_aa IS NULL THEN 'unparseable_hgvsp'
            WHEN canonical_flag IS NULL THEN 'unknown_canonical_scope'
            WHEN canonical_flag = false THEN 'isoform_not_projected'
            WHEN protein_start < 1 OR protein_end < protein_start OR protein_end > canonical_length THEN 'out_of_bounds'
            WHEN substr(canonical_sequence, protein_start, 1) <> ref_aa THEN 'reference_mismatch'
            WHEN end_ref_aa IS NOT NULL AND substr(canonical_sequence, protein_end, 1) <> end_ref_aa THEN 'reference_mismatch'
            ELSE 'drawable'
          END AS site_parse_status,
          CASE
            WHEN canonical_flag = true
             AND protein_start BETWEEN 1 AND canonical_length
             AND protein_end BETWEEN protein_start AND canonical_length
             AND substr(canonical_sequence, protein_start, 1) = ref_aa
             AND (end_ref_aa IS NULL OR substr(canonical_sequence, protein_end, 1) = end_ref_aa)
            THEN true ELSE false END AS is_drawable,
          (uniprot_accession IS NOT DISTINCT FROM representative_accession
           AND HGVSp IS NOT DISTINCT FROM representative_hgvsp) AS is_representative_effect
        FROM effect_parsed
    """)
    effect_query = f"""
        SELECT e.*, {bucket_sql('e.uniprot_accession')} AS accession_bucket
        FROM variant_effect e
        ORDER BY accession_bucket, uniprot_accession,
          CASE effect_scope WHEN 'canonical' THEN 0 WHEN 'isoform' THEN 1 ELSE 2 END,
          protein_start NULLS LAST, variant_key, HGVSp
    """
    copy_partitioned(con, effect_query, root / "variant" / "effect")

    con.execute("CREATE TEMP TABLE variant_membership AS SELECT DISTINCT variant_key, uniprot_accession FROM variant_effect")
    core_query = f"""
        SELECT m.uniprot_accession AS page_accession, r.*,
          {bucket_sql('m.uniprot_accession')} AS accession_bucket
        FROM variant_membership m JOIN read_parquet('{rep}') r USING (variant_key)
        ORDER BY accession_bucket, page_accession, variant_key
    """
    copy_partitioned(con, core_query, root / "variant" / "core")

    branches = {"clinvar": "Variant/clinvar_branch.parquet"}
    for name, rel in branches.items():
        path = source(view_root, rel)
        query = f"""
            SELECT m.uniprot_accession AS page_accession, b.*,
              {bucket_sql('m.uniprot_accession')} AS accession_bucket
            FROM variant_membership m JOIN read_parquet('{path}') b USING (variant_key)
            ORDER BY accession_bucket, page_accession, variant_key
        """
        copy_partitioned(con, query, root / "variant" / "source" / name)

    # The physical COSMIC source contains extensive exact row multiplication.
    # Its six columns describe one source fact; deduplicate that complete fact
    # before copying it to each protein membership.  Different sample-count
    # facts for the same variant remain separate and are never summed.
    cosmic = source(view_root, "Variant/cosmic_branch.parquet")
    invalid_tier = con.execute(f"""
        SELECT count(*) FROM read_parquet('{cosmic}')
        WHERE CGC_TIER IS NOT NULL AND CGC_TIER NOT IN (1, 2)
    """).fetchone()[0]
    if invalid_tier:
        fail("COSMIC CGC_TIER contains values other than 1, 2, or NULL")
    invalid_role = con.execute(f"""
        SELECT count(*)
        FROM read_parquet('{cosmic}'),
          unnest(string_split(coalesce(ONC_TSG, ''), ',')) AS roles(role)
        WHERE trim(role) <> ''
          AND lower(trim(role)) NOT IN ('oncogene', 'tsg', 'fusion')
    """).fetchone()[0]
    if invalid_role:
        fail("COSMIC ONC_TSG contains an unknown CGC role")
    cosmic_query = f"""
        WITH cosmic_facts AS (
          {cosmic_facts_sql(cosmic)}
        )
        SELECT m.uniprot_accession AS page_accession, b.*,
          {bucket_sql('m.uniprot_accession')} AS accession_bucket
        FROM variant_membership m JOIN cosmic_facts b USING (variant_key)
        ORDER BY accession_bucket, page_accession, variant_key,
          GENOME_SCREEN_SAMPLE_COUNT NULLS LAST
    """
    copy_partitioned(con, cosmic_query, root / "variant" / "source" / "cosmic")


def parquet_count(con: duckdb.DuckDBPyConnection, path: Path) -> int:
    glob = sql_path(path / "**" / "*.parquet")
    return int(con.execute(f"SELECT count(*) FROM read_parquet('{glob}', hive_partitioning=true)").fetchone()[0])


def validate_build(con: duckdb.DuckDBPyConnection, root: Path, accessions: list[str]) -> dict[str, int]:
    paths = {
        "feature_interval": root / "sequence" / "feature_interval",
        "covalent_pair": root / "sequence" / "covalent_pair",
        "pfam_interval": root / "sequence" / "pfam_interval",
        "ptm_site": root / "sequence" / "ptm_site",
        "conservation_tile": root / "sequence" / "conservation_tile",
        "variant_effect": root / "variant" / "effect",
        "variant_core": root / "variant" / "core",
        "variant_clinvar": root / "variant" / "source" / "clinvar",
        "variant_cosmic": root / "variant" / "source" / "cosmic",
    }
    counts = {name: parquet_count(con, path) for name, path in paths.items()}
    if counts["variant_effect"] == 0 or counts["variant_core"] == 0:
        fail("M2 variant outputs are unexpectedly empty")
    effects = sql_path(paths["variant_effect"] / "**" / "*.parquet")
    invalid_drawable = con.execute(f"""
        SELECT count(*) FROM read_parquet('{effects}', hive_partitioning=true)
        WHERE is_drawable AND site_parse_status <> 'drawable'
    """).fetchone()[0]
    if invalid_drawable:
        fail("Drawable effects include a non-drawable parse status")
    isoform_drawable = con.execute(f"""
        SELECT count(*) FROM read_parquet('{effects}', hive_partitioning=true)
        WHERE is_drawable AND effect_scope IS DISTINCT FROM 'canonical'
    """).fetchone()[0]
    if isoform_drawable:
        fail("Isoform or unknown-scope effects were projected onto canonical coordinates")
    unknown_collapsed = con.execute(f"""
        SELECT count(*) FROM read_parquet('{effects}', hive_partitioning=true)
        WHERE canonical_flag IS NULL AND effect_scope IS NOT NULL
    """).fetchone()[0]
    if unknown_collapsed:
        fail("Unknown canonical flags were collapsed into isoform scope")
    return counts


def build_summary_db(con: duckdb.DuckDBPyConnection, root: Path, scope: str) -> None:
    db = root / "memvar_m2.duckdb"
    out = duckdb.connect(str(db))
    try:
        effect_glob = sql_path(root / "variant" / "effect" / "**" / "*.parquet")
        out.execute(f"""
            CREATE TABLE build_scope AS SELECT '{scope.replace(chr(39), chr(39) * 2)}'::VARCHAR AS scope;
            CREATE TABLE variant_summary AS
            SELECT uniprot_accession,
              count(DISTINCT variant_key) AS variant_count,
              count(*) AS effect_count,
              count(*) FILTER (WHERE effect_scope = 'canonical') AS canonical_effect_count,
              count(*) FILTER (WHERE effect_scope = 'isoform') AS isoform_effect_count,
              count(*) FILTER (WHERE effect_scope IS NULL) AS unknown_scope_effect_count,
              count(*) FILTER (WHERE is_drawable) AS drawable_effect_count
            FROM read_parquet('{effect_glob}', hive_partitioning=true)
            GROUP BY uniprot_accession;
        """)
        out.execute("CHECKPOINT")
    finally:
        out.close()


def install_build(temp: Path, output_root: Path) -> None:
    targets = ["sequence", "variant", "memvar_m2.duckdb"]
    for name in targets:
        src = temp / name
        dst = output_root / name
        if dst.is_dir():
            shutil.rmtree(dst)
        elif dst.exists():
            dst.unlink()
        os.replace(src, dst)
    temp.rmdir()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    con: duckdb.DuckDBPyConnection | None = None
    temp: Path | None = None
    try:
        view_root, output_root = validate_paths(args.view_root, args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        accessions = sorted(set(a.strip().upper() for a in args.accession if a.strip()))
        temp = output_root / f".m2-build-{uuid.uuid4().hex}"
        temp.mkdir()
        con = duckdb.connect()
        con.execute(f"SET threads={args.threads}")
        validate_sources(con, view_root)
        if not TRACK_MAP_PATH.is_file():
            fail(f"Missing website track mapping: {TRACK_MAP_PATH}")
        track_map = json.loads(TRACK_MAP_PATH.read_text())
        create_scope(con, view_root, accessions)
        build_sequence(con, view_root, temp, track_map)
        build_variants(con, view_root, temp)
        counts = validate_build(con, temp, accessions)
        scope = ",".join(accessions) if accessions else "all"
        build_summary_db(con, temp, scope)
        install_build(temp, output_root)
        temp = None
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError, duckdb.Error) as error:
        print(f"build_m2 failed: {error}", file=sys.stderr)
        return 1
    finally:
        if con is not None:
            con.close()
        if temp is not None and temp.exists():
            shutil.rmtree(temp)
    elapsed = time.monotonic() - started
    print(f"Built M2 scope: {scope}")
    for name, count in counts.items():
        print(f"{name}: {count:,}")
    print(f"elapsed_seconds: {elapsed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
