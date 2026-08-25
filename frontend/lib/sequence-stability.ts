import type { SequenceOverviewResponse, StabilityOverviewBin } from "./api";

export const STABILITY_COLORS = {
  stabilizing: "#1B75BC",
  neutral: "#7A838C",
  destabilizing: "#D94949",
} as const;

export function stabilityColor(ddg: number): string {
  if (ddg <= -0.5) return STABILITY_COLORS.stabilizing;
  if (ddg >= 0.5) return STABILITY_COLORS.destabilizing;
  return STABILITY_COLORS.neutral;
}

export function smoothWavePath(points: Array<{ x: number; y: number }>): string {
  if (!points.length) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const point = points[index];
    const midpoint = (previous.x + point.x) / 2;
    path += ` C ${midpoint} ${previous.y}, ${midpoint} ${point.y}, ${point.x} ${point.y}`;
  }
  return path;
}

export type StabilityOverviewView = {
  available: boolean;
  bins: StabilityOverviewBin[];
  totals: {
    predicted_variants: number;
    canonical_sites: number;
    distinct_substitutions: number;
  };
};

const EMPTY_TOTALS = {
  predicted_variants: 0,
  canonical_sites: 0,
  distinct_substitutions: 0,
} as const;

function count(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0
    ? Math.floor(value)
    : 0;
}

/**
 * Normalise the M15 extension at the API boundary. During a rolling local
 * restart the browser can briefly receive a pre-M15 sequence response; that
 * means "unavailable", not a biological zero and not a fatal render error.
 */
export function stabilityOverviewFrom(
  response: Pick<SequenceOverviewResponse, "stability_bins" | "stability_totals"> | null | undefined,
): StabilityOverviewView {
  const available = Array.isArray(response?.stability_bins) && response?.stability_totals != null;
  if (!available) return { available: false, bins: [], totals: { ...EMPTY_TOTALS } };

  const totals = response.stability_totals!;
  return {
    available: true,
    bins: response.stability_bins!,
    totals: {
      predicted_variants: count(totals.predicted_variants),
      canonical_sites: count(totals.canonical_sites),
      distinct_substitutions: count(totals.distinct_substitutions),
    },
  };
}
