export type VariantEvidenceBranch = "facts" | "effects" | "clinvar" | "cosmic" | "stability" | "population";
export type VariantSourceTone = "clinvar" | "cosmic" | "gnomad" | "dbsnp" | "prediction" | "stability" | "neutral";
export type StabilityTone = "stabilizing" | "small-change" | "destabilizing";
export type GnomadAncestryTone = "afr" | "ami" | "amr" | "asj" | "eas" | "fin" | "mid" | "nfe" | "sas" | "remaining";

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
  if (source === "gnomad") return "population";
  return "other";
}

/** Source hue identifies provenance only; it is never a clinical or frequency scale. */
export function variantSourceTone(value: string): VariantSourceTone {
  const source = value.trim().toLowerCase();
  if (source === "clinvar") return "clinvar";
  if (source === "cosmic") return "cosmic";
  if (source === "gnomad") return "gnomad";
  if (source === "dbsnp") return "dbsnp";
  if (source === "alphamissense") return "prediction";
  if (source === "thermompnn" || source === "stability") return "stability";
  return "neutral";
}

export function stabilityTone(direction: string | null | undefined): StabilityTone {
  if (direction === "predicted_stabilizing") return "stabilizing";
  if (direction === "predicted_destabilizing") return "destabilizing";
  return "small-change";
}

export function gnomadAncestryTone(value: string): GnomadAncestryTone {
  const ancestry = value.trim().toLowerCase();
  return ["afr", "ami", "amr", "asj", "eas", "fin", "mid", "nfe", "sas"].includes(ancestry)
    ? ancestry as GnomadAncestryTone
    : "remaining";
}
