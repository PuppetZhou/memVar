#!/usr/bin/env python3
"""Build bounded AlphaGenome display assets for the memVar protein portal.

The multi-terabyte AlphaGenome archive and View are immutable inputs.  The
builder creates a complete protein/gene/tile catalog plus display-ready signal
pyramids for either a bounded pilot or the full archive.  Runtime API requests
never read the source HDF5 files.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import uuid

import duckdb
import h5py
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


WEBSITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WEBSITE_ROOT.parent
VIEW_ROOT = PROJECT_ROOT / "View"
GENERATED_ROOT = WEBSITE_ROOT / "data" / "generated"
DEFAULT_SOURCE = Path("/media/xuyzh/Newsmy/alpha-predict/alphagenome_1mb_by_gene")
DEFAULT_PROTEINS = VIEW_ROOT / "Basic_info" / "protein_basic.parquet"
DEFAULT_BRIDGE = VIEW_ROOT / "Basic_info" / "gene_identifier_bridge.parquet"
DEFAULT_OUTPUT = GENERATED_ROOT / "alphagenome"

GENE_RE = re.compile(r"ENSG[0-9]{11}")
TILE_RE = re.compile(r"tile_[0-9]{3}")
ACCESSION_RE = re.compile(r"[A-Z0-9]+")
LEVELS = (256, 1024, 4096)
JUNCTION_LIMIT = 200
CONTACT_SIZE = 128
SOURCE_LABEL = "AlphaGenome"
GENOME_BUILD = "GRCh38"
PREDICTION_KIND = "reference_sequence_tracks"

DENSE_MODALITIES = (
    "rna_seq", "cage", "procap", "atac", "chip_histone",
    "splice_sites", "splice_site_usage",
)
ALL_MODALITIES = DENSE_MODALITIES + ("splice_junctions", "contact_maps")
DISPLAY_UNITS = {
    "rna_seq": "normalized read signal",
    "cage": "normalized read signal",
    "procap": "normalized read signal",
    "atac": "normalized insertion signal",
    "chip_histone": "normalized read signal",
    "splice_sites": "class probability",
    "splice_site_usage": "usage fraction",
    "splice_junctions": "predicted junction signal",
    "contact_maps": "predicted contact frequency",
}


class BuildError(RuntimeError):
    """A source or generated-data contract violation."""


def fail(message: str) -> None:
    raise BuildError(message)


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_paths(source: Path, proteins: Path, bridge: Path, output: Path) -> None:
    for path, label in ((source, "AlphaGenome source"), (proteins, "protein registry"), (bridge, "gene bridge")):
        if not path.exists():
            fail(f"{label} does not exist: {path}")
    if not source.is_dir() or not (source / "genes").is_dir() or not (source / "_metadata").is_dir():
        fail(f"AlphaGenome source layout is invalid: {source}")
    if not path_is_within(output, GENERATED_ROOT.resolve()):
        fail(f"Output must remain inside website/data/generated: {output}")
    if path_is_within(output, source) or path_is_within(source, output):
        fail("Output and AlphaGenome source must not overlap")
    if path_is_within(output, VIEW_ROOT.resolve()) or path_is_within(VIEW_ROOT.resolve(), output):
        fail("Output and View must not overlap")


def validate_resume_root(resume_root: Path, output: Path) -> Path:
    resume_root = resume_root.resolve()
    if resume_root.is_symlink() or not resume_root.is_dir():
        fail(f"Resume root is not an existing directory: {resume_root}")
    if resume_root.parent != output.parent or not resume_root.name.startswith(f"{output.name}.tmp-"):
        fail(f"Resume root must be an AlphaGenome staging directory beside {output}")
    if not path_is_within(resume_root, GENERATED_ROOT.resolve()):
        fail(f"Resume root must remain inside website/data/generated: {resume_root}")
    return resume_root


def json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError(f"Cannot read JSON manifest: {path}") from error
    if not isinstance(value, dict):
        fail(f"Manifest is not an object: {path}")
    return value


def scalar(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    return value


def load_tracks(source: Path) -> list[dict[str, object]]:
    tracks: list[dict[str, object]] = []
    for modality in ALL_MODALITIES:
        metadata_path = source / "_metadata" / f"{modality}.parquet"
        if not metadata_path.is_file():
            fail(f"Missing AlphaGenome track metadata: {metadata_path}")
        rows = pq.read_table(metadata_path).to_pylist()
        if not rows:
            fail(f"AlphaGenome track metadata is empty: {metadata_path}")
        for index, raw in enumerate(rows):
            tracks.append({
                "track_id": f"{modality}:{index:03d}",
                "modality": modality,
                "source_column_index": index,
                "name": raw.get("name"),
                "assay_title": raw.get("Assay title"),
                "ontology_curie": raw.get("ontology_curie"),
                "biosample_name": raw.get("biosample_name"),
                "biosample_type": raw.get("biosample_type"),
                "biosample_life_stage": raw.get("biosample_life_stage"),
                "gtex_tissue": raw.get("gtex_tissue"),
                "strand": raw.get("strand"),
                "histone_mark": raw.get("histone_mark"),
                "data_source": raw.get("data_source"),
                "display_unit": DISPLAY_UNITS[modality],
            })
    return tracks


def discover_genes(source: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    genes: list[dict[str, object]] = []
    tiles: list[dict[str, object]] = []
    seen_genes: set[str] = set()
    seen_tiles: set[tuple[str, str]] = set()
    for gene_dir in sorted((source / "genes").iterdir()):
        if not gene_dir.is_dir() or not GENE_RE.fullmatch(gene_dir.name):
            continue
        manifest_path = gene_dir / "manifest.json"
        success_path = gene_dir / "_SUCCESS"
        if not manifest_path.is_file() or not success_path.is_file():
            fail(f"Incomplete AlphaGenome gene directory: {gene_dir}")
        manifest = json_object(manifest_path)
        gene_id = str(manifest.get("ensembl_gene_id", ""))
        if gene_id != gene_dir.name or gene_id in seen_genes:
            fail(f"Invalid or duplicate AlphaGenome gene identity: {gene_dir}")
        manifest_tiles = manifest.get("tiles")
        if not isinstance(manifest_tiles, list) or int(manifest.get("num_tiles", -1)) != len(manifest_tiles):
            fail(f"AlphaGenome tile count mismatch: {gene_id}")
        seen_genes.add(gene_id)
        genes.append({
            "ensembl_gene_id": gene_id,
            "gene_symbol": manifest.get("gene_name"),
            "hgnc_id": manifest.get("hgnc_id"),
            "chromosome": manifest.get("chromosome"),
            "gene_start_1based": manifest.get("gene_start_1based"),
            "gene_end_1based_inclusive": manifest.get("gene_end_1based_inclusive"),
            "gene_strand": manifest.get("gene_strand"),
            "num_tiles": len(manifest_tiles),
        })
        for raw_tile in manifest_tiles:
            if not isinstance(raw_tile, dict):
                fail(f"Invalid tile manifest row: {gene_id}")
            tile_id = str(raw_tile.get("tile_id", ""))
            key = gene_id, tile_id
            tile_dir = gene_dir / "tiles" / tile_id
            if not TILE_RE.fullmatch(tile_id) or key in seen_tiles:
                fail(f"Invalid or duplicate tile identity: {gene_id}/{tile_id}")
            required = (tile_dir / "manifest.json", tile_dir / "regular_tracks.h5", tile_dir / "splice_junctions.parquet", tile_dir / "_SUCCESS")
            if any(not path.is_file() for path in required):
                fail(f"Incomplete AlphaGenome tile: {gene_id}/{tile_id}")
            if int(raw_tile.get("window_width", -1)) != 1_048_576:
                fail(f"Unexpected model window width: {gene_id}/{tile_id}")
            seen_tiles.add(key)
            tiles.append({
                "ensembl_gene_id": gene_id,
                "tile_id": tile_id,
                "tile_index": raw_tile.get("tile_index"),
                "chromosome": raw_tile.get("chromosome"),
                "window_start_0based": raw_tile.get("window_start_0based"),
                "window_end_0based": raw_tile.get("window_end_0based"),
                "core_start_0based": raw_tile.get("core_start_0based"),
                "core_end_0based": raw_tile.get("core_end_0based"),
                "window_anchor": raw_tile.get("window_anchor"),
                "window_width": raw_tile.get("window_width"),
            })
    if not genes or not tiles:
        fail("AlphaGenome source contains no complete genes or tiles")
    return genes, tiles


def load_protein_mappings(proteins: Path, bridge: Path) -> tuple[list[tuple[str, str | None]], dict[str, list[str]]]:
    connection = duckdb.connect()
    try:
        protein_rows = connection.execute(
            "SELECT uniprot_accession, gene_symbol FROM read_parquet(?) ORDER BY 1", [str(proteins)]
        ).fetchall()
        bridge_rows = connection.execute(
            """
            SELECT DISTINCT uniprot_accession, identifier_base
            FROM read_parquet(?)
            WHERE identifier_database = 'Ensembl' AND identifier_base IS NOT NULL
            ORDER BY 1, 2
            """,
            [str(bridge)],
        ).fetchall()
    finally:
        connection.close()
    mapping: dict[str, list[str]] = defaultdict(list)
    for accession, gene_id in bridge_rows:
        if isinstance(gene_id, str) and GENE_RE.fullmatch(gene_id):
            mapping[str(accession)].append(gene_id)
    return [(str(accession), gene_symbol) for accession, gene_symbol in protein_rows], dict(mapping)


def select_pilot_genes(
    genes: list[dict[str, object]],
    protein_rows: list[tuple[str, str | None]],
    mapping: dict[str, list[str]],
    tile_limit: int,
    explicit_accessions: list[str],
) -> set[str]:
    gene_by_id = {str(row["ensembl_gene_id"]): row for row in genes}
    predicted = set(gene_by_id)
    selected: list[str] = []

    def add(gene_id: str) -> None:
        if gene_id in predicted and gene_id not in selected:
            selected.append(gene_id)

    for accession in explicit_accessions:
        for gene_id in mapping.get(accession.upper(), []):
            add(gene_id)

    # Ensure the pilot exercises multi-tile, negative-strand, and one-to-many mapping.
    for row in sorted(genes, key=lambda item: (-int(item["num_tiles"]), str(item["ensembl_gene_id"]))):
        if int(row["num_tiles"]) > 1:
            add(str(row["ensembl_gene_id"]))
            break
    for row in genes:
        if row["gene_strand"] == "-":
            add(str(row["ensembl_gene_id"]))
            break
    for accession, _ in protein_rows:
        eligible = [gene_id for gene_id in mapping.get(accession, []) if gene_id in predicted]
        if len(eligible) > 1:
            for gene_id in eligible:
                add(gene_id)
            break

    used_tiles = sum(int(gene_by_id[gene_id]["num_tiles"]) for gene_id in selected)
    for gene_id in sorted(predicted):
        if used_tiles >= tile_limit:
            break
        if gene_id in selected:
            continue
        count = int(gene_by_id[gene_id]["num_tiles"])
        if used_tiles + count <= tile_limit:
            add(gene_id)
            used_tiles += count
    return set(selected)


def aggregate_dataset(dataset: h5py.Dataset, bins: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    length, track_count = dataset.shape
    if length % bins:
        fail(f"Dense track length {length} is not divisible by {bins}")
    width = length // bins
    means = np.empty((bins, track_count), dtype=np.float32)
    maxima = np.empty((bins, track_count), dtype=np.float32)
    bins_per_read = max(1, min(64, bins))
    for first_bin in range(0, bins, bins_per_read):
        last_bin = min(bins, first_bin + bins_per_read)
        raw = np.asarray(dataset[first_bin * width:last_bin * width, :], dtype=np.float32)
        shaped = raw.reshape(last_bin - first_bin, width, track_count)
        means[first_bin:last_bin] = shaped.mean(axis=1)
        maxima[first_bin:last_bin] = shaped.max(axis=1)
    return means, maxima


def coarsen(values: np.ndarray, bins: int, operation: str) -> np.ndarray:
    if values.shape[0] % bins:
        fail(f"Pyramid level {values.shape[0]} is not divisible by {bins}")
    shaped = values.reshape(bins, values.shape[0] // bins, values.shape[1])
    return shaped.mean(axis=1) if operation == "mean" else shaped.max(axis=1)


def half_bytes(values: np.ndarray) -> bytes:
    return np.asarray(values, dtype="<f2").tobytes(order="C")


SIGNAL_SCHEMA = pa.schema([
    ("track_id", pa.string()), ("modality", pa.string()), ("level_bins", pa.int32()),
    ("window_start_0based", pa.int64()), ("window_end_0based", pa.int64()),
    ("source_resolution_bp", pa.int32()), ("value_count", pa.int32()),
    ("mean_float16_le", pa.binary()), ("max_float16_le", pa.binary()),
])


def build_signal_bundle(
    h5_path: Path,
    tile: dict[str, object],
    tracks_by_modality: dict[str, list[dict[str, object]]],
    output: Path,
) -> int:
    rows: list[dict[str, object]] = []
    with h5py.File(h5_path, "r") as handle:
        for modality in DENSE_MODALITIES:
            if modality not in handle or "values" not in handle[modality]:
                fail(f"Missing HDF5 modality {modality}: {h5_path}")
            dataset = handle[f"{modality}/values"]
            expected_tracks = tracks_by_modality[modality]
            if dataset.ndim != 2 or dataset.shape[1] != len(expected_tracks):
                fail(f"HDF5/metadata shape mismatch for {modality}: {h5_path}")
            resolution = int(handle[modality].attrs["resolution"])
            detail_mean, detail_max = aggregate_dataset(dataset)
            for level in LEVELS:
                mean_values = detail_mean if level == 4096 else coarsen(detail_mean, level, "mean")
                max_values = detail_max if level == 4096 else coarsen(detail_max, level, "max")
                for index, track in enumerate(expected_tracks):
                    rows.append({
                        "track_id": track["track_id"], "modality": modality, "level_bins": level,
                        "window_start_0based": tile["window_start_0based"],
                        "window_end_0based": tile["window_end_0based"],
                        "source_resolution_bp": resolution, "value_count": level,
                        "mean_float16_le": half_bytes(mean_values[:, index]),
                        "max_float16_le": half_bytes(max_values[:, index]),
                    })
    output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=SIGNAL_SCHEMA), output, compression="zstd")
    return len(rows)


CONTACT_SCHEMA = pa.schema([
    ("track_id", pa.string()), ("matrix_size", pa.int32()),
    ("window_start_0based", pa.int64()), ("window_end_0based", pa.int64()),
    ("source_resolution_bp", pa.int32()), ("mean_float16_le", pa.binary()),
])


def build_contact_bundle(
    h5_path: Path,
    tile: dict[str, object],
    tracks: list[dict[str, object]],
    output: Path,
) -> int:
    with h5py.File(h5_path, "r") as handle:
        if "contact_maps/values" not in handle:
            fail(f"Missing contact map dataset: {h5_path}")
        dataset = handle["contact_maps/values"]
        if dataset.shape[:2] != (512, 512) or dataset.shape[2] != len(tracks):
            fail(f"Contact map/metadata shape mismatch: {h5_path}")
        raw = np.asarray(dataset[:, :, :], dtype=np.float32)
        reduced = raw.reshape(CONTACT_SIZE, 4, CONTACT_SIZE, 4, len(tracks)).mean(axis=(1, 3))
        resolution = int(handle["contact_maps"].attrs["resolution"])
    rows = [{
        "track_id": track["track_id"], "matrix_size": CONTACT_SIZE,
        "window_start_0based": tile["window_start_0based"],
        "window_end_0based": tile["window_end_0based"],
        "source_resolution_bp": resolution,
        "mean_float16_le": half_bytes(reduced[:, :, index]),
    } for index, track in enumerate(tracks)]
    output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=CONTACT_SCHEMA), output, compression="zstd")
    return len(rows)


JUNCTION_SCHEMA = pa.schema([
    ("track_id", pa.string()), ("rank", pa.int32()), ("chromosome", pa.string()),
    ("start_0based", pa.int64()), ("end_0based", pa.int64()), ("strand", pa.string()),
    ("value", pa.float32()),
])


def parquet_row_count(path: Path, schema: pa.Schema, expected_rows: int | None = None) -> int | None:
    """Return a completed bundle's row count without reading its data pages."""
    try:
        parquet = pq.ParquetFile(path)
        if not parquet.schema_arrow.equals(schema, check_metadata=False):
            return None
        rows = parquet.metadata.num_rows
    except (OSError, pa.ArrowException):
        return None
    if expected_rows is not None and rows != expected_rows:
        return None
    return rows


def resume_bundle_counts(
    root: Path,
    signal_relative_path: Path,
    junction_relative_path: Path,
    contact_relative_path: Path,
    *,
    expected_signal_rows: int,
    expected_contact_rows: int,
) -> tuple[int, int, int] | None:
    signal_rows = parquet_row_count(root / signal_relative_path, SIGNAL_SCHEMA, expected_signal_rows)
    junction_rows = parquet_row_count(root / junction_relative_path, JUNCTION_SCHEMA)
    contact_rows = parquet_row_count(root / contact_relative_path, CONTACT_SCHEMA, expected_contact_rows)
    if signal_rows is None or junction_rows is None or contact_rows is None:
        return None
    return signal_rows, junction_rows, contact_rows


def build_junction_bundle(source_path: Path, tracks: list[dict[str, object]], output: Path) -> int:
    columns = ["chromosome", "start", "end", "strand"] + [f"track_{index:03d}" for index in range(len(tracks))]
    table = pq.read_table(source_path, columns=columns)
    base = {name: table.column(name).to_pylist() for name in columns[:4]}
    rows: list[dict[str, object]] = []
    for index, track in enumerate(tracks):
        values = np.asarray(table.column(f"track_{index:03d}").to_numpy(), dtype=np.float32)
        eligible = np.flatnonzero(np.isfinite(values) & (values > 0))
        if eligible.size > JUNCTION_LIMIT:
            chosen = eligible[np.argpartition(values[eligible], -JUNCTION_LIMIT)[-JUNCTION_LIMIT:]]
        else:
            chosen = eligible
        ordered = chosen[np.argsort(-values[chosen], kind="stable")]
        for rank, row_index in enumerate(ordered, 1):
            rows.append({
                "track_id": track["track_id"], "rank": rank,
                "chromosome": base["chromosome"][row_index],
                "start_0based": base["start"][row_index], "end_0based": base["end"][row_index],
                "strand": base["strand"][row_index], "value": float(values[row_index]),
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=JUNCTION_SCHEMA), output, compression="zstd")
    return len(rows)


def create_catalog(
    path: Path,
    genes: list[dict[str, object]],
    tiles: list[dict[str, object]],
    tracks: list[dict[str, object]],
    coverage: list[dict[str, object]],
    prepared: list[dict[str, object]],
) -> None:
    connection = duckdb.connect(str(path))
    try:
        for table_name, rows in (("gene", genes), ("tile", tiles), ("track", tracks), ("protein_gene_coverage", coverage), ("prepared_tile", prepared)):
            arrow = pa.Table.from_pylist(rows)
            connection.register(f"_{table_name}", arrow)
            connection.execute(f"CREATE TABLE {table_name} AS SELECT * FROM _{table_name}")
            connection.unregister(f"_{table_name}")
        connection.execute("CREATE INDEX coverage_accession ON protein_gene_coverage(uniprot_accession)")
        connection.execute("CREATE INDEX tile_gene ON tile(ensembl_gene_id, tile_id)")
        connection.execute("CREATE INDEX track_identity ON track(track_id)")
        connection.execute("CREATE UNIQUE INDEX prepared_identity ON prepared_tile(ensembl_gene_id, tile_id)")
        connection.execute("CHECKPOINT")
    finally:
        connection.close()


def build(
    source: Path,
    proteins: Path,
    bridge: Path,
    output: Path,
    *,
    all_genes: bool,
    pilot_tiles: int,
    accessions: list[str],
    resume_root: Path | None = None,
) -> None:
    source, proteins, bridge, output = (path.resolve() for path in (source, proteins, bridge, output))
    validate_paths(source, proteins, bridge, output)
    tracks = load_tracks(source)
    genes, tiles = discover_genes(source)
    protein_rows, mapping = load_protein_mappings(proteins, bridge)
    predicted = {str(row["ensembl_gene_id"]) for row in genes}
    selected_genes = predicted if all_genes else select_pilot_genes(genes, protein_rows, mapping, pilot_tiles, accessions)

    if resume_root is not None and not all_genes:
        fail("--resume-root requires --all so a partial catalog cannot be published")
    temporary = validate_resume_root(resume_root, output) if resume_root is not None else output.with_name(f"{output.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}")
    backup = output.with_name(f"{output.name}.old-{uuid.uuid4().hex}")
    temporary.mkdir(parents=True, exist_ok=resume_root is not None)
    tracks_by_modality: dict[str, list[dict[str, object]]] = defaultdict(list)
    for track in tracks:
        tracks_by_modality[str(track["modality"])].append(track)
    expected_signal_rows = sum(len(tracks_by_modality[modality]) for modality in DENSE_MODALITIES) * len(LEVELS)
    expected_contact_rows = len(tracks_by_modality["contact_maps"])
    target_tile_count = sum(1 for tile in tiles if str(tile["ensembl_gene_id"]) in selected_genes)

    prepared: list[dict[str, object]] = []
    resumed_tiles = 0
    rebuilt_tiles = 0
    print(f"AlphaGenome build target: {target_tile_count:,} tiles; staging: {temporary}", flush=True)
    try:
        for tile in tiles:
            gene_id, tile_id = str(tile["ensembl_gene_id"]), str(tile["tile_id"])
            if gene_id not in selected_genes:
                continue
            source_tile = source / "genes" / gene_id / "tiles" / tile_id
            relative = Path(gene_id) / tile_id
            signal_rel = Path("tracks") / relative.with_suffix(".parquet")
            junction_rel = Path("junctions") / relative.with_suffix(".parquet")
            contact_rel = Path("contacts") / relative.with_suffix(".parquet")
            existing = resume_bundle_counts(
                temporary, signal_rel, junction_rel, contact_rel,
                expected_signal_rows=expected_signal_rows,
                expected_contact_rows=expected_contact_rows,
            ) if resume_root is not None else None
            if existing is not None:
                signal_rows, junction_rows, contact_rows = existing
                resumed_tiles += 1
            else:
                for partial in (temporary / signal_rel, temporary / junction_rel, temporary / contact_rel):
                    partial.unlink(missing_ok=True)
                signal_rows = build_signal_bundle(source_tile / "regular_tracks.h5", tile, tracks_by_modality, temporary / signal_rel)
                junction_rows = build_junction_bundle(source_tile / "splice_junctions.parquet", tracks_by_modality["splice_junctions"], temporary / junction_rel)
                contact_rows = build_contact_bundle(source_tile / "regular_tracks.h5", tile, tracks_by_modality["contact_maps"], temporary / contact_rel)
                rebuilt_tiles += 1
            prepared.append({
                "ensembl_gene_id": gene_id, "tile_id": tile_id,
                "signal_relative_path": signal_rel.as_posix(),
                "junction_relative_path": junction_rel.as_posix(),
                "contact_relative_path": contact_rel.as_posix(),
                "signal_row_count": signal_rows, "junction_row_count": junction_rows,
                "contact_row_count": contact_rows,
            })
            if len(prepared) % 50 == 0 or len(prepared) == target_tile_count:
                print(
                    f"AlphaGenome progress: {len(prepared):,}/{target_tile_count:,} "
                    f"({resumed_tiles:,} resumed; {rebuilt_tiles:,} built this run)",
                    flush=True,
                )

        prepared_genes = {str(row["ensembl_gene_id"]) for row in prepared}
        coverage: list[dict[str, object]] = []
        for accession, protein_symbol in protein_rows:
            ensembl_ids = mapping.get(accession, [])
            eligible = [gene_id for gene_id in ensembl_ids if gene_id in predicted]
            if eligible:
                status = "exact" if len(eligible) == 1 else "ambiguous"
                for gene_id in eligible:
                    coverage.append({
                        "uniprot_accession": accession, "protein_gene_symbol": protein_symbol,
                        "ensembl_gene_id": gene_id, "mapping_status": status,
                        "mapping_count": len(eligible), "has_prediction": True,
                        "display_ready": gene_id in prepared_genes,
                    })
            elif ensembl_ids:
                for gene_id in ensembl_ids:
                    coverage.append({
                        "uniprot_accession": accession, "protein_gene_symbol": protein_symbol,
                        "ensembl_gene_id": gene_id, "mapping_status": "no_prediction",
                        "mapping_count": len(ensembl_ids), "has_prediction": False,
                        "display_ready": False,
                    })
            else:
                coverage.append({
                    "uniprot_accession": accession, "protein_gene_symbol": protein_symbol,
                    "ensembl_gene_id": None, "mapping_status": "no_ensembl",
                    "mapping_count": 0, "has_prediction": False, "display_ready": False,
                })

        catalog = temporary / "alphagenome_catalog.duckdb"
        catalog.unlink(missing_ok=True)
        catalog.with_suffix(f"{catalog.suffix}.wal").unlink(missing_ok=True)
        create_catalog(catalog, genes, tiles, tracks, coverage, prepared)
        manifest = {
            "schema_version": 1,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source": SOURCE_LABEL,
            "genome_build": GENOME_BUILD,
            "prediction_kind": PREDICTION_KIND,
            "local_output_subset": True,
            "missing_official_modalities": ["dnase", "chip_tf"],
            "pyramid_bins": list(LEVELS),
            "junction_limit_per_track": JUNCTION_LIMIT,
            "contact_matrix_size": CONTACT_SIZE,
            "gene_count": len(genes), "tile_count": len(tiles),
            "protein_count": len(protein_rows), "prepared_gene_count": len(prepared_genes),
            "prepared_tile_count": len(prepared), "full_build": all_genes,
        }
        (temporary / "build_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

        replaced = False
        try:
            if output.exists():
                os.replace(output, backup)
                replaced = True
            os.replace(temporary, output)
            if replaced:
                shutil.rmtree(backup)
        except Exception:
            if replaced and not output.exists() and backup.exists():
                os.replace(backup, output)
            raise
    except Exception:
        print(f"AlphaGenome staging preserved for resume: {temporary}", flush=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--protein-basic", type=Path, default=DEFAULT_PROTEINS)
    parser.add_argument("--gene-bridge", type=Path, default=DEFAULT_BRIDGE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--resume-root", type=Path)
    parser.add_argument("--all", action="store_true", dest="all_genes")
    parser.add_argument("--pilot-tiles", type=int, default=20)
    parser.add_argument("--accession", action="append", default=["P00533"])
    args = parser.parse_args()
    if args.pilot_tiles < 1:
        fail("--pilot-tiles must be positive")
    for accession in args.accession:
        if not ACCESSION_RE.fullmatch(accession.upper()):
            fail(f"Invalid pilot accession: {accession}")
    build(
        args.source_root, args.protein_basic, args.gene_bridge, args.output_root,
        all_genes=args.all_genes, pilot_tiles=args.pilot_tiles,
        accessions=[value.upper() for value in args.accession],
        resume_root=args.resume_root,
    )


if __name__ == "__main__":
    main()
