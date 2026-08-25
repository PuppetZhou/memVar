export type ClinicalClassificationTone = "pathogenic" | "benign" | "uncertain" | "conflict" | "neutral";

const CLINICAL_CLASSIFICATION_FIELDS = new Set(["clinicalsignificance", "classification"]);

export function clinicalClassification(record: Record<string, unknown>): string | null {
  for (const [key, value] of Object.entries(record)) {
    const normalizedKey = key.toLocaleLowerCase().replaceAll(/[_\s-]/g, "");
    if (CLINICAL_CLASSIFICATION_FIELDS.has(normalizedKey) && typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return null;
}

export function clinicalClassificationTone(value: string | null): ClinicalClassificationTone {
  if (!value) return "neutral";
  const normalized = value.toLocaleLowerCase();
  if (normalized.includes("conflict")) return "conflict";
  if (normalized.includes("uncertain significance") || /(^|\W)vus($|\W)/i.test(value)) return "uncertain";
  if (normalized.includes("benign")) return "benign";
  if (normalized.includes("pathogenic")) return "pathogenic";
  return "neutral";
}
