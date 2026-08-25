import type { GoAspect } from "./api";

export function applyGoTextFilters(query: string, evidenceCode: string): { query: string; evidenceCode: string } {
  return { query: query.trim(), evidenceCode: evidenceCode.trim().toUpperCase() };
}

/** A second activation of the selected GO aspect closes its bounded browser. */
export function toggledGoAspect(current: GoAspect | null, requested: GoAspect): GoAspect | null {
  return current === requested ? null : requested;
}

export function goAspectLabel(aspect: GoAspect): string {
  return aspect === "MF" ? "Molecular function" : aspect === "BP" ? "Biological process" : "Cellular component";
}

export function quickGoTermUrl(goId: string): string {
  return `https://www.ebi.ac.uk/QuickGO/term/${encodeURIComponent(goId)}`;
}

export function pubmedUrl(referenceId: string | null): string | null {
  const match = referenceId?.match(/^PMID:(\d+)$/i);
  return match ? `https://pubmed.ncbi.nlm.nih.gov/${match[1]}/` : null;
}

export function formatGoDate(value: string | null): string {
  return value && /^\d{8}$/.test(value) ? `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}` : value ?? "Not recorded";
}

export function goTermEvidencePath(
  accession: string,
  goId: string,
  options: { evidenceCode: string; includeNegated: boolean; cursor?: string | null; limit?: number },
): string {
  const params = new URLSearchParams({ limit: String(options.limit ?? 20) });
  const evidenceCode = options.evidenceCode.trim().toUpperCase();
  if (evidenceCode) params.set("evidence_code", evidenceCode);
  if (options.includeNegated) params.set("include_negated", "true");
  if (options.cursor) params.set("cursor", options.cursor);
  return `/proteins/${encodeURIComponent(accession)}/go/terms/${encodeURIComponent(goId)}/evidence?${params}`;
}
