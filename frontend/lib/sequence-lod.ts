export type CanonicalRange = {
  start: number;
  end: number;
};

export type VariantOverviewMark = CanonicalRange & {
  totalCount: number;
  clinvarPlpCount: number;
  occupiedSiteCount: number;
};

export type PtmOverviewSite = {
  position: number;
  totalCount: number;
  types: Array<{ ptmType: string; count: number }>;
};

export type PtmOverviewMark = CanonicalRange & {
  totalCount: number;
  occupiedSiteCount: number;
  types: Array<{ ptmType: string; count: number }>;
};

export type StabilityOverviewSummary = CanonicalRange & {
  observationCount: number;
  distinctSubstitutionCount: number;
  min: number | null;
  q25: number | null;
  median: number | null;
  q75: number | null;
  max: number | null;
};

export type StabilityOverviewInput = CanonicalRange & {
  observationCount: number;
  distinctSubstitutionCount: number;
  min: number | null;
  q25: number | null;
  median: number | null;
  q75: number | null;
  max: number | null;
};

export const MIN_OVERVIEW_MARKS = 48;
export const MAX_OVERVIEW_MARKS = 96;

function finiteCount(value: number | undefined): number {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? Math.floor(value) : 0;
}

function finiteValue(value: number | null): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/**
 * The overview budget is a display concern, not a data filter. Every returned
 * mark covers a contiguous canonical 1-based range and aggregation remains
 * count-conserving.
 */
export function sequenceMarkBudget(plotWidth: number): number {
  const estimate = Math.floor((Number.isFinite(plotWidth) ? plotWidth : 0) / 20);
  return Math.max(MIN_OVERVIEW_MARKS, Math.min(MAX_OVERVIEW_MARKS, estimate));
}

export function splitCanonicalRange(range: CanonicalRange, budget: number): CanonicalRange[] {
  const start = Math.max(1, Math.round(range.start));
  const end = Math.max(start, Math.round(range.end));
  const span = end - start + 1;
  const count = Math.max(1, Math.min(span, Math.round(budget)));
  const marks: CanonicalRange[] = [];

  for (let index = 0; index < count; index += 1) {
    const markStart = start + Math.floor(index * span / count);
    const markEnd = start + Math.floor((index + 1) * span / count) - 1;
    marks.push({ start: markStart, end: Math.max(markStart, markEnd) });
  }
  return marks;
}

function markIndex(position: number, range: CanonicalRange, count: number): number {
  const span = range.end - range.start + 1;
  return Math.max(0, Math.min(count - 1, Math.floor((position - range.start) * count / span)));
}

export function aggregateVariantMarks(
  totalCounts: number[],
  clinvarPlpCounts: number[],
  range: CanonicalRange,
  budget: number,
): VariantOverviewMark[] {
  const marks = splitCanonicalRange(range, budget).map((mark) => ({ ...mark, totalCount: 0, clinvarPlpCount: 0, occupiedSiteCount: 0 }));
  for (let position = range.start; position <= range.end; position += 1) {
    const total = finiteCount(totalCounts[position - 1]);
    if (!total) continue;
    const target = marks[markIndex(position, range, marks.length)];
    target.totalCount += total;
    target.clinvarPlpCount += Math.min(total, finiteCount(clinvarPlpCounts[position - 1]));
    target.occupiedSiteCount += 1;
  }
  return marks;
}

export function aggregatePtmMarks(
  sites: PtmOverviewSite[],
  range: CanonicalRange,
  budget: number,
): PtmOverviewMark[] {
  const marks = splitCanonicalRange(range, budget).map((mark) => ({ ...mark, totalCount: 0, occupiedSiteCount: 0, types: new Map<string, number>() }));
  for (const site of sites) {
    if (site.position < range.start || site.position > range.end) continue;
    const target = marks[markIndex(site.position, range, marks.length)];
    const siteCount = finiteCount(site.totalCount);
    if (!siteCount) continue;
    target.totalCount += siteCount;
    target.occupiedSiteCount += 1;
    for (const type of site.types) {
      const count = finiteCount(type.count);
      if (count) target.types.set(type.ptmType, (target.types.get(type.ptmType) ?? 0) + count);
    }
  }
  return marks.map(({ types, ...mark }) => ({
    ...mark,
    types: [...types.entries()].map(([ptmType, count]) => ({ ptmType, count })).sort((left, right) => right.count - left.count || left.ptmType.localeCompare(right.ptmType)),
  }));
}

function weightedQuantile(values: Array<{ value: number; weight: number }>, quantile: number): number | null {
  const usable = values.filter((entry) => finiteValue(entry.value) && entry.weight > 0).sort((left, right) => left.value - right.value);
  const totalWeight = usable.reduce((total, entry) => total + entry.weight, 0);
  if (!totalWeight) return null;
  const target = totalWeight * Math.max(0, Math.min(1, quantile));
  let seen = 0;
  for (const entry of usable) {
    seen += entry.weight;
    if (seen >= target) return entry.value;
  }
  return usable.at(-1)?.value ?? null;
}

/**
 * Re-aggregates already bounded server summaries. Quartiles are weighted
 * summary estimates at overview scale; the exact per-site distribution remains
 * available only after zooming into the detail window.
 */
export function aggregateStabilityMarks(
  bins: StabilityOverviewInput[],
  range: CanonicalRange,
  budget: number,
): StabilityOverviewSummary[] {
  const marks = splitCanonicalRange(range, budget).map((mark) => ({ ...mark, items: [] as StabilityOverviewInput[] }));
  for (const bin of bins) {
    const overlapStart = Math.max(range.start, bin.start);
    const overlapEnd = Math.min(range.end, bin.end);
    if (overlapStart > overlapEnd) continue;
    const midpoint = (overlapStart + overlapEnd) / 2;
    marks[markIndex(midpoint, range, marks.length)].items.push(bin);
  }
  return marks.map(({ start, end, items }) => {
    const observed = items.filter((item) => finiteValue(item.median));
    const weights = observed.map((item) => Math.max(1, finiteCount(item.observationCount)));
    const values = (field: "q25" | "median" | "q75") => weightedQuantile(observed.flatMap((item, index) => finiteValue(item[field]) ? [{ value: item[field], weight: weights[index] }] : []), .5);
    const minValues = observed.map((item) => item.min).filter(finiteValue);
    const maxValues = observed.map((item) => item.max).filter(finiteValue);
    return {
      start,
      end,
      observationCount: items.reduce((total, item) => total + finiteCount(item.observationCount), 0),
      distinctSubstitutionCount: items.reduce((total, item) => total + finiteCount(item.distinctSubstitutionCount), 0),
      min: minValues.length ? Math.min(...minValues) : null,
      q25: values("q25"),
      median: values("median"),
      q75: values("q75"),
      max: maxValues.length ? Math.max(...maxValues) : null,
    };
  });
}
