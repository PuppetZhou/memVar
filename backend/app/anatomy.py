"""Protein-scoped anatomy availability summaries from explicit display mappings."""

from __future__ import annotations

import json
from pathlib import Path
import re

import duckdb
from fastapi import APIRouter, Depends

from .models import AnatomyEvidenceSummary, AnatomyRegionSummary, AnatomySummaryResponse
from .store import get_connection, require_protein
from .release_store import release_store


router = APIRouter(prefix="/api/v1")
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "anatomy_crosswalk.json"


def normalize_term(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().replace("_", " ").replace("-", " ")).strip()


def load_crosswalk() -> tuple[list[dict[str, object]], dict[str, tuple[str, str | None]]]:
    payload = json.loads(CONFIG_PATH.read_text())
    regions = payload["regions"]
    aliases: dict[str, tuple[str, str | None]] = {}
    ontology_by_region: dict[str, str | None] = {}
    for mapping in payload["mappings"]:
        target = str(mapping["body_region_id"]), mapping.get("ontology_id")
        ontology_by_region[target[0]] = target[1]
        for raw in mapping["aliases"]:
            key = normalize_term(str(raw))
            previous = aliases.get(key)
            if previous is not None and previous != target:
                raise RuntimeError(f"Conflicting anatomy mapping for: {raw}")
            aliases[key] = target
    for region in regions:
        region["ontology_id"] = ontology_by_region.get(str(region["id"]))
    return regions, aliases


REGIONS, ALIASES = load_crosswalk()


def mapped_region(raw_term: str | None) -> tuple[str, str | None, bool]:
    if raw_term is None or not raw_term.strip():
        return "other", None, False
    mapped = ALIASES.get(normalize_term(raw_term))
    return (*mapped, True) if mapped else ("other", None, False)


@router.get("/proteins/{acc}/anatomy/summary", response_model=AnatomySummaryResponse)
def anatomy_summary(
    acc: str,
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> AnatomySummaryResponse:
    overview = require_protein(core, acc)
    accession = str(overview["uniprot_accession"])
    summary_path = release_store().anatomy_summary
    if not summary_path.is_file():
        raise RuntimeError(f"Generated anatomy summary is missing: {summary_path}")
    rows = core.execute(
        """
        SELECT body_region_id, ontology_id, layer, source_database, modality_or_type,
               record_count, distinct_context_count, raw_filter_terms, mapping_status
        FROM read_parquet(?) WHERE uniprot_accession = ?
        ORDER BY body_region_id, layer, source_database, modality_or_type
        """,
        [str(summary_path), accession],
    ).fetchall()

    summaries: list[AnatomyRegionSummary] = []
    for region in REGIONS:
        region_id = str(region["id"])
        region_rows = [row for row in rows if row[0] == region_id]
        evidence = [AnatomyEvidenceSummary(
            layer=row[2], source_database=row[3], modality_or_type=row[4],
            record_count=int(row[5]), distinct_context_count=int(row[6]),
            raw_filter_terms=list(row[7] or []),
        ) for row in region_rows]
        ontology = next((row[1] for row in region_rows if row[1]), region.get("ontology_id"))
        summaries.append(AnatomyRegionSummary(
            body_region_id=region_id, display_label=str(region["label"]),
            ontology_id=ontology, has_data=bool(evidence),
            mapping_status=("unmapped_other" if any(row[8] == "unmapped_other" for row in region_rows) else "explicit"),
            evidence=evidence,
        ))
    return AnatomySummaryResponse(uniprot_accession=accession, regions=summaries)
