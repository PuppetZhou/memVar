import type {
  DifferentialExpressionContrast,
  DifferentialExpressionDataset,
  DifferentialExpressionTargetResult,
} from "./api";

export type ContrastDirection = DifferentialExpressionTargetResult["direction"] | "mixed";

type NullableTargetResult = Omit<DifferentialExpressionTargetResult, "log2fc" | "fdr"> & {
  log2fc: number | null;
  fdr: number | null;
};

type NullableContrast = Omit<DifferentialExpressionContrast, "target_results"> & {
  target_results: NullableTargetResult[];
};

export const DE_SORT_RULE = "Source-defined direction/significance (defined up/down before mixed mapping; not-significant last), then FDR, |log2FC|, then contrast ID. This order is for display only, not disease importance.";

export function formatDeNumber(value: number | null, digits = 3) {
  if (value === null || !Number.isFinite(value)) return "Not available";
  if (value !== 0 && Math.abs(value) < .001) return value.toExponential(2);
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export function contrastDirection(contrast: NullableContrast): ContrastDirection {
  const directions = new Set(contrast.target_results.map((result) => result.direction));
  if (directions.size > 1) return "mixed";
  return contrast.target_results[0]?.direction ?? "not_significant";
}

function nullableNumberOrder(left: number | null, right: number | null) {
  if (left === null || !Number.isFinite(left)) return right === null || !Number.isFinite(right) ? 0 : 1;
  if (right === null || !Number.isFinite(right)) return -1;
  return left - right;
}

function finiteFirstAbsoluteLog2fcDescending(left: number | null, right: number | null) {
  const leftFinite = left !== null && Number.isFinite(left);
  const rightFinite = right !== null && Number.isFinite(right);
  if (!leftFinite || !rightFinite) return leftFinite === rightFinite ? 0 : leftFinite ? -1 : 1;
  return Math.abs(right) - Math.abs(left);
}

function directionOrder(direction: ContrastDirection) {
  if (direction === "up" || direction === "down") return 0;
  if (direction === "mixed") return 1;
  return 2;
}

export function representativeTargetResult<T extends NullableTargetResult>(contrast: Omit<NullableContrast, "target_results"> & { target_results: T[] }): T | null {
  return [...contrast.target_results].sort((left, right) =>
    nullableNumberOrder(left.fdr, right.fdr)
    || finiteFirstAbsoluteLog2fcDescending(left.log2fc, right.log2fc)
    || (left.ensembl_gene_id ?? "").localeCompare(right.ensembl_gene_id ?? "")
  )[0] ?? null;
}

export function compareContrasts(left: NullableContrast, right: NullableContrast) {
  const leftResult = representativeTargetResult(left);
  const rightResult = representativeTargetResult(right);
  return directionOrder(contrastDirection(left)) - directionOrder(contrastDirection(right))
    || nullableNumberOrder(leftResult?.fdr ?? null, rightResult?.fdr ?? null)
    || finiteFirstAbsoluteLog2fcDescending(leftResult?.log2fc ?? null, rightResult?.log2fc ?? null)
    || left.contrast_id.localeCompare(right.contrast_id);
}

export function sortContrasts<T extends NullableContrast>(contrasts: T[]) {
  return [...contrasts].sort(compareContrasts);
}

export function sortDifferentialExpressionDatasets(datasets: DifferentialExpressionDataset[]) {
  return datasets
    .map((dataset) => ({ ...dataset, contrasts: sortContrasts(dataset.contrasts) }))
    .sort((left, right) => {
      const firstOrder = compareContrasts(left.contrasts[0] ?? emptyContrast(left.dataset_id), right.contrasts[0] ?? emptyContrast(right.dataset_id));
      return firstOrder || left.dataset_id.localeCompare(right.dataset_id);
    });
}

function emptyContrast(datasetId: string): NullableContrast {
  return {
    contrast_id: `~${datasetId}`,
    disease_category: "",
    tissue: "",
    disease_condition: "",
    case_definition: "",
    control_definition: "",
    case_n: 0,
    control_n: 0,
    paired: false,
    target_result_total: 0,
    mapping_status: "unique_gene_row",
    target_results: [],
  };
}

export function differentialExpressionCounts(contrasts: NullableContrast[]) {
  return contrasts.reduce((counts, contrast) => {
    counts.total += 1;
    const direction = contrastDirection(contrast);
    if (direction === "up") counts.up += 1;
    else if (direction === "down") counts.down += 1;
    else if (direction === "mixed") counts.mixed += 1;
    else counts.notSignificant += 1;
    return counts;
  }, { total: 0, up: 0, down: 0, mixed: 0, notSignificant: 0 });
}
