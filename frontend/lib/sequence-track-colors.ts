export const SEQUENCE_TRACK_PALETTE = [
  "#7b95c6",
  "#49c2d9",
  "#a1d8e8",
  "#67a583",
  "#a2c986",
  "#d0e2c0",
  "#fded95",
  "#ffc1a6",
  "#f59c7c",
  "#f47254",
  "#c85e62",
] as const;

export type SequenceTrackColor = (typeof SEQUENCE_TRACK_PALETTE)[number];

export type NormalizedTrackCategory = Readonly<{
  key: string;
  label: string;
}>;

export type TrackCategoryStyle = Readonly<{
  key: string;
  color: SequenceTrackColor;
  patternIndex: number;
  textColor: "#172230" | "#ffffff";
}>;

export type VariantCountBucketKey = "none" | "one" | "two" | "three-to-five" | "six-to-nine" | "ten-plus";

export type VariantCountBucket = Readonly<{
  key: VariantCountBucketKey;
  label: string;
  color: SequenceTrackColor;
  min: number;
  max: number | null;
}>;

const VARIANT_COUNT_BUCKETS: readonly VariantCountBucket[] = [
  { key: "none", label: "No variants", color: "#d0e2c0", min: 0, max: 0 },
  { key: "one", label: "1 variant", color: "#a1d8e8", min: 1, max: 1 },
  { key: "two", label: "2 variants", color: "#a2c986", min: 2, max: 2 },
  { key: "three-to-five", label: "3–5 variants", color: "#fded95", min: 3, max: 5 },
  { key: "six-to-nine", label: "6–9 variants", color: "#f59c7c", min: 6, max: 9 },
  { key: "ten-plus", label: "10+ variants", color: "#c85e62", min: 10, max: null },
];

function cleanPart(value: string | null | undefined): string {
  return value?.normalize("NFKC").trim().replace(/\s+/g, " ") ?? "";
}

function stableKey(label: string): string {
  return cleanPart(label).toLowerCase();
}

function category(label: string): NormalizedTrackCategory {
  return { key: stableKey(label), label };
}

function cleanTopologyDescription(value: string | null | undefined): string {
  return cleanPart(value)
    .replace(/\s*;\s*name\s*=\s*[^;]+(?=\s*;|$)/gi, "")
    .replace(/\s*;\s*/g, "; ")
    .trim();
}

/** Keep named membrane sides distinct while merging numbered helices of the same kind. */
export function normalizeTopologyCategory(
  featureType: string | null | undefined,
  description: string | null | undefined,
): NormalizedTrackCategory {
  const type = cleanPart(featureType);
  const detail = cleanTopologyDescription(description);
  const typeKey = stableKey(type);

  if (typeKey === "topological domain") return category(detail || type || "Topology");
  if (typeKey === "transmembrane" || typeKey === "intramembrane") {
    return category(detail ? `${type}: ${detail}` : type);
  }
  return category(type || detail || "Topology");
}

/** Functional annotations are colored by feature type; descriptions remain instance labels. */
export function normalizeFunctionalCategory(
  featureType: string | null | undefined,
  description?: string | null,
): NormalizedTrackCategory {
  return category(cleanPart(featureType) || cleanPart(description) || "Functional site");
}

export function normalizePfamCategory(
  pfamType: string | null | undefined,
  pfamId?: string | null,
  pfamAccession?: string | null,
): NormalizedTrackCategory {
  return category(cleanPart(pfamType) || cleanPart(pfamId) || cleanPart(pfamAccession) || "Pfam domain");
}

export function normalizePtmCategory(ptmType: string | null | undefined): NormalizedTrackCategory {
  return category(cleanPart(ptmType) || "PTM site");
}

function hashCategory(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function channelToLinear(channel: number): number {
  const value = channel / 255;
  return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
}

/** Choose whichever supported foreground has the stronger WCAG contrast. */
export function contrastTextColor(background: string): "#172230" | "#ffffff" {
  const hex = background.trim().replace(/^#/, "");
  const expanded = hex.length === 3 ? [...hex].map((part) => `${part}${part}`).join("") : hex;
  if (!/^[\da-f]{6}$/i.test(expanded)) return "#172230";

  const red = channelToLinear(Number.parseInt(expanded.slice(0, 2), 16));
  const green = channelToLinear(Number.parseInt(expanded.slice(2, 4), 16));
  const blue = channelToLinear(Number.parseInt(expanded.slice(4, 6), 16));
  const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
  const darkLuminance = 0.0167;
  const darkContrast = (luminance + 0.05) / (darkLuminance + 0.05);
  const whiteContrast = 1.05 / (luminance + 0.05);
  return darkContrast >= whiteContrast ? "#172230" : "#ffffff";
}

/**
 * Assign colors from the complete category set. The first 11 categories always
 * have distinct fills; later categories reuse fills with a new pattern index.
 */
export function assignTrackCategoryStyles(
  categories: readonly (string | NormalizedTrackCategory)[],
): Map<string, TrackCategoryStyle> {
  const keys = [...new Set(categories.map((item) => (
    typeof item === "string" ? stableKey(item) : stableKey(item.key)
  )).filter(Boolean))].sort((left, right) => left.localeCompare(right, "en"));
  const styles = new Map<string, TrackCategoryStyle>();
  const usedByPattern = new Map<number, Set<number>>();

  for (const key of keys) {
    const start = hashCategory(key) % SEQUENCE_TRACK_PALETTE.length;
    let patternIndex = 0;
    let colorIndex = start;

    while (true) {
      const used = usedByPattern.get(patternIndex) ?? new Set<number>();
      const availableOffset = Array.from({ length: SEQUENCE_TRACK_PALETTE.length }, (_, offset) => offset)
        .find((offset) => !used.has((start + offset) % SEQUENCE_TRACK_PALETTE.length));
      if (availableOffset !== undefined) {
        colorIndex = (start + availableOffset) % SEQUENCE_TRACK_PALETTE.length;
        used.add(colorIndex);
        usedByPattern.set(patternIndex, used);
        break;
      }
      patternIndex += 1;
    }

    const color = SEQUENCE_TRACK_PALETTE[colorIndex];
    styles.set(key, { key, color, patternIndex, textColor: contrastTextColor(color) });
  }
  return styles;
}

export function variantCountBucket(count: number): VariantCountBucket {
  const safeCount = Number.isFinite(count) ? Math.max(0, Math.floor(count)) : 0;
  return VARIANT_COUNT_BUCKETS.find((bucket) => (
    safeCount >= bucket.min && (bucket.max === null || safeCount <= bucket.max)
  )) ?? VARIANT_COUNT_BUCKETS[0];
}

export function variantCountBuckets(): readonly VariantCountBucket[] {
  return VARIANT_COUNT_BUCKETS;
}
