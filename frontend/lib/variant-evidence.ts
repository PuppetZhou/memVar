export type VariantEvidenceBranch = "facts" | "effects" | "clinvar" | "cosmic" | "stability" | "population";

export const VARIANT_EVIDENCE_BRANCHES: { key: VariantEvidenceBranch; label: string }[] = [
  { key: "facts", label: "Variant facts" },
  { key: "effects", label: "Protein effects" },
  { key: "clinvar", label: "ClinVar" },
  { key: "cosmic", label: "COSMIC" },
  { key: "stability", label: "Stability" },
  { key: "population", label: "Population" },
];

/** Build an external link only from the stable, typed ClinVar accession we actually store. */
export function clinvarRecordUrl(record: Record<string, unknown>): string | null {
  const accession = record.RCVaccession;
  if (typeof accession !== "string" || !/^RCV\d+(?:\.\d+)?$/.test(accession)) return null;
  return `https://www.ncbi.nlm.nih.gov/clinvar/${encodeURIComponent(accession)}/`;
}

export function normalizedSource(value: string): "clinvar" | "cosmic" | "population" | "other" {
  const source = value.trim().toLowerCase();
  if (source === "clinvar") return "clinvar";
  if (source === "cosmic") return "cosmic";
  if (source === "gnomad" || source === "dbsnp") return "population";
  return "other";
}
