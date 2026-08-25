"use client";

import {
  KeyboardEvent as ReactKeyboardEvent,
  memo,
  PointerEvent as ReactPointerEvent,
  RefObject,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  SequenceOverviewBin,
  SequenceOverviewFeatureInterval,
  SequenceOverviewPfamInterval,
  SequenceOverviewPtmSite,
  SequenceOverviewResponse,
  SequenceOverviewSecondaryStructureInterval,
  StabilityOverviewBin,
  StabilitySiteDetailResponse,
  SiteItem,
  SiteResponse,
} from "../lib/api";
import { fullLengthPosition, navigatorGeometry, panViewport, resizeViewport } from "../lib/sequence-navigator";
import { stabilityColor, stabilityOverviewFrom } from "../lib/sequence-stability";
import {
  aggregatePtmMarks,
  aggregateStabilityMarks,
  aggregateVariantMarks,
  sequenceMarkBudget,
} from "../lib/sequence-lod";
import { getJson } from "../lib/api-client";
import { formatTermLabel } from "../lib/display-labels";
import {
  assignTrackCategoryStyles,
  NormalizedTrackCategory,
  normalizeFunctionalCategory,
  normalizePfamCategory,
  normalizePtmCategory,
  normalizeTopologyCategory,
  TrackCategoryStyle,
  variantCountBucket,
  variantCountBuckets,
} from "../lib/sequence-track-colors";
import { StatusMessage } from "./status-message";
import { SelectedSiteEvidence } from "./selected-site-evidence";
import { allCovalentPairsAreDisulfide, covalentBondLabel, routeCovalentPairLanes } from "../lib/covalent-bonds";

type VisualTrack = "topology" | "pfam" | "functional" | "secondaryStructure" | "conservation" | "ptm" | "variant" | "stability" | "covalent";
type Viewport = { start: number; end: number };
type OverviewInterval = {
  id: string;
  label: string;
  start: number;
  end: number;
  source: string;
  kind: string;
  category: NormalizedTrackCategory;
};
type DetailState = { kind: "idle" | "loading" | "error" | "ready"; sites?: SiteResponse; error?: string };

const MAX_DETAIL_WINDOW = 120;
const MIN_VIEWPORT = 10;
const OVERVIEW_BINS = 400;
const RESIDUE_CELL_WIDTH = 44;
const RESIDUE_CELL_HEIGHT = 42;
const VARIANT_ALL_COLOR = "#7B95C6";
const VARIANT_PLP_COLOR = "#B42352";
const COVALENT_PAIR_PALETTE = ["#CC247C", "#E95351", "#F7A24F", "#FBEB66", "#4EA660", "#79CAFB", "#5292F7", "#AA77E9"];

function covalentPairColor(index: number) {
  const hex = COVALENT_PAIR_PALETTE[index % COVALENT_PAIR_PALETTE.length];
  const cycle = Math.floor(index / COVALENT_PAIR_PALETTE.length);
  if (!cycle) return hex;
  const amount = Math.min(.28, Math.ceil(cycle / 2) * .1);
  const toward = cycle % 2 ? 0 : 255;
  const channels = [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16));
  return `#${channels.map((channel) => Math.round(channel + (toward - channel) * amount).toString(16).padStart(2, "0")).join("")}`;
}

const TRACKS: { key: VisualTrack; label: string; symbol: string }[] = [
  { key: "topology", label: "Topology", symbol: "▱" },
  { key: "pfam", label: "Pfam domains", symbol: "▰" },
  { key: "functional", label: "Functional sites", symbol: "◆" },
  { key: "secondaryStructure", label: "Secondary structure", symbol: "⌒" },
  { key: "conservation", label: "Conservation (JSD)", symbol: "∿" },
  { key: "ptm", label: "PTM", symbol: "▲" },
  { key: "variant", label: "Variants", symbol: "▥" },
  { key: "stability", label: "Stability ΔΔG", symbol: "↕" },
  { key: "covalent", label: "Covalent bonds", symbol: "⌁" },
];

export type SiteSelection = { start: number; end: number; site?: number } | null;

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function boundedViewport(start: number, end: number, length: number): Viewport {
  const safeStart = Math.max(1, Math.min(Math.round(start), length));
  const safeEnd = Math.max(safeStart, Math.min(Math.round(end), length));
  return { start: safeStart, end: safeEnd };
}

function centeredViewport(center: number, span: number, length: number): Viewport {
  const width = Math.max(1, Math.min(Math.round(span), length));
  const start = Math.max(1, Math.min(Math.round(center - (width - 1) / 2), length - width + 1));
  return { start, end: start + width - 1 };
}

function sameSelection(left: SiteSelection, right: SiteSelection): boolean {
  return left?.start === right?.start && left?.end === right?.end && left?.site === right?.site;
}

function parsePinned(siteValue: string | null, rangeValue: string | null, length: number): SiteSelection {
  const site = Number(siteValue);
  if (siteValue && Number.isInteger(site) && site >= 1 && site <= length) return { start: site, end: site, site };
  const range = rangeValue?.match(/^(\d+)-(\d+)$/);
  if (!range) return null;
  const start = Number(range[1]);
  const end = Number(range[2]);
  return start >= 1 && end >= start && end <= length ? { start, end } : null;
}

function intervalPosition(position: number, start: number, end: number): number {
  return ((position - start) / Math.max(1, end - start + 1)) * 100;
}

function SequenceSelectionOverlay({ selection, viewport, height }: { selection: SiteSelection; viewport: Viewport; height: number }) {
  if (!selection || selection.end < viewport.start || selection.start > viewport.end) return null;
  const span = viewport.end - viewport.start + 1;
  if (selection.site !== undefined) {
    const x = ((selection.site - viewport.start + .5) / span) * 1000;
    return <line className="sequence-selection-line" x1={x} x2={x} y1={0} y2={height} />;
  }
  const start = Math.max(selection.start, viewport.start);
  const end = Math.min(selection.end, viewport.end);
  const x = ((start - viewport.start) / span) * 1000;
  const width = Math.max(1, ((end - start + 1) / span) * 1000);
  return <rect className="sequence-selection-range" x={x} y={.5} width={width} height={Math.max(1, height - 1)} />;
}

function positionFromPointer(clientX: number, element: HTMLElement, viewport: Viewport): number {
  const rect = element.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / Math.max(1, rect.width)));
  return Math.max(viewport.start, Math.min(viewport.end, Math.floor(viewport.start + ratio * (viewport.end - viewport.start + 1))));
}

function usePlotWidth<T extends HTMLElement>(ref: RefObject<T | null>): number {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const update = () => setWidth(Math.round(element.getBoundingClientRect().width));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}

function placeIntervals<T extends { start: number; end: number }>(intervals: T[], maxLanes = 3) {
  const laneEnds = Array(maxLanes).fill(0) as number[];
  const placed: (T & { lane: number })[] = [];
  let overflow = 0;
  for (const interval of [...intervals].sort((a, b) => a.start - b.start || a.end - b.end)) {
    const lane = laneEnds.findIndex((end) => end < interval.start);
    if (lane < 0) overflow += 1;
    else {
      laneEnds[lane] = interval.end;
      placed.push({ ...interval, lane });
    }
  }
  return { placed, overflow };
}

function topologyInterval(interval: SequenceOverviewFeatureInterval, index: number): OverviewInterval {
  const category = normalizeTopologyCategory(interval.feature_type, interval.description);
  return {
    id: interval.feature_id ?? `topology-${interval.start}-${interval.end}-${index}`,
    label: interval.description ?? formatTermLabel(interval.feature_type),
    start: interval.start,
    end: interval.end,
    source: interval.source,
    kind: formatTermLabel(interval.feature_type),
    category,
  };
}

function functionalInterval(interval: SequenceOverviewFeatureInterval, index: number): OverviewInterval {
  const category = normalizeFunctionalCategory(interval.feature_type, interval.description);
  return {
    id: interval.feature_id ?? `functional-${interval.start}-${interval.end}-${index}`,
    label: interval.description ?? formatTermLabel(interval.feature_type),
    start: interval.start,
    end: interval.end,
    source: interval.source,
    kind: formatTermLabel(interval.feature_type),
    category,
  };
}

function pfamInterval(interval: SequenceOverviewPfamInterval): OverviewInterval {
  const category = normalizePfamCategory(interval.pfam_type, interval.pfam_id, interval.pfam_accession);
  return {
    id: interval.pfam_accession,
    label: interval.description ?? interval.pfam_id ?? interval.pfam_accession,
    start: interval.start,
    end: interval.end,
    source: interval.source,
    kind: interval.pfam_type ? formatTermLabel(interval.pfam_type) : "Pfam domain",
    category,
  };
}

function TrackLegend({ categories, styles }: { categories: NormalizedTrackCategory[]; styles: Map<string, TrackCategoryStyle> }) {
  const unique = [...new Map(categories.map((category) => [category.key, category])).values()];
  if (!unique.length) return null;
  return <ul className="sequence-track-legend" aria-label="Track color legend">
    {unique.map((category) => {
      const style = styles.get(category.key);
      return <li key={category.key}><i style={{ backgroundColor: style?.color }} className={style && style.patternIndex > 0 ? `pattern-${(style.patternIndex % 3) + 1}` : ""} /><span>{category.label}</span></li>;
    })}
  </ul>;
}

function IntervalTrack({ label, symbol, intervals, viewport, selection, onSelect, className, styles }: {
  label: string;
  symbol: string;
  intervals: OverviewInterval[];
  viewport: Viewport;
  selection: SiteSelection;
  onSelect: (selection: SiteSelection) => void;
  className: string;
  styles: Map<string, TrackCategoryStyle>;
}) {
  const tooltipId = useId();
  const [active, setActive] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);
  const clipped = intervals.filter((item) => item.start <= viewport.end && item.end >= viewport.start);
  const { placed, overflow } = placeIntervals(clipped);
  const itemKey = (item: OverviewInterval) => `${item.id}-${item.start}-${item.end}`;
  const activeItem = clipped.find((item) => itemKey(item) === active) ?? null;
  const patterns = [...new Map(clipped.flatMap((item) => {
    const style = styles.get(item.category.key);
    return style && style.patternIndex > 0 ? [[`${style.color}-${style.patternIndex}`, style] as const] : [];
  })).values()];
  const patternPrefix = `${className}-${tooltipId.replace(/:/g, "")}`;

  function activate(item: OverviewInterval, sticky: boolean) {
    const key = itemKey(item);
    setActive(key);
    if (sticky) setPinned((current) => current === key ? null : key);
  }

  function selectItem(item: OverviewInterval) {
    const next = item.start === item.end
      ? { start: item.start, end: item.end, site: item.start }
      : { start: item.start, end: item.end };
    const key = itemKey(item);
    if (sameSelection(selection, next)) {
      setPinned(null);
      setActive(null);
      onSelect(null);
      return;
    }
    setPinned(key);
    setActive(key);
    onSelect(next);
  }

  return <div className={`sequence-track-block ${className}`}>
    <div className="sequence-track-row">
      <div className="sequence-track-label"><span aria-hidden="true">{symbol}</span> {label}</div>
      <div className="sequence-track-plot">
        <svg viewBox="0 0 1000 66" preserveAspectRatio="none" role="group" aria-label={`Interactive ${label} track with ${clipped.length} annotations in view`}>
          <defs>{patterns.map((style) => <pattern key={`${style.color}-${style.patternIndex}`} id={`${patternPrefix}-${style.patternIndex}-${style.color.slice(1)}`} width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill={style.color} /><path d="M-2 2 L2 -2 M0 8 L8 0 M6 10 L10 6" stroke={style.textColor} strokeOpacity=".35" strokeWidth="2" /></pattern>)}</defs>
          {placed.map((item) => {
            const key = itemKey(item);
            const left = Math.max(item.start, viewport.start);
            const right = Math.min(item.end, viewport.end);
            const x = intervalPosition(left, viewport.start, viewport.end);
            const width = Math.max(.35, ((right - left + 1) / (viewport.end - viewport.start + 1)) * 100);
            const description = `${item.category.label}; ${item.label}; canonical ${item.start}–${item.end}; ${item.source}`;
            const style = styles.get(item.category.key);
            const fill = style?.patternIndex ? `url(#${patternPrefix}-${style.patternIndex}-${style.color.slice(1)})` : style?.color;
            return <g
              key={key}
              role="button"
              tabIndex={0}
              aria-label={description}
              aria-describedby={active === key ? tooltipId : undefined}
              onPointerEnter={() => activate(item, false)}
              onPointerLeave={() => setActive(pinned)}
              onFocus={() => activate(item, false)}
              onBlur={() => setActive(pinned)}
              onClick={() => selectItem(item)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  selectItem(item);
                } else if (event.key === "Escape") {
                  setPinned(null);
                  setActive(null);
                  onSelect(null);
                }
              }}
            >
              <rect x={x * 10} y={5 + item.lane * 20} width={width * 10} height={14} rx={2} vectorEffect="non-scaling-stroke" fill={fill} stroke={style?.color} />
              {width > 14 && <text x={x * 10 + 7} y={15 + item.lane * 20} fill={style?.textColor}>{item.label}</text>}
            </g>;
          })}
          <SequenceSelectionOverlay selection={selection} viewport={viewport} height={66} />
        </svg>
        {activeItem && <output id={tooltipId} className="sequence-annotation-tooltip"><strong>{activeItem.category.label}</strong><span>{activeItem.label}</span><span>Canonical {activeItem.start.toLocaleString()}–{activeItem.end.toLocaleString()} · {activeItem.source}</span></output>}
        {overflow > 0 && <span className="sequence-lane-overflow">+{overflow} overlapping annotations</span>}
        {!clipped.length && <span className="sequence-track-empty">No annotations in this range</span>}
      </div>
    </div>
    <TrackLegend categories={intervals.map((item) => item.category)} styles={styles} />
  </div>;
}

type SecondaryStructureVisual = {
  id: string;
  start: number;
  end: number;
  featureType: SequenceOverviewSecondaryStructureInterval["feature_type"];
  label: string;
  source: "UniProt";
};

function secondaryStructureInterval(interval: SequenceOverviewSecondaryStructureInterval, index: number): SecondaryStructureVisual {
  return {
    id: interval.feature_id ?? `secondary-${interval.feature_type}-${interval.start}-${interval.end}-${index}`,
    start: interval.start,
    end: interval.end,
    featureType: interval.feature_type,
    label: interval.description ?? interval.feature_type,
    source: interval.source,
  };
}

function SecondaryStructureTrack({ intervals, viewport, selection, onSelect }: {
  intervals: SecondaryStructureVisual[];
  viewport: Viewport;
  selection: SiteSelection;
  onSelect: (selection: SiteSelection) => void;
}) {
  const tooltipId = useId();
  const [active, setActive] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);
  const visible = intervals.filter((item) => item.start <= viewport.end && item.end >= viewport.start);
  const { placed, overflow } = placeIntervals(visible, 3);
  const activeItem = visible.find((item) => item.id === active) ?? null;

  function activate(item: SecondaryStructureVisual, sticky: boolean) {
    setActive(item.id);
    if (sticky) setPinned((current) => current === item.id ? null : item.id);
  }

  function selectItem(item: SecondaryStructureVisual) {
    const next = item.start === item.end
      ? { start: item.start, end: item.end, site: item.start }
      : { start: item.start, end: item.end };
    if (sameSelection(selection, next)) {
      setPinned(null);
      setActive(null);
      onSelect(null);
      return;
    }
    setPinned(item.id);
    setActive(item.id);
    onSelect(next);
  }

  return <div className="sequence-track-block sequence-secondary-structure">
    <div className="sequence-track-row">
      <div className="sequence-track-label"><span aria-hidden="true">⌒</span> Secondary structure</div>
      <div className="sequence-track-plot">
        <svg viewBox="0 0 1000 66" preserveAspectRatio="none" role="group" aria-label={`Interactive secondary-structure track with ${visible.length} UniProt annotations in view`}>
          {placed.map((item) => {
            const left = Math.max(item.start, viewport.start);
            const right = Math.min(item.end, viewport.end);
            const x = intervalPosition(left, viewport.start, viewport.end) * 10;
            const width = Math.max(4, ((right - left + 1) / (viewport.end - viewport.start + 1)) * 1000);
            const y = 10 + item.lane * 18;
            const key = item.id;
            const description = `${item.featureType}; ${item.label}; canonical ${item.start}–${item.end}; UniProt secondary-structure annotation`;
            const label = item.featureType === "Beta strand" ? "Beta strand" : item.featureType;
            const tip = Math.min(15, Math.max(3, width * .35));
            return <g key={key} className={`secondary-structure-mark secondary-${item.featureType.toLowerCase().replace(/\s+/g, "-")}`} role="button" tabIndex={0} aria-label={description} aria-describedby={active === key ? tooltipId : undefined} onPointerEnter={() => activate(item, false)} onPointerLeave={() => setActive(pinned)} onFocus={() => activate(item, false)} onBlur={() => setActive(pinned)} onClick={() => selectItem(item)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectItem(item); } else if (event.key === "Escape") { setPinned(null); setActive(null); onSelect(null); } }}>
              {item.featureType === "Helix" && <rect className="secondary-helix-shape" x={x} y={y} width={width} height="12" rx="6" />}
              {item.featureType === "Beta strand" && <path className="secondary-beta-shape" d={`M ${x} ${y} L ${x + Math.max(1, width - tip)} ${y} L ${x + width} ${y + 6} L ${x + Math.max(1, width - tip)} ${y + 12} L ${x} ${y + 12} Z`} />}
              {item.featureType === "Turn" && <path className="secondary-turn-shape" d={`M ${x} ${y + 9} Q ${x + width * .3} ${y - 2} ${x + width * .5} ${y + 9} T ${x + width} ${y + 9}`} />}
              {width > 72 && <text x={x + Math.min(8, width * .12)} y={y + 8.5}>{label}</text>}
            </g>;
          })}
          <SequenceSelectionOverlay selection={selection} viewport={viewport} height={66} />
        </svg>
        {activeItem && <output id={tooltipId} className="sequence-annotation-tooltip"><strong>{activeItem.featureType}</strong><span>{activeItem.label}</span><span>Canonical {activeItem.start.toLocaleString()}–{activeItem.end.toLocaleString()} · UniProt</span><small>Activate to select this canonical range.</small></output>}
        {overflow > 0 && <span className="sequence-lane-overflow">+{overflow} overlapping secondary-structure annotations</span>}
        {!visible.length && <span className="sequence-track-empty">No UniProt secondary-structure annotations in this range</span>}
      </div>
    </div>
    <ul className="sequence-track-legend sequence-secondary-legend" aria-label="Secondary structure shape legend"><li><i className="secondary-legend-glyph secondary-legend-helix" /><span>Helix · capsule</span></li><li><i className="secondary-legend-glyph secondary-legend-beta" /><span>Beta strand · C-terminal arrow</span></li><li><i className="secondary-legend-glyph secondary-legend-turn" /><span>Turn · loop segment</span></li><li><span>UniProt · canonical 1-based closed intervals</span></li></ul>
  </div>;
}

function JsdTrack({ bins, detail, viewport, selection }: { bins: SequenceOverviewBin[]; detail?: SiteResponse; viewport: Viewport; selection: SiteSelection }) {
  const detailed = (detail?.tracks.conservation ?? []).flatMap((item) => {
    const position = numberValue(item.position);
    const jsd = numberValue(item.jsd_conservation);
    return position === null || jsd === null ? [] : [{ start: position, end: position, position, mean: jsd, min: jsd, max: jsd }];
  });
  const summary = bins.filter((bin) => bin.end >= viewport.start && bin.start <= viewport.end && bin.conservation.jsd_mean !== null).map((bin) => ({
    start: bin.start,
    end: bin.end,
    position: (bin.start + bin.end) / 2,
    mean: bin.conservation.jsd_mean!,
    min: bin.conservation.jsd_min!,
    max: bin.conservation.jsd_max!,
  }));
  const points = detailed.length ? detailed : summary;
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const active = activeIndex === null ? null : points[activeIndex] ?? null;
  const x = (position: number) => intervalPosition(position, viewport.start, viewport.end) * 10;
  const y = (value: number) => 48 - Math.max(0, Math.min(1, value)) * 38;
  const ribbon = points.length > 1 ? `${points.map((point, index) => `${index ? "L" : "M"} ${x(point.position)} ${y(point.max)}`).join(" ")} ${[...points].reverse().map((point) => `L ${x(point.position)} ${y(point.min)}`).join(" ")} Z` : "";
  const line = points.map((point, index) => `${index ? "L" : "M"} ${x(point.position)} ${y(point.mean)}`).join(" ");
  function inspectAt(position: number) {
    if (!points.length) return;
    let closest = 0;
    for (let index = 1; index < points.length; index += 1) {
      if (Math.abs(points[index].position - position) < Math.abs(points[closest].position - position)) closest = index;
    }
    setActiveIndex(closest);
  }

  function onKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (!points.length) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "Home" || event.key === "End") {
      event.preventDefault();
      const current = activeIndex ?? 0;
      const next = event.key === "Home" ? 0 : event.key === "End" ? points.length - 1 : Math.max(0, Math.min(points.length - 1, current + (event.key === "ArrowLeft" ? -1 : 1)));
      setActiveIndex(next);
    } else if (event.key === "Escape") {
      setActiveIndex(null);
    }
  }

  return <div className="sequence-track-row sequence-jsd-row">
    <div className="sequence-track-label">∿ JSD · 0–1</div>
    <div className="sequence-signal-plot" role="slider" tabIndex={0} aria-label={`JSD conservation, fixed zero to one scale. ${detailed.length ? "Exact residue values" : "Bin summaries"} are available on hover or keyboard focus.`} aria-valuemin={viewport.start} aria-valuemax={viewport.end} aria-valuenow={active ? Math.round(active.position) : viewport.start} aria-valuetext={active ? (detailed.length ? `Residue ${active.start}; JSD ${active.mean.toFixed(4)}` : `Residues ${active.start} to ${active.end}; mean JSD ${active.mean.toFixed(4)}, range ${active.min.toFixed(4)} to ${active.max.toFixed(4)}`) : "No JSD observation inspected"} onPointerMove={(event) => inspectAt(positionFromPointer(event.clientX, event.currentTarget, viewport))} onPointerLeave={() => setActiveIndex(null)} onFocus={() => setActiveIndex((current) => current ?? 0)} onBlur={() => setActiveIndex(null)} onKeyDown={onKeyDown}>
      <svg viewBox="0 0 1000 56" preserveAspectRatio="none" role="img" aria-label={`JSD conservation on a fixed zero to one scale; ${points.length} ${detailed.length ? "residue" : "summary"} observations in view`}>
        <line className="detail-jsd-guide" x1="0" x2="1000" y1="10" y2="10" />
        <line className="detail-jsd-guide" x1="0" x2="1000" y1="29" y2="29" />
        <line className="detail-jsd-guide" x1="0" x2="1000" y1="48" y2="48" />
        {ribbon && <path className="detail-jsd-band" d={ribbon} />}
        {line && <path className="detail-jsd-line" d={line} />}
        <SequenceSelectionOverlay selection={selection} viewport={viewport} height={56} />
      </svg>
      {active && <output className="sequence-annotation-tooltip jsd-annotation-tooltip"><strong>{detailed.length ? `Residue ${active.start.toLocaleString()}` : `JSD summary · residues ${active.start.toLocaleString()}–${active.end.toLocaleString()}`}</strong><span>JSD {detailed.length ? active.mean.toFixed(4) : `mean ${active.mean.toFixed(4)}`}</span>{!detailed.length && <span>Range {active.min.toFixed(4)}–{active.max.toFixed(4)}</span>}<small>Jensen–Shannon divergence on the fixed 0–1 conservation scale.</small></output>}
      {!points.length && <span className="sequence-track-empty">No JSD observations in this range</span>}
    </div>
  </div>;
}

type PtmDisplayMark = {
  start: number;
  end: number;
  totalCount: number;
  occupiedSiteCount: number;
  types: Array<{ ptmType: string; count: number }>;
  residue?: string | null;
};

function ptmGlyph(context: CanvasRenderingContext2D, x: number, y: number, radius: number, type: string) {
  const normalized = type.toLowerCase();
  context.beginPath();
  if (normalized.includes("glyco")) {
    context.moveTo(x, y - radius); context.lineTo(x + radius, y); context.lineTo(x, y + radius); context.lineTo(x - radius, y); context.closePath();
  } else if (normalized.includes("ubiquitin") || normalized.includes("sumo")) {
    for (let index = 0; index < 6; index += 1) {
      const angle = -Math.PI / 2 + index * Math.PI / 3;
      const pointX = x + Math.cos(angle) * radius;
      const pointY = y + Math.sin(angle) * radius;
      if (index) context.lineTo(pointX, pointY); else context.moveTo(pointX, pointY);
    }
    context.closePath();
  } else if (normalized.includes("lipid")) {
    context.moveTo(x, y - radius); context.lineTo(x + radius, y + radius); context.lineTo(x - radius, y + radius); context.closePath();
  } else if (normalized.includes("acetyl") || normalized.includes("methyl")) {
    context.rect(x - radius, y - radius, radius * 2, radius * 2);
  } else if (normalized.includes("proteol") || normalized.includes("other")) {
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.moveTo(x + radius * .35, y); context.arc(x, y, radius * .35, 0, Math.PI * 2);
  } else {
    context.arc(x, y, radius, 0, Math.PI * 2);
  }
  context.fill();
  context.stroke();
}

const PtmTrack = memo(function PtmTrack({ sites, allTypes, styles, viewport, selection, onSelect, onSelectRange }: {
  sites: SequenceOverviewPtmSite[];
  allTypes: NormalizedTrackCategory[];
  styles: Map<string, TrackCategoryStyle>;
  viewport: Viewport;
  selection: SiteSelection;
  onSelect: (selection: SiteSelection) => void;
  onSelectRange: (selection: SiteSelection) => void;
}) {
  const tooltipId = useId();
  const plotRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const plotWidth = usePlotWidth(plotRef);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [pinnedKey, setPinnedKey] = useState<string | null>(null);
  const overview = viewport.end - viewport.start + 1 > MAX_DETAIL_WINDOW;
  const visibleSites = useMemo<PtmDisplayMark[]>(() => sites.filter((site) => site.position >= viewport.start && site.position <= viewport.end).map((site) => ({
    start: site.position, end: site.position, totalCount: site.total_count, occupiedSiteCount: 1, residue: site.residue,
    types: site.types.map((type) => ({ ptmType: type.ptm_type, count: type.count })),
  })), [sites, viewport]);
  const clustered = useMemo(() => aggregatePtmMarks(sites.map((site) => ({
    position: site.position, totalCount: site.total_count, types: site.types.map((type) => ({ ptmType: type.ptm_type, count: type.count })),
  })), viewport, sequenceMarkBudget(plotWidth)), [plotWidth, sites, viewport]);
  const marks = (overview ? clustered : visibleSites).filter((mark) => mark.totalCount > 0);
  const active = marks.find((mark) => `${mark.start}-${mark.end}` === activeKey) ?? null;
  const visiblePtmRecords = marks.reduce((total, mark) => total + mark.totalCount, 0);
  const visiblePtmSites = marks.reduce((total, mark) => total + mark.occupiedSiteCount, 0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.round(rect.width * ratio));
      canvas.height = Math.max(1, Math.round(rect.height * ratio));
      const context = canvas.getContext("2d");
      if (!context) return;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.clearRect(0, 0, rect.width, rect.height);
      const baseline = rect.height - 12;
      context.strokeStyle = "#d0e2c0"; context.lineWidth = 1;
      context.beginPath(); context.moveTo(0, baseline + .5); context.lineTo(rect.width, baseline + .5); context.stroke();
      for (const mark of marks) {
        const x = ((mark.start + mark.end) / 2 - viewport.start + .5) / Math.max(1, viewport.end - viewport.start + 1) * rect.width;
        const radius = Math.max(3.5, Math.min(11, 3 + Math.log1p(mark.totalCount) * 2.1));
        const type = mark.types[0]?.ptmType ?? "other";
        const category = normalizePtmCategory(type);
        context.fillStyle = styles.get(category.key)?.color ?? "#f59c7c";
        context.strokeStyle = "#172230"; context.lineWidth = 1.1;
        ptmGlyph(context, x, baseline - radius - 3, radius, type);
        if (overview && mark.types.length > 1) {
          context.fillStyle = "#172230"; context.font = "700 10px Inter, system-ui, sans-serif"; context.textAlign = "center";
          context.fillText(`+${mark.types.length - 1}`, x, Math.max(10, baseline - radius * 2 - 5));
        }
      }
      if (selection && selection.site === undefined && selection.end >= viewport.start && selection.start <= viewport.end) {
        const left = Math.max(selection.start, viewport.start);
        const right = Math.min(selection.end, viewport.end);
        const x = ((left - viewport.start) / Math.max(1, viewport.end - viewport.start + 1)) * rect.width;
        const width = ((right - left + 1) / Math.max(1, viewport.end - viewport.start + 1)) * rect.width;
        context.fillStyle = "rgb(244 114 84 / 8%)"; context.fillRect(x, 0, width, rect.height);
        context.strokeStyle = "rgb(244 114 84 / 68%)"; context.lineWidth = 1; context.strokeRect(x + .5, .5, Math.max(0, width - 1), Math.max(0, rect.height - 1));
      } else if (selection?.site && selection.site >= viewport.start && selection.site <= viewport.end) {
        const x = ((selection.site - viewport.start + .5) / Math.max(1, viewport.end - viewport.start + 1)) * rect.width;
        context.strokeStyle = "#f47254"; context.lineWidth = 2; context.setLineDash([4, 3]);
        context.beginPath(); context.moveTo(x, 0); context.lineTo(x, rect.height); context.stroke(); context.setLineDash([]);
      }
    };
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [marks, overview, selection, styles, viewport]);

  function nearest(position: number) {
    return marks.reduce<PtmDisplayMark | null>((best, mark) => !best || Math.abs((mark.start + mark.end) / 2 - position) < Math.abs((best.start + best.end) / 2 - position) ? mark : best, null);
  }

  function activate(mark: PtmDisplayMark | null, select = false) {
    if (!mark) return;
    const key = `${mark.start}-${mark.end}`;
    setActiveKey(key);
    if (!select) return;
    const next = overview ? { start: mark.start, end: mark.end } : { start: mark.start, end: mark.end, site: mark.start };
    if (sameSelection(selection, next)) {
      setPinnedKey(null);
      setActiveKey(null);
      (overview ? onSelectRange : onSelect)(null);
      return;
    }
    setPinnedKey(key);
    (overview ? onSelectRange : onSelect)(next);
  }

  function keyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (!marks.length) return;
    const currentIndex = Math.max(0, marks.findIndex((mark) => `${mark.start}-${mark.end}` === activeKey));
    if (event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "Home" || event.key === "End") {
      event.preventDefault(); event.stopPropagation();
      const next = event.key === "Home" ? 0 : event.key === "End" ? marks.length - 1 : Math.max(0, Math.min(marks.length - 1, currentIndex + (event.key === "ArrowLeft" ? -1 : 1)));
      activate(marks[next]);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault(); event.stopPropagation(); activate(marks[currentIndex], true);
    } else if (event.key === "Escape") { setPinnedKey(null); setActiveKey(null); onSelect(null); }
  }

  return <div className="sequence-track-block sequence-ptm-block">
    <div className="sequence-track-row sequence-ptm-row">
      <div className="sequence-track-label">▲ PTM sites</div>
      <div
        ref={plotRef}
        className="sequence-canvas-plot sequence-ptm-plot"
        role="slider"
        tabIndex={0}
        aria-label={overview ? "Aggregated PTM records by canonical range. Use arrows to inspect clusters and Enter to zoom into an exact range." : "Exact PTM sites by canonical position. Use arrows to inspect sites and Enter to pin."}
        aria-valuemin={viewport.start}
        aria-valuemax={viewport.end}
        aria-valuenow={active ? Math.round((active.start + active.end) / 2) : viewport.start}
        aria-valuetext={active ? `${overview ? `Residues ${active.start} to ${active.end}` : `Residue ${active.start}`}; ${active.totalCount} dbPTM records across ${active.occupiedSiteCount} site${active.occupiedSiteCount === 1 ? "" : "s"}` : "No PTM mark inspected"}
        aria-describedby={active ? tooltipId : undefined}
        onPointerMove={(event) => activate(nearest(positionFromPointer(event.clientX, event.currentTarget, viewport)))}
        onPointerLeave={() => setActiveKey(pinnedKey)}
        onClick={(event) => activate(nearest(positionFromPointer(event.clientX, event.currentTarget, viewport)), true)}
        onFocus={() => activate(active ?? marks[0] ?? null)}
        onBlur={() => setActiveKey(pinnedKey)}
        onKeyDown={keyDown}
      >
        <canvas ref={canvasRef} aria-hidden="true" />
        {overview && <span className="sequence-overview-status">Aggregated {visiblePtmRecords.toLocaleString()} records across {visiblePtmSites.toLocaleString()} sites</span>}
        {active && <output id={tooltipId} className="sequence-annotation-tooltip"><strong>{overview ? `PTM cluster · residues ${active.start}–${active.end}` : `PTM at ${("residue" in active ? active.residue : null) ?? "?"}${active.start}`}</strong>{active.types.map((type) => <span key={type.ptmType}>{formatTermLabel(type.ptmType)} × {type.count.toLocaleString()}</span>)}<span>{active.totalCount.toLocaleString()} dbPTM record{active.totalCount === 1 ? "" : "s"} across {active.occupiedSiteCount.toLocaleString()} canonical site{active.occupiedSiteCount === 1 ? "" : "s"}</span>{overview && <small>Activate to zoom into this exact canonical range.</small>}</output>}
        {!marks.length && <span className="sequence-track-empty">No PTM records in this range</span>}
      </div>
    </div>
    <TrackLegend categories={allTypes} styles={styles} />
  </div>;
});

const VariantBars = memo(function VariantBars({ totalCounts, plpCounts, viewport, selection, onSelect, onSelectRange }: {
  totalCounts: number[];
  plpCounts: number[];
  viewport: Viewport;
  selection: SiteSelection;
  onSelect: (selection: SiteSelection) => void;
  onSelectRange: (selection: SiteSelection) => void;
}) {
  const tooltipId = useId();
  const plotRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const plotWidth = usePlotWidth(plotRef);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [pinnedKey, setPinnedKey] = useState<string | null>(null);
  const overview = viewport.end - viewport.start + 1 > MAX_DETAIL_WINDOW;
  const marks = useMemo(() => aggregateVariantMarks(totalCounts, plpCounts, viewport, overview ? sequenceMarkBudget(plotWidth) : viewport.end - viewport.start + 1).filter((mark) => mark.totalCount > 0), [overview, plotWidth, plpCounts, totalCounts, viewport]);
  const active = marks.find((mark) => `${mark.start}-${mark.end}` === activeKey) ?? null;
  const maxCount = Math.max(1, ...marks.map((mark) => mark.totalCount));
  const visibleVariants = marks.reduce((total, mark) => total + mark.totalCount, 0);
  const visibleVariantSites = marks.reduce((total, mark) => total + mark.occupiedSiteCount, 0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.round(rect.width * ratio));
      canvas.height = Math.max(1, Math.round(rect.height * ratio));
      const context = canvas.getContext("2d");
      if (!context) return;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.clearRect(0, 0, rect.width, rect.height);
      const baseline = rect.height - 10;
      context.strokeStyle = "#d0e2c0"; context.beginPath(); context.moveTo(0, baseline + .5); context.lineTo(rect.width, baseline + .5); context.stroke();
      const span = viewport.end - viewport.start + 1;
      const slot = rect.width / Math.max(1, overview ? sequenceMarkBudget(plotWidth) : span);
      const barWidth = Math.max(.9, Math.min(16, slot * .68));
      for (const mark of marks) {
        const height = (Math.log1p(mark.totalCount) / Math.log1p(maxCount)) * Math.max(12, baseline - 7);
        const redHeight = height * (mark.clinvarPlpCount / mark.totalCount);
        const x = (((mark.start + mark.end) / 2 - viewport.start + .5) / span) * rect.width - barWidth / 2;
        context.fillStyle = VARIANT_ALL_COLOR;
        context.fillRect(x, baseline - (height - redHeight), barWidth, height - redHeight);
        if (redHeight > 0) { context.fillStyle = VARIANT_PLP_COLOR; context.fillRect(x, baseline - height, barWidth, redHeight); }
      }
      if (selection && selection.site === undefined && selection.end >= viewport.start && selection.start <= viewport.end) {
        const left = Math.max(selection.start, viewport.start);
        const right = Math.min(selection.end, viewport.end);
        const x = ((left - viewport.start) / span) * rect.width;
        const width = ((right - left + 1) / span) * rect.width;
        context.fillStyle = "rgb(244 114 84 / 8%)"; context.fillRect(x, 0, width, rect.height);
        context.strokeStyle = "rgb(244 114 84 / 68%)"; context.lineWidth = 1; context.strokeRect(x + .5, .5, Math.max(0, width - 1), Math.max(0, rect.height - 1));
      } else if (selection?.site && selection.site >= viewport.start && selection.site <= viewport.end) {
        const x = ((selection.site - viewport.start + .5) / span) * rect.width;
        context.strokeStyle = "#f47254"; context.lineWidth = 2; context.setLineDash([4, 3]); context.beginPath(); context.moveTo(x, 0); context.lineTo(x, rect.height); context.stroke(); context.setLineDash([]);
      }
    };
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [marks, maxCount, overview, plotWidth, selection, viewport]);

  function nearest(position: number) {
    return marks.reduce<typeof marks[number] | null>((best, mark) => !best || Math.abs((mark.start + mark.end) / 2 - position) < Math.abs((best.start + best.end) / 2 - position) ? mark : best, null);
  }

  function activate(mark: typeof marks[number] | null, select = false) {
    if (!mark) return;
    const key = `${mark.start}-${mark.end}`;
    setActiveKey(key);
    if (!select) return;
    const next = overview ? { start: mark.start, end: mark.end } : { start: mark.start, end: mark.start, site: mark.start };
    if (sameSelection(selection, next)) {
      setPinnedKey(null);
      setActiveKey(null);
      (overview ? onSelectRange : onSelect)(null);
      return;
    }
    setPinnedKey(key);
    (overview ? onSelectRange : onSelect)(next);
  }

  function keyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (!marks.length) return;
    const current = Math.max(0, marks.findIndex((mark) => `${mark.start}-${mark.end}` === activeKey));
    if (event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "Home" || event.key === "End") {
      event.preventDefault(); event.stopPropagation();
      const next = event.key === "Home" ? 0 : event.key === "End" ? marks.length - 1 : Math.max(0, Math.min(marks.length - 1, current + (event.key === "ArrowLeft" ? -1 : 1)));
      activate(marks[next]);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault(); event.stopPropagation(); activate(marks[current], true);
    } else if (event.key === "Escape") { setPinnedKey(null); setActiveKey(null); onSelect(null); }
  }

  return <div className="sequence-track-block sequence-variant-block">
    <div className="sequence-track-row sequence-variant-row">
      <div className="sequence-track-label">▥ Variant sites</div>
      <div
        ref={plotRef}
        className="sequence-canvas-plot sequence-variant-plot"
        role="slider"
        tabIndex={0}
        aria-label={overview ? "Aggregated canonical variant density by range. Use arrows to inspect bins and Enter to zoom into an exact canonical range. The mulberry segment is explicit ClinVar P/LP evidence presence, not consensus." : "Canonical variant count by residue. The mulberry segment is explicit ClinVar P/LP evidence presence, not consensus."}
        aria-valuemin={viewport.start}
        aria-valuemax={viewport.end}
        aria-valuenow={active ? Math.round((active.start + active.end) / 2) : viewport.start}
        aria-valuetext={active ? `${overview ? `Residues ${active.start} to ${active.end}` : `Residue ${active.start}`}; ${active.totalCount} unique canonical variants across ${active.occupiedSiteCount} occupied site${active.occupiedSiteCount === 1 ? "" : "s"}; ${active.clinvarPlpCount} with explicit ClinVar P/LP evidence` : "No variant mark inspected"}
        aria-describedby={active ? tooltipId : undefined}
        onPointerMove={(event) => activate(nearest(positionFromPointer(event.clientX, event.currentTarget, viewport)))}
        onPointerLeave={() => setActiveKey(pinnedKey)}
        onClick={(event) => activate(nearest(positionFromPointer(event.clientX, event.currentTarget, viewport)), true)}
        onFocus={() => activate(active ?? marks[0] ?? null)}
        onBlur={() => setActiveKey(pinnedKey)}
        onKeyDown={keyDown}
      >
        <canvas ref={canvasRef} aria-hidden="true" />
        {overview && <span className="sequence-overview-status">Aggregated {visibleVariants.toLocaleString()} variants across {visibleVariantSites.toLocaleString()} sites</span>}
        {active && <output id={tooltipId} className="sequence-annotation-tooltip"><strong>{overview ? `Variant density · residues ${active.start}–${active.end}` : `Residue ${active.start.toLocaleString()}`}</strong><span>{active.totalCount.toLocaleString()} unique canonical variant{active.totalCount === 1 ? "" : "s"} across {active.occupiedSiteCount.toLocaleString()} occupied site{active.occupiedSiteCount === 1 ? "" : "s"}</span><span>{active.clinvarPlpCount.toLocaleString()} with explicit ClinVar P/LP evidence</span><small>{overview ? "Activate to zoom into this exact canonical range. " : ""}Mulberry is evidence presence, not cross-disease consensus.</small></output>}
        {!marks.length && <span className="sequence-track-empty">No canonical variants in this range</span>}
      </div>
    </div>
    <ul className="sequence-track-legend" aria-label="Variant density legend"><li><i style={{ backgroundColor: VARIANT_ALL_COLOR }} /><span>All canonical variants</span></li><li><i style={{ backgroundColor: VARIANT_PLP_COLOR }} /><span>Explicit ClinVar P/LP evidence present</span></li></ul>
  </div>;
});

const StabilityTrack = memo(function StabilityTrack({ accession, bins, detail, viewport, selection, onSelect }: {
  accession: string;
  bins: StabilityOverviewBin[];
  detail: SiteResponse | undefined;
  viewport: Viewport;
  selection: SiteSelection;
  onSelect: (selection: SiteSelection) => void;
}) {
  const plotRef = useRef<HTMLDivElement>(null);
  const plotWidth = usePlotWidth(plotRef);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [pinnedKey, setPinnedKey] = useState<string | null>(null);
  const [siteDetail, setSiteDetail] = useState<{ kind: "idle" | "loading" | "error" | "ready"; data?: StabilitySiteDetailResponse; error?: string }>({ kind: "idle" });
  const siteDetailCache = useRef(new Map<number, StabilitySiteDetailResponse>());
  const y = (value: number) => 10 + (3 - Math.max(-3, Math.min(3, value))) / 6 * 80;
  const detailRows = (detail?.tracks.stability ?? []).flatMap((row) => {
    const values = [row.position, row.ddg_min, row.ddg_q25, row.ddg_median, row.ddg_q75, row.ddg_max].map(numberValue);
    if (values.some((value) => value === null)) return [];
    return [{
      key: String(values[0]), start: values[0]!, end: values[0]!, min: values[1]!, q25: values[2]!, median: values[3]!, q75: values[4]!, max: values[5]!,
      count: numberValue(row.distinct_substitution_count) ?? 0, variants: numberValue(row.genomic_variant_count) ?? 0,
    }];
  });
  const detailed = viewport.end - viewport.start + 1 <= MAX_DETAIL_WINDOW && detailRows.length > 0;
  const overviewPoints = useMemo(() => aggregateStabilityMarks(bins.map((bin) => ({
    start: bin.start, end: bin.end, observationCount: bin.observation_count, distinctSubstitutionCount: bin.distinct_substitution_count,
    min: bin.ddg_min, q25: bin.ddg_q25, median: bin.ddg_median, q75: bin.ddg_q75, max: bin.ddg_max,
  })), viewport, sequenceMarkBudget(plotWidth)).flatMap((mark, index) => mark.median === null || mark.min === null || mark.q25 === null || mark.q75 === null || mark.max === null ? [] : [{
    key: `overview-${index}-${mark.start}-${mark.end}`, start: mark.start, end: mark.end, min: mark.min, q25: mark.q25, median: mark.median, q75: mark.q75, max: mark.max,
    count: mark.distinctSubstitutionCount, variants: mark.observationCount,
  }]), [bins, plotWidth, viewport]);
  const points = detailed ? detailRows : overviewPoints;
  const plotted = points.map((point) => ({
    ...point,
    x: intervalPosition((point.start + point.end) / 2, viewport.start, viewport.end) * 10,
    y: y(point.median),
  }));
  const active = plotted.find((point) => point.key === activeKey) ?? null;
  const activePosition = detailed && active ? active.start : null;

  useEffect(() => { siteDetailCache.current.clear(); }, [accession]);

  useEffect(() => {
    if (activePosition === null) { setSiteDetail({ kind: "idle" }); return; }
    const cached = siteDetailCache.current.get(activePosition);
    if (cached) { setSiteDetail({ kind: "ready", data: cached }); return; }
    const controller = new AbortController();
    setSiteDetail({ kind: "loading" });
    getJson<StabilitySiteDetailResponse>(`/proteins/${encodeURIComponent(accession)}/stability/sites/${activePosition}`, controller.signal)
      .then((data) => { siteDetailCache.current.set(activePosition, data); setSiteDetail({ kind: "ready", data }); })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setSiteDetail({ kind: "error", error: error instanceof Error ? error.message : "Unable to load substitution details." });
      });
    return () => controller.abort();
  }, [accession, activePosition]);

  function nearestPoint(position: number) {
    return plotted.reduce<typeof plotted[number] | null>((best, candidate) => {
      if (!best) return candidate;
      const candidateDistance = Math.abs((candidate.start + candidate.end) / 2 - position);
      const bestDistance = Math.abs((best.start + best.end) / 2 - position);
      return candidateDistance < bestDistance ? candidate : best;
    }, null);
  }

  function pointAt(clientX: number, element: HTMLElement) {
    return nearestPoint(positionFromPointer(clientX, element, viewport));
  }

  function selectPoint(point: typeof plotted[number]) {
    const next = detailed ? { start: point.start, end: point.start, site: point.start } : { start: point.start, end: point.end };
    if (sameSelection(selection, next)) {
      setPinnedKey(null);
      setActiveKey(null);
      onSelect(null);
      return;
    }
    setPinnedKey(point.key);
    setActiveKey(point.key);
    onSelect(next);
  }

  function keyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (!plotted.length) return;
    const current = Math.max(0, plotted.findIndex((point) => point.key === activeKey));
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      const next = Math.max(0, Math.min(plotted.length - 1, current + (event.key === "ArrowLeft" ? -1 : 1)));
      setActiveKey(plotted[next].key);
    } else if (event.key === "Home" || event.key === "End") {
      event.preventDefault(); setActiveKey(plotted[event.key === "Home" ? 0 : plotted.length - 1].key);
    } else if ((event.key === "Enter" || event.key === " ") && active) {
      event.preventDefault(); selectPoint(active);
    } else if (event.key === "Escape") {
      event.preventDefault(); setPinnedKey(null); setActiveKey(null); onSelect(null);
    }
  }

  return <div className="sequence-track-block sequence-stability">
    <div className="sequence-track-row">
      <div className="sequence-track-label"><span aria-hidden="true">↕</span> Stability ΔΔG</div>
      <div ref={plotRef} className="sequence-track-plot stability-track-plot" role="slider" tabIndex={0} aria-label={`Interactive ThermoMPNN predicted ΔΔG distributions for canonical range ${viewport.start} to ${viewport.end}. Each mark shows median, IQR, and min–max; missing marks are omitted. Negative is predicted stabilizing and positive predicted destabilizing.`} aria-valuemin={viewport.start} aria-valuemax={viewport.end} aria-valuenow={active ? Math.round((active.start + active.end) / 2) : viewport.start} onPointerMove={(event) => setActiveKey(pointAt(event.clientX, event.currentTarget)?.key ?? null)} onPointerLeave={() => setActiveKey(pinnedKey)} onClick={(event) => { const point = pointAt(event.clientX, event.currentTarget); if (point) selectPoint(point); }} onFocus={() => setActiveKey((current) => current ?? plotted[0]?.key ?? null)} onBlur={() => setActiveKey(pinnedKey)} onKeyDown={keyDown}>
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none" role="img" aria-label={`ThermoMPNN predicted stability distributions in canonical range ${viewport.start} to ${viewport.end}; negative is predicted stabilizing and positive predicted destabilizing.`}>
          <line className="stability-zero-line" x1="0" x2="1000" y1={y(0)} y2={y(0)} />
          {[-3, 3].map((value) => <text key={value} className="stability-axis-label" x="4" y={y(value) + (value > 0 ? 8 : -3)}>{value > 0 ? "+3" : "−3"}</text>)}
          {plotted.map((point) => {
            const color = stabilityColor(point.median);
            const activePoint = active?.key === point.key;
            const boxTop = Math.min(y(point.q25), y(point.q75));
            const boxHeight = Math.max(1.2, Math.abs(y(point.q25) - y(point.q75)));
            return <g key={point.key} className={`stability-distribution${activePoint ? " is-active" : ""}`} style={{ color }}>
              <line className="stability-whisker" x1={point.x} x2={point.x} y1={y(point.min)} y2={y(point.max)} />
              <line className="stability-whisker-cap" x1={point.x - 4} x2={point.x + 4} y1={y(point.min)} y2={y(point.min)} />
              <line className="stability-whisker-cap" x1={point.x - 4} x2={point.x + 4} y1={y(point.max)} y2={y(point.max)} />
              <rect className="stability-iqr" x={point.x - 5} y={boxTop} width="10" height={boxHeight} />
              <line className="stability-median" x1={point.x - 7} x2={point.x + 7} y1={point.y} y2={point.y} />
            </g>;
          })}
          <SequenceSelectionOverlay selection={selection} viewport={viewport} height={100} />
        </svg>
        {!points.length && <span className="sequence-track-empty">No drawable ThermoMPNN predictions in this range</span>}
        {active && <output className="stability-hover-card" style={{ left: `${Math.max(12, Math.min(88, active.x / 10))}%` }}><div className="stability-hover-heading"><strong>{detailed ? `Residue ${active.start}` : `Residues ${active.start}–${active.end}`}</strong><span>{active.min.toFixed(3)} to {active.max.toFixed(3)} kcal/mol</span></div><p>Median {active.median >= 0 ? "+" : ""}{active.median.toFixed(3)} · IQR {active.q25.toFixed(3)} to {active.q75.toFixed(3)} · {active.count} distinct substitution{active.count === 1 ? "" : "s"}</p><small>Whisker = min–max; box = IQR; line = median. Predicted ΔΔG, not clinical evidence.</small>{detailed ? siteDetail.kind === "loading" ? <small>Loading substitutions…</small> : siteDetail.kind === "error" ? <small>{siteDetail.error}</small> : siteDetail.kind === "ready" && siteDetail.data ? <div className="stability-substitution-grid" role="table" aria-label={`ThermoMPNN substitutions at residue ${active.start}`}><span role="columnheader">Mutation</span><span role="columnheader">ΔΔG</span><span role="columnheader">Direction</span>{siteDetail.data.substitutions.map((item) => <span role="row" className="stability-substitution-row" key={item.substitution}><b>{item.substitution}</b><i>{item.ddg >= 0 ? "+" : ""}{item.ddg.toFixed(3)}</i><em style={{ color: stabilityColor(item.ddg) }}>{item.direction === "predicted_stabilizing" ? "Stabilizing" : item.direction === "predicted_destabilizing" ? "Destabilizing" : "Small change"}</em></span>)}</div> : null : <small>Activate this overview mark or zoom to 120 aa or less to inspect exact site substitutions.</small>}</output>}
      </div>
    </div>
    <ul className="sequence-track-legend" aria-label="Stability direction legend"><li><i className="stability-key stabilizing" /><span>Predicted stabilizing (≤ −0.5)</span></li><li><i className="stability-key small-change" /><span>Small predicted change</span></li><li><i className="stability-key destabilizing" /><span>Predicted destabilizing (≥ +0.5)</span></li></ul>
  </div>;
});

function CovalentTrack({ pairs, viewport, selection, onSelect }: {
  pairs: SequenceOverviewResponse["covalent_pairs"];
  viewport: Viewport;
  selection: SiteSelection;
  onSelect: (selection: SiteSelection) => void;
}) {
  const visible = pairs.map((pair, pairIndex) => ({ pair, pairIndex })).filter(({ pair }) => (pair.start_endpoint >= viewport.start && pair.start_endpoint <= viewport.end) || (pair.end_endpoint >= viewport.start && pair.end_endpoint <= viewport.end) || (pair.start_endpoint < viewport.start && pair.end_endpoint > viewport.end));
  const lanes = routeCovalentPairLanes(visible.map(({ pair }) => pair));
  const laneTotal = lanes.length ? Math.max(...lanes) + 1 : 1;
  const trackHeight = 34 + Math.max(0, laneTotal - 1) * 13;
  const baseline = trackHeight - 8;
  const allDisulfide = allCovalentPairsAreDisulfide(pairs);
  return <div className="sequence-track-block sequence-covalent-block"><div className="sequence-track-row sequence-covalent-row">
    <div className="sequence-track-label">⌁ Covalent bonds</div>
    <div className="sequence-track-plot">
      <svg style={{ height: `${trackHeight}px` }} viewBox={`0 0 1000 ${trackHeight}`} preserveAspectRatio="none" role="group" aria-label={`Interactive covalent-bond arc track with ${visible.length} pairs crossing this range`}>
        {visible.map(({ pair, pairIndex }, visibleIndex) => {
          const left = intervalPosition(Math.max(viewport.start, Math.min(pair.start_endpoint, pair.end_endpoint)), viewport.start, viewport.end);
          const right = intervalPosition(Math.min(viewport.end, Math.max(pair.start_endpoint, pair.end_endpoint)), viewport.start, viewport.end);
          const target = pair.start_endpoint >= viewport.start && pair.start_endpoint <= viewport.end ? pair.start_endpoint : pair.end_endpoint;
          const bondType = covalentBondLabel(pair.feature_type);
          const label = `${bondType}${pair.description ? `; ${pair.description}` : ""}; linked canonical endpoints ${pair.start_endpoint} and ${pair.end_endpoint}`;
          const color = covalentPairColor(pairIndex);
          const peak = baseline - 18 - lanes[visibleIndex] * 13;
          const leftX = left * 10;
          const rightX = right * 10;
          return <g key={`${pair.start_endpoint}-${pair.end_endpoint}-${pairIndex}`} role="button" tabIndex={0} aria-label={label} onClick={() => onSelect({ start: target, end: target, site: target })} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect({ start: target, end: target, site: target }); } }}><title>{label}</title><path className="covalent-connector" style={{ stroke: color }} d={`M ${leftX} ${baseline} Q ${(leftX + rightX) / 2} ${peak} ${rightX} ${baseline}`} />{pair.start_endpoint >= viewport.start && pair.start_endpoint <= viewport.end && <circle style={{ fill: color, stroke: color }} cx={intervalPosition(pair.start_endpoint, viewport.start, viewport.end) * 10} cy={baseline} r={5} />}{pair.end_endpoint >= viewport.start && pair.end_endpoint <= viewport.end && <circle style={{ fill: color, stroke: color }} cx={intervalPosition(pair.end_endpoint, viewport.start, viewport.end) * 10} cy={baseline} r={5} />}</g>;
        })}
        <SequenceSelectionOverlay selection={selection} viewport={viewport} height={trackHeight} />
      </svg>
      {!visible.length && <span className="sequence-track-empty">No linked endpoints in this range</span>}
    </div>
  </div>{visible.length > 0 && <ul className="sequence-track-legend covalent-pair-legend" aria-label="Covalent bond types and endpoint colors">{allDisulfide && <li className="covalent-type-summary"><span><strong>Disulfide bonds (S—S)</strong></span></li>}{visible.map(({ pair, pairIndex }) => <li key={`${pair.start_endpoint}-${pair.end_endpoint}-${pairIndex}`}><i style={{ backgroundColor: covalentPairColor(pairIndex) }} /><span>{!allDisulfide && <><strong>{covalentBondLabel(pair.feature_type)}</strong> · </>}{pair.start_endpoint} ↔ {pair.end_endpoint}</span></li>)}</ul>}</div>;
}

function RangeSelector({ viewport, length, onViewport }: { viewport: Viewport; length: number; onViewport: (viewport: Viewport) => void }) {
  type Drag = { pointerId: number; mode: "create" | "pan" | "start" | "end"; anchor: number; origin: Viewport; preview: Viewport };
  const railRef = useRef<HTMLDivElement>(null);
  const [drag, setDrag] = useState<Drag | null>(null);
  const shown = drag?.preview ?? viewport;
  const geometry = navigatorGeometry(shown, length);

  function pointerPosition(clientX: number) {
    const rect = railRef.current?.getBoundingClientRect();
    return rect ? fullLengthPosition(clientX, rect.left, rect.width, length) : 1;
  }

  function down(event: ReactPointerEvent<HTMLDivElement>) {
    const target = event.target as HTMLElement;
    const part = target.closest<HTMLElement>("[data-navigator-part]")?.dataset.navigatorPart;
    const mode: Drag["mode"] = part === "start" || part === "end" || part === "pan" ? part : "create";
    const anchor = pointerPosition(event.clientX);
    const preview = mode === "create" ? { start: anchor, end: anchor } : viewport;
    setDrag({ pointerId: event.pointerId, mode, anchor, origin: viewport, preview });
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function move(event: ReactPointerEvent<HTMLDivElement>) {
    if (!drag || drag.pointerId !== event.pointerId) return;
    const position = pointerPosition(event.clientX);
    let preview: Viewport;
    if (drag.mode === "create") {
      preview = { start: Math.min(drag.anchor, position), end: Math.max(drag.anchor, position) };
    } else if (drag.mode === "pan") {
      preview = panViewport(drag.origin, position - drag.anchor, length);
    } else {
      preview = resizeViewport(drag.origin, drag.mode, position, length, 2);
    }
    setDrag({ ...drag, preview });
  }

  function finish(event: ReactPointerEvent<HTMLDivElement>) {
    if (!drag || drag.pointerId !== event.pointerId) return;
    const next = drag.preview;
    setDrag(null);
    if (next.end - next.start + 1 >= 2) onViewport(next);
  }

  function keyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    const span = viewport.end - viewport.start + 1;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      const delta = Math.max(1, Math.round(span / 10)) * (event.key === "ArrowLeft" ? -1 : 1);
      onViewport(centeredViewport((viewport.start + viewport.end) / 2 + delta, span, length));
    } else if (event.key === "+" || event.key === "=") {
      event.preventDefault(); onViewport(centeredViewport((viewport.start + viewport.end) / 2, Math.max(MIN_VIEWPORT, Math.round(span * .7)), length));
    } else if (event.key === "-" || event.key === "_") {
      event.preventDefault(); onViewport(centeredViewport((viewport.start + viewport.end) / 2, Math.min(length, Math.round(span * 1.4)), length));
    } else if (event.key === "Home") { event.preventDefault(); onViewport({ start: 1, end: length }); }
  }

  return <div className="sequence-range-selector-row">
    <span>Full-length navigator · drag handles to resize or the window to pan</span>
    <div ref={railRef} className="sequence-range-selector" role="slider" tabIndex={0} aria-label={`Full canonical sequence 1 to ${length}; visible range ${viewport.start} to ${viewport.end}. Drag the handles to resize, drag the selected window to pan, drag empty rail to create a range; arrows pan; plus and minus zoom; Home or double click restores full length.`} aria-valuemin={1} aria-valuemax={length} aria-valuenow={Math.round((viewport.start + viewport.end) / 2)} onPointerDown={down} onPointerMove={move} onPointerUp={finish} onPointerCancel={() => setDrag(null)} onDoubleClick={() => onViewport({ start: 1, end: length })} onKeyDown={keyDown}>
      <i data-navigator-part="pan" style={{ left: `${geometry.leftPercent}%`, width: `${geometry.widthPercent}%` }}><button type="button" data-navigator-part="start" aria-label={`Resize visible range start, currently ${viewport.start}`} /><button type="button" data-navigator-part="end" aria-label={`Resize visible range end, currently ${viewport.end}`} /></i>
      <span className="navigator-start">1</span><span className="navigator-end">{length.toLocaleString()}</span>
    </div>
  </div>;
}

const ResidueGrid = memo(function ResidueGrid({ sequence, totalCounts, plpCounts, viewport, selection, onSelect }: {
  sequence: string;
  totalCounts: number[];
  plpCounts: number[];
  viewport: Viewport;
  selection: SiteSelection;
  onSelect: (position: number) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointerFrame = useRef<number | null>(null);
  const pendingPointerPosition = useRef<number | null>(null);
  const [metrics, setMetrics] = useState({ width: 1, height: 300, scrollTop: 0 });
  const [focusedPosition, setFocusedPosition] = useState(selection?.site ?? viewport.start);
  const columns = Math.max(1, Math.floor(metrics.width / RESIDUE_CELL_WIDTH));
  const rows = Math.ceil((viewport.end - viewport.start + 1) / columns);
  const totalHeight = rows * RESIDUE_CELL_HEIGHT;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const update = () => setMetrics((current) => ({ ...current, width: container.clientWidth, height: container.clientHeight }));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setFocusedPosition((current) => selection?.site ?? Math.max(viewport.start, Math.min(current, viewport.end)));
  }, [selection?.site, viewport.end, viewport.start]);

  useEffect(() => () => {
    if (pointerFrame.current !== null) window.cancelAnimationFrame(pointerFrame.current);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(metrics.width * ratio));
    canvas.height = Math.max(1, Math.round(metrics.height * ratio));
    canvas.style.width = `${metrics.width}px`;
    canvas.style.height = `${metrics.height}px`;
    canvas.style.top = `${metrics.scrollTop}px`;
    const context = canvas.getContext("2d");
    if (!context) return;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, metrics.width, metrics.height);
    context.font = "700 14px ui-monospace, SFMono-Regular, Menlo, monospace";
    context.textAlign = "center";
    context.textBaseline = "middle";
    const firstRow = Math.max(0, Math.floor(metrics.scrollTop / RESIDUE_CELL_HEIGHT) - 1);
    const lastRow = Math.min(rows - 1, Math.ceil((metrics.scrollTop + metrics.height) / RESIDUE_CELL_HEIGHT) + 1);
    const cellWidth = metrics.width / columns;
    for (let row = firstRow; row <= lastRow; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const index = row * columns + column;
        const position = viewport.start + index;
        if (position > viewport.end) break;
        const x = column * cellWidth;
        const y = row * RESIDUE_CELL_HEIGHT - metrics.scrollTop;
        const total = totalCounts[position - 1] ?? 0;
        const plp = plpCounts[position - 1] ?? 0;
        const bucket = variantCountBucket(total);
        context.fillStyle = bucket.color;
        context.fillRect(x + 1, y + 1, cellWidth - 2, RESIDUE_CELL_HEIGHT - 2);
        if (plp > 0) {
          context.fillStyle = "#c85e62";
          context.beginPath(); context.moveTo(x + cellWidth - 12, y + 1); context.lineTo(x + cellWidth - 1, y + 1); context.lineTo(x + cellWidth - 1, y + 12); context.closePath(); context.fill();
        }
        if (selection?.site === position || focusedPosition === position) {
          context.strokeStyle = selection?.site === position ? "#9b2226" : "#172230";
          context.lineWidth = selection?.site === position ? 3 : 2;
          context.strokeRect(x + 2, y + 2, cellWidth - 4, RESIDUE_CELL_HEIGHT - 4);
        }
        context.fillStyle = "#172230";
        context.fillText(sequence[position - 1] ?? "?", x + cellWidth / 2, y + 14);
        context.font = "600 9px ui-monospace, SFMono-Regular, Menlo, monospace";
        context.fillText(String(position), x + cellWidth / 2, y + 30);
        context.font = "700 14px ui-monospace, SFMono-Regular, Menlo, monospace";
      }
    }
  }, [columns, focusedPosition, metrics, plpCounts, rows, selection, sequence, totalCounts, viewport]);

  function positionAt(clientX: number, clientY: number) {
    const container = containerRef.current;
    if (!container) return null;
    const rect = container.getBoundingClientRect();
    const column = Math.max(0, Math.min(columns - 1, Math.floor((clientX - rect.left) / (metrics.width / columns))));
    const row = Math.max(0, Math.floor((clientY - rect.top + container.scrollTop) / RESIDUE_CELL_HEIGHT));
    const position = viewport.start + row * columns + column;
    return position <= viewport.end ? position : null;
  }

  function ensureVisible(position: number) {
    const container = containerRef.current;
    if (!container) return;
    const row = Math.floor((position - viewport.start) / columns);
    const top = row * RESIDUE_CELL_HEIGHT;
    if (top < container.scrollTop) container.scrollTop = top;
    else if (top + RESIDUE_CELL_HEIGHT > container.scrollTop + container.clientHeight) container.scrollTop = top + RESIDUE_CELL_HEIGHT - container.clientHeight;
  }

  function move(delta: number) {
    const next = Math.max(viewport.start, Math.min(viewport.end, focusedPosition + delta));
    setFocusedPosition(next); ensureVisible(next);
  }

  function schedulePointerFocus(position: number) {
    pendingPointerPosition.current = position;
    if (pointerFrame.current !== null) return;
    pointerFrame.current = window.requestAnimationFrame(() => {
      pointerFrame.current = null;
      const next = pendingPointerPosition.current;
      if (next !== null) setFocusedPosition((current) => current === next ? current : next);
    });
  }

  function keyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "ArrowUp" || event.key === "ArrowDown" || event.key === "Home" || event.key === "End") {
      event.preventDefault(); event.stopPropagation();
      if (event.key === "Home") { setFocusedPosition(viewport.start); ensureVisible(viewport.start); }
      else if (event.key === "End") { setFocusedPosition(viewport.end); ensureVisible(viewport.end); }
      else move(event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : event.key === "ArrowUp" ? -columns : columns);
    } else if (event.key === "Enter" || event.key === " ") { event.preventDefault(); event.stopPropagation(); onSelect(focusedPosition); }
  }

  const focusedTotal = totalCounts[focusedPosition - 1] ?? 0;
  const focusedPlp = plpCounts[focusedPosition - 1] ?? 0;
  return <div className="sequence-residue-block">
    <div className="sequence-residue-heading"><strong>Canonical residue map</strong><span>Virtualized · scroll inside this panel</span></div>
    <ul className="sequence-residue-legend" aria-label="Residue variant count legend">{variantCountBuckets().map((bucket) => <li key={bucket.key}><i style={{ backgroundColor: bucket.color }} /><span>{bucket.label}</span></li>)}<li><i className="plp-corner-key" /><span>Explicit ClinVar P/LP present</span></li></ul>
    <div
      ref={containerRef}
      className="sequence-residue-grid"
      role="grid"
      tabIndex={0}
      aria-label={`Canonical residues ${viewport.start} to ${viewport.end}, colored by unique canonical variant count. Use arrow keys to inspect and Enter to select.`}
      aria-rowcount={rows}
      aria-colcount={columns}
      onScroll={(event) => {
        const scrollTop = event.currentTarget.scrollTop;
        setMetrics((current) => current.scrollTop === scrollTop ? current : { ...current, scrollTop });
      }}
      onPointerMove={(event) => { const position = positionAt(event.clientX, event.clientY); if (position) schedulePointerFocus(position); }}
      onClick={(event) => { const position = positionAt(event.clientX, event.clientY); if (position) { setFocusedPosition(position); onSelect(position); } }}
      onFocus={() => ensureVisible(focusedPosition)}
      onKeyDown={keyDown}
    >
      <div className="sequence-residue-spacer" style={{ height: `${totalHeight}px` }}><canvas ref={canvasRef} aria-hidden="true" /></div>
    </div>
    <output className="sequence-residue-status" aria-live="polite"><strong>{sequence[focusedPosition - 1] ?? "?"}{focusedPosition.toLocaleString()}</strong><span>{focusedTotal.toLocaleString()} variant{focusedTotal === 1 ? "" : "s"} · {focusedPlp.toLocaleString()} with explicit ClinVar P/LP evidence</span></output>
  </div>;
});

export function SequenceExplorer({ accession, length, onSelectionChange }: { accession: string; length: number; onSelectionChange: (selection: SiteSelection) => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const search = searchParams.toString();
  const initialSelection = parsePinned(searchParams.get("site"), searchParams.get("range"), length);
  const initialViewport = { start: 1, end: length };
  const [viewport, setViewportState] = useState<Viewport>(initialViewport);
  const [draft, setDraft] = useState<Viewport>(initialViewport);
  const [enabled, setEnabled] = useState<VisualTrack[]>(TRACKS.map((track) => track.key));
  const [overview, setOverview] = useState<{ kind: "loading" | "error" | "ready"; data?: SequenceOverviewResponse; error?: string }>({ kind: "loading" });
  const [detail, setDetail] = useState<DetailState>({ kind: "idle" });
  const [selection, setSelection] = useState<SiteSelection>(initialSelection);
  const [siteEvidenceOpen, setSiteEvidenceOpen] = useState(Boolean(initialSelection?.site));
  const lastSiteRef = useRef<number | null>(initialSelection?.site ?? null);
  const detailSpan = viewport.end - viewport.start + 1;
  const stability = useMemo(() => stabilityOverviewFrom(overview.data), [overview.data]);

  const updateViewport = useCallback((next: Viewport) => {
    const bounded = boundedViewport(next.start, next.end, length);
    setViewportState(bounded);
    setDraft(bounded);
  }, [length]);

  useEffect(() => onSelectionChange(selection), [selection, onSelectionChange]);

  useEffect(() => {
    const next = parsePinned(searchParams.get("site"), searchParams.get("range"), length);
    setSelection((current) => sameSelection(current, next) ? current : next);
  }, [searchParams, length]);

  useEffect(() => {
    const site = selection?.site ?? null;
    if (site === lastSiteRef.current) return;
    lastSiteRef.current = site;
    setSiteEvidenceOpen(site !== null);
  }, [selection?.site]);

  useEffect(() => {
    const controller = new AbortController();
    setOverview({ kind: "loading" });
    getJson<SequenceOverviewResponse>(`/proteins/${encodeURIComponent(accession)}/sequence/overview?bins=${OVERVIEW_BINS}`, controller.signal)
      .then((data) => setOverview({ kind: "ready", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setOverview({ kind: "error", error: error instanceof Error ? error.message : "Unable to load the bounded sequence overview." });
      });
    return () => controller.abort();
  }, [accession]);

  useEffect(() => {
    const detailTracks = [enabled.includes("conservation") && "conservation", enabled.includes("stability") && stability.available && "stability"].filter(Boolean).join(",");
    if (!detailTracks || detailSpan > MAX_DETAIL_WINDOW) { setDetail({ kind: "idle" }); return; }
    const controller = new AbortController();
    const params = new URLSearchParams({ start: String(viewport.start), end: String(viewport.end), tracks: detailTracks });
    setDetail({ kind: "loading" });
    getJson<SiteResponse>(`/proteins/${encodeURIComponent(accession)}/sites?${params}`, controller.signal)
      .then((sites) => setDetail({ kind: "ready", sites }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDetail({ kind: "error", error: error instanceof Error ? error.message : "Unable to load residue-level conservation." });
      });
    return () => controller.abort();
  }, [accession, detailSpan, enabled, stability.available, viewport.end, viewport.start]);

  const writeSelection = useCallback((next: SiteSelection) => {
    const resolved = sameSelection(selection, next) ? null : next;
    setSelection(resolved);
    const params = new URLSearchParams(search);
    params.delete("site");
    params.delete("range");
    if (resolved?.site) params.set("site", String(resolved.site));
    else if (resolved) params.set("range", `${resolved.start}-${resolved.end}`);
    router.replace(`${pathname}${params.size ? `?${params}` : ""}`, { scroll: false });
  }, [pathname, router, search, selection]);

  const selectOverviewRange = useCallback((next: SiteSelection) => {
    const clearing = sameSelection(selection, next);
    writeSelection(next);
    if (!next || clearing) return;
    const span = next.end - next.start + 1;
    updateViewport(centeredViewport((next.start + next.end) / 2, Math.min(MAX_DETAIL_WINDOW, span), length));
  }, [length, selection, updateViewport, writeSelection]);

  const selectResidue = useCallback((position: number) => {
    writeSelection({ start: position, end: position, site: position });
  }, [writeSelection]);

  function zoom(factor: number) {
    updateViewport(centeredViewport((viewport.start + viewport.end) / 2, Math.max(MIN_VIEWPORT, Math.min(length, Math.round(detailSpan * factor))), length));
  }

  function pan(direction: -1 | 1) {
    const delta = Math.max(1, Math.round(detailSpan * .35)) * direction;
    updateViewport(centeredViewport((viewport.start + viewport.end) / 2 + delta, detailSpan, length));
  }

  function reset() {
    updateViewport({ start: 1, end: length });
    setEnabled(TRACKS.map((track) => track.key));
    writeSelection(null);
  }

  function panelKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLSelectElement || event.target instanceof HTMLButtonElement) return;
    if (event.key === "+" || event.key === "=") { event.preventDefault(); zoom(.7); }
    else if (event.key === "-" || event.key === "_") { event.preventDefault(); zoom(1.4); }
    else if (event.key === "Home") { event.preventDefault(); updateViewport({ start: 1, end: length }); }
    else if (event.key === "Escape") { event.preventDefault(); writeSelection(null); }
  }

  const overviewData = overview.data;
  const topology = useMemo(() => overviewData?.topology_intervals.map(topologyInterval) ?? [], [overviewData]);
  const pfam = useMemo(() => overviewData?.pfam_intervals.map(pfamInterval) ?? [], [overviewData]);
  const functional = useMemo(() => overviewData?.functional_intervals.map(functionalInterval) ?? [], [overviewData]);
  const secondaryStructure = useMemo(() => overviewData?.secondary_structure_intervals.map(secondaryStructureInterval) ?? [], [overviewData]);
  const topologyStyles = useMemo(() => assignTrackCategoryStyles(topology.map((item) => item.category)), [topology]);
  const pfamStyles = useMemo(() => assignTrackCategoryStyles(pfam.map((item) => item.category)), [pfam]);
  const functionalStyles = useMemo(() => assignTrackCategoryStyles(functional.map((item) => item.category)), [functional]);
  const ptmCategories = useMemo(() => overviewData?.ptm_type_counts.map((item) => normalizePtmCategory(item.ptm_type)) ?? [], [overviewData]);
  const ptmStyles = useMemo(() => assignTrackCategoryStyles(ptmCategories), [ptmCategories]);
  const totalCounts = overviewData?.variant_site_density.total_counts ?? [];
  const plpCounts = overviewData?.variant_site_density.clinvar_plp_counts ?? [];
  const sequence = overviewData?.canonical_sequence ?? "";

  return <section id="sequence" className="overview-section sequence-section m8-sequence" aria-labelledby="sequence-heading">
    <div className="section-heading split-heading"><div><p className="eyebrow">Canonical coordinates</p><h2 id="sequence-heading">Sequence explorer</h2></div><button type="button" className="quiet-button" onClick={reset}>Reset view &amp; tracks</button></div>
    <p className="section-intro">One canonical panel combines protein features, conservation, PTM and per-site variants. Mulberry marks explicit ClinVar P/LP evidence presence, not consensus.</p>

    <div className="sequence-toolbar" aria-label="Sequence explorer toolbar">
      <fieldset className="sequence-track-controls"><legend>Visible tracks</legend>{TRACKS.map((track) => <label key={track.key}><input type="checkbox" checked={enabled.includes(track.key)} onChange={(event) => setEnabled((current) => event.target.checked ? [...current, track.key] : current.filter((key) => key !== track.key))} /><span aria-hidden="true">{track.symbol}</span> {track.label}</label>)}</fieldset>
      <div className="sequence-zoom-controls"><button type="button" onClick={() => pan(-1)} aria-label="Pan left">←</button><button type="button" onClick={() => zoom(.7)} aria-label="Zoom in">+</button><button type="button" onClick={() => zoom(1.4)} aria-label="Zoom out">−</button><button type="button" onClick={() => pan(1)} aria-label="Pan right">→</button><button type="button" className="full-length-button" onClick={() => updateViewport({ start: 1, end: length })}>Full length</button><span>{viewport.start.toLocaleString()}–{viewport.end.toLocaleString()} aa</span></div>
    </div>

    <div className="sequence-window-controls" aria-label="Set exact canonical range">
      <label>Start<input type="number" min={1} max={length} value={draft.start} onChange={(event) => setDraft((current) => ({ ...current, start: Number(event.target.value) }))} /></label>
      <label>End<input type="number" min={1} max={length} value={draft.end} onChange={(event) => setDraft((current) => ({ ...current, end: Number(event.target.value) }))} /></label>
      <button type="button" className="primary-button" onClick={() => updateViewport(draft)}>Apply range</button>
      <span>Exact residue detail appears at 120 aa or less; wider views aggregate without dropping records.</span>
    </div>

    {overview.kind === "loading" && <StatusMessage title="Loading sequence panel">Retrieving bounded full-protein summaries.</StatusMessage>}
    {overview.kind === "error" && <StatusMessage title="Sequence panel unavailable" tone="error">{overview.error}</StatusMessage>}
    {overviewData && <div className="sequence-panel" tabIndex={0} onKeyDown={panelKeyDown} aria-label={`Canonical sequence panel, visible range ${viewport.start} to ${viewport.end}. Plus and minus zoom, Home restores full length, Escape clears selection.`}>
      <div className="sequence-axis"><span>{viewport.start.toLocaleString()}</span><strong>Canonical sequence · {overviewData.canonical_length.toLocaleString()} aa</strong><span>{viewport.end.toLocaleString()}</span></div>
      <RangeSelector viewport={viewport} length={length} onViewport={updateViewport} />
      {enabled.includes("topology") && <IntervalTrack label="Topology" symbol="▱" intervals={topology} viewport={viewport} selection={selection} onSelect={writeSelection} className="sequence-topology" styles={topologyStyles} />}
      {enabled.includes("pfam") && <IntervalTrack label="Pfam" symbol="▰" intervals={pfam} viewport={viewport} selection={selection} onSelect={writeSelection} className="sequence-pfam" styles={pfamStyles} />}
      {enabled.includes("functional") && <IntervalTrack label="Functional" symbol="◆" intervals={functional} viewport={viewport} selection={selection} onSelect={writeSelection} className="sequence-functional" styles={functionalStyles} />}
      {enabled.includes("secondaryStructure") && <SecondaryStructureTrack intervals={secondaryStructure} viewport={viewport} selection={selection} onSelect={selectOverviewRange} />}
      {!overviewData.response_bounds.secondary_structure_intervals_complete && <p className="sequence-inline-warning" role="status">Secondary-structure overview is bounded: showing {overviewData.response_bounds.secondary_structure_intervals_returned.toLocaleString()} of {overviewData.totals.secondary_structure_intervals.toLocaleString()} UniProt canonical intervals. Zoom to an annotated range for its exact selection.</p>}
      {enabled.includes("conservation") && <JsdTrack bins={overviewData.density_bins} detail={detail.sites} viewport={viewport} selection={selection} />}
      {detail.kind === "error" && <p className="sequence-inline-warning" role="alert">Residue-level JSD unavailable; bounded overview remains visible. {detail.error}</p>}
      {enabled.includes("ptm") && <PtmTrack sites={overviewData.ptm_sites} allTypes={ptmCategories} styles={ptmStyles} viewport={viewport} selection={selection} onSelect={writeSelection} onSelectRange={selectOverviewRange} />}
      {enabled.includes("variant") && <VariantBars totalCounts={totalCounts} plpCounts={plpCounts} viewport={viewport} selection={selection} onSelect={writeSelection} onSelectRange={selectOverviewRange} />}
      {enabled.includes("stability") && stability.available && <StabilityTrack accession={accession} bins={stability.bins} detail={detail.sites} viewport={viewport} selection={selection} onSelect={selectOverviewRange} />}
      {enabled.includes("stability") && !stability.available && <p className="sequence-inline-warning" role="status">ThermoMPNN stability is unavailable from the current API response. Other sequence tracks remain available.</p>}
      {enabled.includes("covalent") && <CovalentTrack pairs={overviewData.covalent_pairs} viewport={viewport} selection={selection} onSelect={writeSelection} />}
      {detailSpan <= MAX_DETAIL_WINDOW ? <ResidueGrid sequence={sequence} totalCounts={totalCounts} plpCounts={plpCounts} viewport={viewport} selection={selection} onSelect={selectResidue} /> : <p className="sequence-detail-hint" role="status">Overview scale: screen-space bins are summarized above without dropping records. Activate a Variant, PTM, Stability, or secondary-structure mark to zoom into exact residues.</p>}
      {selection?.site && !siteEvidenceOpen && <div className="sequence-site-selection-dock" role="status"><span><strong>Canonical residue {selection.site.toLocaleString()} remains selected</strong><small>The evidence panel is hidden; Sequence, Structure, and Variant views stay linked.</small></span><button type="button" className="quiet-button" onClick={() => setSiteEvidenceOpen(true)}>Open site evidence</button><button type="button" className="quiet-button" onClick={() => writeSelection(null)}>Clear selection</button></div>}
      {selection?.site && siteEvidenceOpen && <SelectedSiteEvidence accession={accession} position={selection.site} onClose={() => setSiteEvidenceOpen(false)} onClearSelection={() => writeSelection(null)} onSelectPartner={(partner) => writeSelection({ start: partner, end: partner, site: partner })} onOpenVariants={() => { onSelectionChange(selection); document.getElementById("variants")?.scrollIntoView({ behavior: "smooth", block: "start" }); }} />}
      <ul className="sequence-total-summary" aria-label="Complete sequence summary"><li>Topology <strong>{overviewData.totals.topology_intervals.toLocaleString()}</strong></li><li>Pfam <strong>{overviewData.totals.pfam_intervals.toLocaleString()}</strong></li><li>Functional <strong>{overviewData.totals.functional_intervals.toLocaleString()}</strong></li><li>Secondary structure <strong>{overviewData.totals.secondary_structure_intervals.toLocaleString()}</strong> UniProt intervals</li><li>PTM <strong>{overviewData.totals.ptm_drawable_records.toLocaleString()}</strong> drawable</li><li>Variants <strong>{overviewData.totals.canonical_drawable_variants.toLocaleString()}</strong> drawable</li><li>ThermoMPNN {stability.available ? <><strong>{stability.totals.distinct_substitutions.toLocaleString()}</strong> substitutions at {stability.totals.canonical_sites.toLocaleString()} sites</> : <strong>unavailable</strong>}</li></ul>
      <p className="sr-only">Variant bars contain no variant fact rows. Each drawable canonical variant is anchored once at its minimum canonical protein start. The residue map is virtualized.</p>
    </div>}
  </section>;
}
