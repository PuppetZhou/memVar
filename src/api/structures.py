"""Serve existing local AlphaFold models with current-sequence validation.

Legacy manifest ranges are candidate ranges only. Residue selection is enabled
after the ATOM sequence exactly matches the current canonical sequence slice.
No new alignment, inferred offset, or scientific source merge is performed.
"""
from functools import lru_cache
import gzip
from pathlib import Path

import pyarrow.parquet as pq
import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from .db import query

router = APIRouter(prefix="/api")
PROJECT = Path(__file__).resolve().parents[3]
AA = dict(zip(
    "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split(),
    "ARNDCQEGHILKMFPSTWYV",
))


@lru_cache(maxsize=1)
def source_root() -> Path:
    try:
        config = yaml.safe_load((PROJECT / "config/sources.yaml").read_text())
        return Path(config["Site-Region"]["collections"]["rSASA"]["structure_directory"]).resolve()
    except (OSError, KeyError, TypeError, yaml.YAMLError):
        raise HTTPException(503, "Local structure source is not configured") from None


@lru_cache(maxsize=1)
def manifest() -> dict:
    path = source_root() / "manifest.parquet"
    if not path.is_file():
        raise HTTPException(503, "Local structure catalogue is unavailable")
    try:
        rows = pq.read_table(path, columns=["uniprot_accession", "fragment_number", "relative_path",
            "canonical_start", "canonical_end", "model_version", "source"]).to_pylist()
    except (OSError, ValueError):
        raise HTTPException(503, "Local structure catalogue is unavailable") from None
    grouped: dict[str, list] = {}
    for row in rows:
        grouped.setdefault(row["uniprot_accession"], []).append(row)
    return grouped


def model_path(row: dict) -> Path:
    root = source_root()
    path = (root / row["relative_path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, "Structure file is unavailable")
    return path


@lru_cache(maxsize=24)
def read_model(path: str, modified: int) -> tuple[bytes, list]:
    with gzip.open(path, "rb") as stream:
        contents = stream.read()
    residues = []
    seen = set()
    for line in contents.decode("ascii", errors="replace").splitlines():
        if line.startswith("ENDMDL"):
            break
        if not line.startswith("ATOM  ") or line[12:16].strip() != "CA":
            continue
        if line[16:17] not in (" ", "A"):
            continue
        key = (line[21:22], int(line[22:26]), line[26:27].strip())
        if key in seen:
            continue
        seen.add(key)
        residues.append({"chain_id": key[0], "auth_residue_number": key[1], "insertion_code": key[2],
                         "residue": AA.get(line[17:20], "X")})
    return contents, residues


def protein_sequence(accession: str) -> dict:
    rows = query("""SELECT p.accession,p.default_sequence_id AS sequence_id,s.sequence,s.length
                    FROM web.protein p JOIN web.protein_sequence s
                    ON s.sequence_id=p.default_sequence_id WHERE p.accession=:accession""",
                 {"accession": accession.upper()})
    if not rows:
        raise HTTPException(404, "Protein not found")
    return rows[0]


def catalogue(accession: str, protein: dict) -> list:
    items = []
    for row in sorted(manifest().get(accession, []), key=lambda r: r["fragment_number"]):
        start, end = row["canonical_start"], row["canonical_end"]
        item = {"id": str(row["fragment_number"]), "label": f"AlphaFold · F{row['fragment_number']}",
                "source": row["source"], "model_version": row["model_version"], "kind": "prediction",
                "sequence_id": protein["sequence_id"], "start": start, "end": end,
                "mapping_status": "unverified", "residue_mapping": [], "chains": [],
                "url": f"/api/proteins/{accession}/structures/{row['fragment_number']}/model.pdb"}
        try:
            path = model_path(row)
            _, residues = read_model(str(path), path.stat().st_mtime_ns)
        except (OSError, EOFError, ValueError, HTTPException):
            item.update(mapping_status="file_unavailable", url=None)
            items.append(item)
            continue
        item["chains"] = [{"id": chain, "residue_count": sum(r["chain_id"] == chain for r in residues)}
                          for chain in sorted({r["chain_id"] for r in residues})]
        observed = "".join(r["residue"] for r in residues)
        if (start and end and 1 <= start <= end <= protein["length"]
                and len({r["chain_id"] for r in residues}) == 1
                and len(residues) == end - start + 1
                and observed == protein["sequence"][start - 1:end]):
            item["mapping_status"] = "exact_current_canonical"
            item["residue_mapping"] = [dict(r, position=start + i) for i, r in enumerate(residues)]
        else:
            item["mapping_status"] = "sequence_mismatch"
        items.append(item)
    return items


@router.get("/proteins/{accession}/structures")
def structures(accession: str):
    protein = protein_sequence(accession)
    items = catalogue(protein["accession"], protein)
    return {"accession": protein["accession"], "sequence_id": protein["sequence_id"], "items": items,
            "status": "available" if items else "no_local_model"}


@router.get("/proteins/{accession}/structures/{fragment}/model.pdb")
def structure_model(accession: str, fragment: int):
    protein = protein_sequence(accession)
    row = next((r for r in manifest().get(protein["accession"], []) if r["fragment_number"] == fragment), None)
    if row is None:
        raise HTTPException(404, "Structure not found")
    path = model_path(row)
    try:
        contents, _ = read_model(str(path), path.stat().st_mtime_ns)
    except (OSError, EOFError, ValueError):
        raise HTTPException(503, "Structure file could not be read") from None
    return Response(contents, media_type="chemical/x-pdb", headers={"Cache-Control": "private, max-age=300"})
