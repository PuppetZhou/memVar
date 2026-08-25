import { ExpressionGroup, ExpressionItem, ExpressionModality } from "../../lib/api";
import { resolveTissueDisplay, TissueDisplayTerm } from "../../lib/tissue-display-crosswalk";

export type ExpressionSpec = {
  key: ExpressionModality;
  label: string;
  unit: string;
  explanation: string;
  low: string;
  high: string;
};

export const EXPRESSION_SPECS: ExpressionSpec[] = [
  { key: "hpa_rna", label: "HPA RNA", unit: "nTPM", explanation: "Independent log10(1 + nTPM) scale, visually capped at this protein's 95th percentile; tooltips retain raw nTPM.", low: "#E7F3DF", high: "#00796B" },
  { key: "hpa_ms", label: "HPA MS", unit: "source intensity", explanation: "Independent log10(1 + source intensity) scale, visually capped at this protein's 95th percentile. Missing is not zero.", low: "#FFF0D6", high: "#C05A17" },
  { key: "hpa_ihc", label: "HPA IHC", unit: "categorical staining", explanation: "Categorical cell-type distribution; no tissue-level maximum is inferred.", low: "#F7E7A8", high: "#8D263A" },
  { key: "paxdb", label: "PaxDB", unit: "ppm", explanation: "Independent log10(1 + ppm) scale, visually capped at this protein's 95th percentile. Multiple datasets are retained as separate strips.", low: "#F1DCEC", high: "#7A284F" },
];

export type ExpressionDisplayGroup = TissueDisplayTerm & {
  columnId: string;
  items: ExpressionItem[];
  rawTerms: string[];
};

export function sourceTerm(item: ExpressionItem): string {
  return item.source_tissue ?? item.source_organ ?? "Source term unavailable";
}

export function displayColumnId(label: string): string {
  return label.trim().toLocaleLowerCase();
}

export function modalityGroups(group: ExpressionGroup | undefined): ExpressionDisplayGroup[] {
  if (!group) return [];
  const grouped = new Map<string, ExpressionDisplayGroup>();
  for (const item of group.items) {
    const rawTerm = sourceTerm(item);
    const term = resolveTissueDisplay(item.source_database, rawTerm);
    const columnId = displayColumnId(term.displayLabel);
    const current = grouped.get(columnId);
    if (current) {
      current.items.push(item);
      if (!current.rawTerms.includes(rawTerm)) current.rawTerms.push(rawTerm);
    } else {
      grouped.set(columnId, { ...term, columnId, items: [item], rawTerms: [rawTerm] });
    }
  }
  return Array.from(grouped.values()).sort((left, right) => left.order - right.order || left.displayLabel.localeCompare(right.displayLabel));
}

export function numericValue(item: ExpressionItem): number | null {
  return typeof item.raw_value === "number" && Number.isFinite(item.raw_value) ? item.raw_value : null;
}

export function transformedValue(modality: ExpressionModality, value: number): number {
  return modality === "hpa_ihc" ? value : Math.log10(1 + Math.max(0, value));
}

export function numericScaleMaximum(group: ExpressionGroup | undefined): number {
  const values = (group?.items.map(numericValue).filter((value): value is number => value !== null).map((value) => transformedValue(group.modality, value)) ?? []).sort((left, right) => left - right);
  if (!values.length) return 0;
  // A single extreme source measurement should not flatten the entire tissue
  // matrix. This is a display cap only: raw values remain in tooltips/tables.
  return values[Math.max(0, Math.ceil(values.length * .95) - 1)] ?? 0;
}

export function detailText(item: ExpressionItem, key: string): string | null {
  const value = item.details[key];
  return value === null || value === undefined || value === "" ? null : String(value);
}

export function formatExpressionValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Missing (not zero)";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumSignificantDigits: 6 });
  return String(value);
}

export function formatSourceRelease(value: string): string {
  return value === "not_recorded" ? "release not recorded" : value;
}

export const IHC_LEVELS = ["Not detected", "Low", "Medium", "High"] as const;

export function ihcLevel(value: unknown): (typeof IHC_LEVELS)[number] | "Missing" {
  const normalized = String(value ?? "").trim().toLocaleLowerCase();
  return IHC_LEVELS.find((level) => level.toLocaleLowerCase() === normalized) ?? "Missing";
}
