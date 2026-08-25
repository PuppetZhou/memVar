import type { AlphaFoldStructureFragment, SequenceVariantSiteDensity } from "./api";
import { variantCountBucket } from "./sequence-track-colors";

export const STRUCTURE_MISSING_COLOR = "#d8dee8";

export type StructureAtom = Readonly<{
  b?: number;
  resi?: number;
}>;

export type FragmentResidueMapping = Readonly<{
  valid: boolean;
  canonicalStart: number | null;
  canonicalEnd: number | null;
}>;

/**
 * Translate a canonical 1-based residue into the fragment-local 1-based PDB
 * residue number. An invalid/incomplete DBREF mapping is never guessed.
 */
export function canonicalToFragmentResidue(
  canonicalPosition: number,
  mapping: FragmentResidueMapping,
): number | null {
  if (
    !mapping.valid
    || mapping.canonicalStart === null
    || mapping.canonicalEnd === null
    || !Number.isInteger(canonicalPosition)
    || canonicalPosition < mapping.canonicalStart
    || canonicalPosition > mapping.canonicalEnd
  ) return null;
  return canonicalPosition - mapping.canonicalStart + 1;
}

/** Translate a clicked fragment-local PDB residue back to canonical space. */
export function fragmentToCanonicalResidue(
  fragmentPosition: number,
  mapping: FragmentResidueMapping,
): number | null {
  if (
    !mapping.valid
    || mapping.canonicalStart === null
    || mapping.canonicalEnd === null
    || !Number.isInteger(fragmentPosition)
    || fragmentPosition < 1
  ) return null;
  const canonicalPosition = mapping.canonicalStart + fragmentPosition - 1;
  return canonicalPosition <= mapping.canonicalEnd ? canonicalPosition : null;
}

export function confidenceColor(atom: StructureAtom): string {
  const score = atom.b;
  if (typeof score !== "number" || !Number.isFinite(score)) return STRUCTURE_MISSING_COLOR;
  if (score > 90) return "#0053D6";
  if (score >= 70) return "#65CBF3";
  if (score >= 50) return "#FFDB13";
  return "#FF7D45";
}

/**
 * AlphaFold fragments restart PDB residue numbering at one. DBREF supplies the
 * canonical interval, so only accept that mapping when the parsed model spans
 * the complete local 1..N interval declared by DBREF.
 */
export function validateFragmentResidueMapping(
  fragment: AlphaFoldStructureFragment,
  atoms: readonly StructureAtom[],
): FragmentResidueMapping {
  const start = fragment.canonical_start;
  const end = fragment.canonical_end;
  if (start === null || end === null || !Number.isInteger(start) || !Number.isInteger(end) || start < 1 || end < start) {
    return { valid: false, canonicalStart: null, canonicalEnd: null };
  }

  const expectedLength = end - start + 1;
  const residues = new Set<number>();
  for (const atom of atoms) {
    if (Number.isInteger(atom.resi)) residues.add(atom.resi as number);
  }
  const values = [...residues];
  const valid = values.length === expectedLength
    && Math.min(...values) === 1
    && Math.max(...values) === expectedLength;
  return { valid, canonicalStart: start, canonicalEnd: end };
}

export function sequenceVariantColor(
  atom: StructureAtom,
  mapping: FragmentResidueMapping,
  density: SequenceVariantSiteDensity | null,
): string {
  if (!mapping.valid || mapping.canonicalStart === null || mapping.canonicalEnd === null || !density) {
    return STRUCTURE_MISSING_COLOR;
  }
  if (!Number.isInteger(atom.resi) || (atom.resi as number) < 1) return STRUCTURE_MISSING_COLOR;
  if (!Number.isInteger(density.start) || !Number.isInteger(density.end) || density.end < density.start) {
    return STRUCTURE_MISSING_COLOR;
  }
  if (density.total_counts.length !== density.end - density.start + 1) return STRUCTURE_MISSING_COLOR;

  const canonicalPosition = mapping.canonicalStart + (atom.resi as number) - 1;
  if (canonicalPosition > mapping.canonicalEnd || canonicalPosition < density.start || canonicalPosition > density.end) {
    return STRUCTURE_MISSING_COLOR;
  }
  const count = density.total_counts[canonicalPosition - density.start];
  if (!Number.isFinite(count) || count < 0) return STRUCTURE_MISSING_COLOR;
  return variantCountBucket(count).color;
}
