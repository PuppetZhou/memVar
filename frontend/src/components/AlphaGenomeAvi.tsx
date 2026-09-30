import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
} from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { ChevronUp, Plus, X, ZoomIn } from 'lucide-react';
import { api, number, params } from '../api';
import { palette } from '../lib/palette';
import { GenomeTooltip } from './AlphaGenomeInspect';
import {
  GENOMIC_PLOT,
  positionAtPixel,
  positionInView as inView,
  projectX,
  type GenomicView,
} from './genomic-coordinates';

export type AviView = GenomicView;
export type AviContribution = {
  feature: string;
  label: string;
  group: string;
  value: number | null;
};
export type AviItem = {
  variant_id: string;
  position: number;
  ref: string;
  alt: string;
  raw: number | null;
  phred: number | null;
  status: string;
  contributions?: AviContribution[];
  attribution_status?: string;
};
export type AviPage = {
  kind: 'avi';
  items: AviItem[];
  start: number;
  end: number;
  chromosome: string;
  total: number;
  has_more: boolean;
  next_cursor: string | null;
  scope: string;
  attribution_status?: string;
  source_snapshot?: string | null;
  attribution_note?: string;
};
export type AviDetail = {
  variant: {
    variant_id: string;
    chromosome: string;
    position: number;
    ref: string;
    alt: string;
  };
  score: { raw: number | null; phred: number | null; status: string };
  attribution: {
    status: string;
    source_snapshot: string | null;
    contributions: AviContribution[];
    note: string;
  };
};
export type AviTrackProps = {
  accession: string;
  gene: { ensembl_gene_id: string };
  tile: { tile_id: string; chromosome: string };
  view: AviView;
  /** The selected SNV position, distinct from the temporary shared hover position. */
  position: number | null;
  onPosition: (position: number | null) => void;
  onFocusVariant: (position: number) => void;
  hoverPosition: number | null;
  onHover: (position: number | null) => void;
  /** Temporary 0-based half-open brush, owned by the shared track container. */
  brush: AviView | null;
};

type AviScale = 'raw' | 'phred';
type Group = { id: string; label: string; color: string };
type Segment = { group: string; from: number; to: number };
export const AVI_GROUPS: Group[] = [
  { id: 'protein', label: 'Protein impact', color: palette.blue },
  { id: 'conservation', label: 'Conservation', color: palette.sage },
  { id: 'accessibility', label: 'Accessibility', color: palette.butter },
  { id: 'chip', label: 'ChIP', color: palette.cyan },
  { id: 'transcription', label: 'Transcription / RNA', color: palette.leaf },
  { id: 'splicing', label: 'Splicing', color: palette.coral },
  { id: 'contacts', label: 'Contacts', color: palette.ice },
  { id: 'variant_type', label: 'Variant type', color: palette.peach },
];
const aliases: Record<string, string> = {
  protein_impact: 'protein',
  rna: 'transcription',
  transcription_rna: 'transcription',
};
const groupId = (id: string) => aliases[id] ?? id;
const finiteValue = (value: number | null | undefined): value is number =>
  typeof value === 'number' && Number.isFinite(value);
const num = (value: number | null | undefined) =>
  finiteValue(value) ? number(value, 5) : 'Not available';
const styleColor = (name: string, color: string) =>
  ({ [name]: color }) as CSSProperties;
const TOP = 18,
  BOTTOM = 218,
  HEIGHT = 246;
const EXPECTED_FEATURES = 18;
const contributionCoverage = (item: AviItem) => {
  const values = item.contributions ?? [],
    finite = values.filter((c) => finiteValue(c.value)).length;
  return {
    finite,
    partial:
      finite > 0 &&
      (values.length !== EXPECTED_FEATURES || finite !== EXPECTED_FEATURES),
  };
};

function knownGroups(contributions: AviContribution[]): Group[] {
  const extras = [
    ...new Set(contributions.map((c) => groupId(c.group))),
  ].filter((id) => !AVI_GROUPS.some((g) => g.id === id));
  return [
    ...AVI_GROUPS,
    ...extras.map((id) => ({
      id,
      label: id.replaceAll('_', ' '),
      color: palette.ice,
    })),
  ];
}

/** Separate positive and negative feature sums; never normalize to or reconstruct AVI. */
function segmentsFor(item: AviItem, groups: Group[]): Segment[] {
  let positive = 0,
    negative = 0;
  const segments: Segment[] = [];
  const grouped = new Map<string, { positive: number; negative: number }>();
  for (const c of item.contributions ?? []) {
    if (!finiteValue(c.value)) continue;
    const key = groupId(c.group),
      totals = grouped.get(key) ?? { positive: 0, negative: 0 };
    if (c.value >= 0) totals.positive += c.value;
    else totals.negative += c.value;
    grouped.set(key, totals);
  }
  for (const group of groups) {
    const totals = grouped.get(group.id);
    if (!totals) continue;
    if (totals.positive === 0 && totals.negative === 0)
      segments.push({ group: group.id, from: 0, to: 0 });
    if (totals.positive > 0) {
      segments.push({
        group: group.id,
        from: positive,
        to: positive + totals.positive,
      });
      positive += totals.positive;
    }
    if (totals.negative < 0) {
      segments.push({
        group: group.id,
        from: negative,
        to: negative + totals.negative,
      });
      negative += totals.negative;
    }
  }
  return segments;
}

function AviLegend({
  groups,
  scores,
  onToggle,
  onAll,
  onTotal,
}: {
  groups: Group[];
  scores: string[];
  onToggle: (id: string) => void;
  onAll: () => void;
  onTotal: () => void;
}) {
  const options = [
    { id: 'total', label: 'Total impact score', color: '#26292d' },
    ...groups,
  ];
  return (
    <div
      className="agx-avi-legend agx-avi-sidebar"
      role="group"
      aria-label="AVI score categories"
    >
      <div className="agx-avi-options">
        {options.map((group) => (
          <label
            key={group.id}
            className={`agx-avi-category${group.id === 'total' ? ' agx-avi-total' : ''}`}
            data-selected={scores.includes(group.id)}
            style={styleColor('--avi-group-color', group.color)}
          >
            <input
              type="checkbox"
              checked={scores.includes(group.id)}
              onChange={() => onToggle(group.id)}
            />
            <i aria-hidden="true" />
            <span>{group.label}</span>
          </label>
        ))}
      </div>
      <div className="agx-avi-selection-actions">
        <button
          disabled={options.every((g) => scores.includes(g.id))}
          onClick={onAll}
        >
          Select all
        </button>
        <button
          disabled={scores.length === 1 && scores[0] === 'total'}
          onClick={onTotal}
        >
          Total only
        </button>
      </div>
    </div>
  );
}

export function AviPlot({
  items,
  chromosome,
  view,
  scale,
  groups,
  scores,
  position,
  hoverPosition,
  onHover,
  brush,
  onSelect,
}: {
  items: AviItem[];
  chromosome: string;
  view: AviView;
  scale: AviScale;
  groups: Group[];
  scores: string[];
  position: number | null;
  hoverPosition: number | null;
  onHover: (position: number | null) => void;
  brush: AviView | null;
  onSelect: (item: AviItem) => void;
}) {
  const [canvas, setCanvas] = useState<HTMLCanvasElement | null>(null);
  const [width, setWidth] = useState(1000);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [anchor, setAnchor] = useState<{ x: number; y: number } | null>(null);
  const showTotal = scores.includes('total');
  const visibleGroups = useMemo(
    () => (scale === 'raw' ? groups.filter((g) => scores.includes(g.id)) : []),
    [groups, scores, scale]
  );
  const plotted = useMemo(
    () =>
      items.map((item) => ({
        item,
        segments: segmentsFor(item, visibleGroups),
      })),
    [items, visibleGroups]
  );
  const byPosition = useMemo(() => {
    const result = new Map<number, AviItem[]>();
    for (const item of items)
      result.set(item.position, [...(result.get(item.position) ?? []), item]);
    return result;
  }, [items]);
  const bounds = useMemo(() => {
    let low = 0,
      high = 0;
    for (const { item, segments } of plotted) {
      const value = item[scale];
      if (showTotal && finiteValue(value)) {
        low = Math.min(low, value);
        high = Math.max(high, value);
      }
      for (const segment of segments) {
        low = Math.min(low, segment.to);
        high = Math.max(high, segment.to);
      }
    }
    return { low, high, span: high - low || 1 };
  }, [plotted, scale, showTotal]);
  const x = useCallback(
    (position1: number) => projectX(position1 - 1, view, width),
    [view[0], view[1], width]
  );
  const plotLeft = (width * GENOMIC_PLOT.left) / GENOMIC_PLOT.width;
  const plotRight = (width * GENOMIC_PLOT.right) / GENOMIC_PLOT.width;
  const plotWidth = (width * GENOMIC_PLOT.span) / GENOMIC_PLOT.width;
  const y = useCallback(
    (value: number) =>
      BOTTOM - ((value - bounds.low) / bounds.span) * (BOTTOM - TOP),
    [bounds]
  );
  // Density changes glyph size only. Every allele keeps its source x/y and values.
  const density = useMemo(() => {
    const columns = new Map<number, number>();
    for (const item of items)
      if (inView(item.position, view)) {
        const pixel = Math.floor(x(item.position));
        columns.set(pixel, (columns.get(pixel) ?? 0) + 1);
      }
    return {
      columns,
      crowded: [...columns.values()].some((count) => count > 6),
    };
  }, [items, view, x]);
  const hovered =
    hoveredId === null
      ? null
      : (items.find(
          (item) =>
            item.variant_id === hoveredId && item.position === hoverPosition
        ) ?? null);
  const exactItems =
    hoverPosition === null ? [] : (byPosition.get(hoverPosition) ?? []);
  const inspected = hovered ? [hovered] : exactItems;
  const selectedFeatures = (hovered?.contributions ?? []).filter((c) =>
    visibleGroups.some((g) => g.id === groupId(c.group))
  );
  const nonzeroFeatures = selectedFeatures
    .filter((c) => finiteValue(c.value) && c.value !== 0)
    .sort((a, b) => Math.abs(b.value!) - Math.abs(a.value!));
  const tooltipFeatures = nonzeroFeatures.slice(0, 6);
  const zeroCount = selectedFeatures.filter((c) => c.value === 0).length;
  const missingCount = selectedFeatures.filter(
    (c) => !finiteValue(c.value)
  ).length;
  const omittedCount = nonzeroFeatures.length - tooltipFeatures.length;

  useEffect(() => {
    if (!canvas) return;
    const observer = new ResizeObserver((entries) =>
      setWidth(Math.max(1, entries[0].contentRect.width))
    );
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [canvas]);

  useEffect(() => {
    const ctx = canvas?.getContext('2d');
    if (!ctx || !canvas) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(HEIGHT * ratio);
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, HEIGHT);
    ctx.font = '12px system-ui';
    ctx.textAlign = 'right';
    for (const r of [0, 0.5, 1]) {
      const yy = TOP + r * (BOTTOM - TOP);
      ctx.strokeStyle = '#e0e4e8';
      ctx.beginPath();
      ctx.moveTo(plotLeft, yy);
      ctx.lineTo(plotRight, yy);
      ctx.stroke();
      ctx.fillStyle = '#303438';
      ctx.fillText(
        number(bounds.high - r * (bounds.high - bounds.low), 3),
        width * 0.044,
        yy + 4
      );
    }
    const zero = y(0);
    ctx.strokeStyle = '#aeb8c4';
    ctx.beginPath();
    ctx.moveTo(plotLeft, zero);
    ctx.lineTo(plotRight, zero);
    ctx.stroke();
    ctx.save();
    ctx.beginPath();
    ctx.rect(plotLeft, 0, plotWidth, BOTTOM + 8);
    ctx.clip();
    const barWidth = Math.max(
      0.65,
      Math.min(8, (plotWidth / (view[1] - view[0])) * 0.74)
    );
    // Draw contributions before total markers so a later allele cannot erase a total.
    for (const { item, segments } of plotted) {
      if (!inView(item.position, view)) continue;
      const xx = x(item.position);
      for (const segment of segments) {
        if (segment.from === segment.to) continue;
        ctx.fillStyle =
          groups.find((group) => group.id === segment.group)?.color ??
          '#8b96a4';
        ctx.fillRect(
          xx - barWidth / 2,
          Math.min(y(segment.from), y(segment.to)),
          barWidth,
          Math.abs(y(segment.to) - y(segment.from))
        );
      }
    }
    if (showTotal) {
      ctx.fillStyle = '#303438';
      ctx.beginPath();
      for (const { item } of plotted) {
        const value = item[scale];
        if (!inView(item.position, view) || !finiteValue(value)) continue;
        const xx = x(item.position),
          yy = y(value),
          count = density.columns.get(Math.floor(xx)) ?? 1;
        const radius = count > 12 ? 0.65 : count > 3 ? 0.95 : 1.5;
        // One path avoids repeated anti-aliasing darkening at identical marks.
        // No per-position maximum/mean, jitter, or allele filtering is applied.
        ctx.moveTo(xx, yy - radius);
        ctx.lineTo(xx + radius, yy);
        ctx.lineTo(xx, yy + radius);
        ctx.lineTo(xx - radius, yy);
        ctx.closePath();
      }
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (brush) {
      const a = Math.max(view[0], Math.min(...brush)),
        b = Math.min(view[1], Math.max(...brush));
      if (a < b) {
        ctx.fillStyle = '#2656c91a';
        ctx.fillRect(x(a + 1), 0, x(b + 1) - x(a + 1), BOTTOM + 8);
        ctx.strokeStyle = '#2656c980';
        ctx.strokeRect(x(a + 1), 0.5, x(b + 1) - x(a + 1), BOTTOM + 7);
      }
    }
    if (position !== null && inView(position, view)) {
      ctx.strokeStyle = '#2656c9';
      ctx.lineWidth = 1.3;
      ctx.beginPath();
      ctx.moveTo(x(position), 0);
      ctx.lineTo(x(position), BOTTOM + 7);
      ctx.stroke();
      ctx.lineWidth = 1;
    }
    if (hoverPosition !== null && inView(hoverPosition, view)) {
      ctx.strokeStyle = '#2656c9';
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(x(hoverPosition), 0);
      ctx.lineTo(x(hoverPosition), BOTTOM + 7);
      ctx.stroke();
      for (const item of inspected) {
        const value = item[scale];
        if (!showTotal || !finiteValue(value)) continue;
        ctx.beginPath();
        ctx.moveTo(plotLeft, y(value));
        ctx.lineTo(plotRight, y(value));
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = '#2656c9';
        ctx.beginPath();
        ctx.arc(x(item.position), y(value), 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.setLineDash([4, 3]);
      }
      ctx.setLineDash([]);
    }
    ctx.restore();
    if (hoverPosition !== null && inView(hoverPosition, view)) {
      ctx.fillStyle = '#2656c9';
      ctx.textAlign = 'center';
      const label = `${chromosome}:${hoverPosition.toLocaleString()}`,
        half = ctx.measureText(label).width / 2;
      ctx.fillText(
        label,
        Math.max(half + 3, Math.min(width - half - 3, x(hoverPosition))),
        HEIGHT - 6
      );
      ctx.textAlign = 'right';
      for (const item of inspected)
        if (showTotal && finiteValue(item[scale]))
          ctx.fillText(
            number(item[scale], 3),
            width * 0.044,
            y(item[scale]) - 4
          );
    }
  }, [
    canvas,
    width,
    plotted,
    scale,
    groups,
    scores,
    showTotal,
    position,
    hoverPosition,
    brush,
    bounds,
    x,
    y,
    chromosome,
    hoveredId,
    density,
    plotLeft,
    plotRight,
    plotWidth,
  ]);

  const clearHover = () => {
    setHoveredId(null);
    setAnchor(null);
    onHover(null);
  };
  const focusRecord = (index: number) => {
    const item = items[Math.max(0, Math.min(items.length - 1, index))];
    if (!item || !scores.length) return;
    setHoveredId(item.variant_id);
    onHover(item.position);
    setAnchor({
      x: x(item.position),
      y: showTotal && finiteValue(item[scale]) ? y(item[scale]) : TOP,
    });
  };
  const tooltipLeft = anchor
    ? Math.max(6, Math.min(Math.max(6, width - 326), anchor.x + 12))
    : 6;
  const tooltipTop = anchor ? Math.max(8, Math.min(95, anchor.y + 14)) : 8;
  return (
    <>
      <div
        className="agx-avi-plot"
        data-density={density.crowded ? 'dense' : 'resolved'}
      >
        <canvas
          ref={setCanvas}
          className="agx-avi-canvas"
          style={{ height: HEIGHT }}
          role="img"
          tabIndex={0}
          aria-label={`AVI ${scale}. Showing ${scores.length ? scores.map((id) => (id === 'total' ? 'Total impact score' : (groups.find((g) => g.id === id)?.label ?? id))).join(', ') : 'no scores'}. ${items.length} individual SNVs. Arrow keys inspect alleles; Enter opens details.`}
          onPointerMove={(event) => {
            if (!scores.length) {
              clearHover();
              return;
            }
            const rect = event.currentTarget.getBoundingClientRect(),
              px = event.clientX - rect.left,
              py = event.clientY - rect.top;
            if (
              px < plotLeft ||
              px > plotRight ||
              py < TOP - 10 ||
              py > BOTTOM + 8
            ) {
              clearHover();
              return;
            }
            let best: AviItem | null = null,
              distance = Infinity;
            for (const { item, segments } of plotted) {
              const horizontal = Math.abs(x(item.position) - px);
              if (horizontal > 6) continue;
              const value = item[scale];
              const distances = segments.map((segment) => {
                const top = Math.min(y(segment.from), y(segment.to)),
                  bottom = Math.max(y(segment.from), y(segment.to));
                return Math.max(top - py, py - bottom, 0);
              });
              if (showTotal && finiteValue(value))
                distances.push(Math.abs(y(value) - py));
              if (!distances.length) continue;
              const vertical = Math.min(...distances);
              const d = horizontal * 4 + vertical;
              if (d < distance) {
                best = item;
                distance = d;
              }
            }
            const pointerPosition = positionAtPixel(px, width, view, true);
            setHoveredId(best?.variant_id ?? null);
            setAnchor({ x: px, y: py });
            onHover(best?.position ?? pointerPosition);
          }}
          onPointerLeave={clearHover}
          onBlur={clearHover}
          onFocus={(event) => {
            if (items.length && event.currentTarget.matches(':focus-visible'))
              focusRecord(0);
          }}
          onKeyDown={(event) => {
            if (!items.length || !scores.length) return;
            const index = Math.max(
              0,
              items.findIndex((item) => item.variant_id === hoveredId)
            );
            if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
              event.preventDefault();
              focusRecord(index + (event.key === 'ArrowRight' ? 1 : -1));
            } else if (event.key === 'Enter') {
              event.preventDefault();
              onSelect(items[index]);
            } else if (event.key === 'Escape') clearHover();
          }}
          onClick={() => {
            if (hovered) onSelect(hovered);
          }}
        />
        {anchor && hoverPosition !== null && (
          <GenomeTooltip
            className="agx-avi-tooltip"
            left={tooltipLeft}
            top={tooltipTop}
          >
            <div className="agx-avi-tooltip-heading">
              <strong>
                {chromosome}:{hoverPosition.toLocaleString()}
              </strong>
              {hovered && (
                <span className="agx-avi-tooltip-allele">
                  {hovered.ref}
                  <span>→</span>
                  {hovered.alt}
                </span>
              )}
            </div>
            {!inspected.length ? (
              <p className="agx-avi-tooltip-note">
                No loaded SNV at this coordinate.
              </p>
            ) : (
              showTotal && (
                <div className="agx-avi-tooltip-totals">
                  {inspected.map((item) => (
                    <div
                      className="agx-avi-tooltip-value"
                      key={item.variant_id}
                    >
                      <span>
                        {!hovered && `${item.ref} → ${item.alt} · `}Total{' '}
                        <small>{scale === 'phred' ? 'PHRED' : 'Raw'}</small>
                      </span>
                      <b>{num(item[scale])}</b>
                    </div>
                  ))}
                </div>
              )
            )}
            {hovered && visibleGroups.length > 0 && (
              <div className="agx-avi-tooltip-features">
                <div className="agx-avi-tooltip-caption">
                  {visibleGroups.length === 1
                    ? visibleGroups[0].label
                    : 'Feature contributions'}
                  <span>Raw contribution</span>
                </div>
                {tooltipFeatures.map((c) => (
                  <div
                    key={c.feature}
                    className="agx-avi-tooltip-value"
                    style={styleColor(
                      '--avi-group-color',
                      groups.find((g) => g.id === groupId(c.group))?.color ??
                        palette.ice
                    )}
                  >
                    <span>
                      <i aria-hidden="true" />
                      {c.label}
                    </span>
                    <b>{num(c.value)}</b>
                  </div>
                ))}
                {!selectedFeatures.length && (
                  <p className="agx-avi-tooltip-note">
                    Contributions unavailable
                  </p>
                )}
                {(zeroCount > 0 || missingCount > 0 || omittedCount > 0) && (
                  <p className="agx-avi-tooltip-note">
                    {[
                      zeroCount ? `${zeroCount} zero-value features` : '',
                      missingCount ? `${missingCount} unavailable` : '',
                      omittedCount
                        ? `${omittedCount} more · showing 6 largest by magnitude`
                        : '',
                    ]
                      .filter(Boolean)
                      .join(' · ')}
                  </p>
                )}
              </div>
            )}
            {hovered && (
              <div className="agx-avi-tooltip-footer">
                {(byPosition.get(hovered.position)?.length ?? 0) > 1 && (
                  <>
                    {byPosition.get(hovered.position)!.length} alleles at this
                    position ·{' '}
                  </>
                )}
                Click for all feature values
              </div>
            )}
          </GenomeTooltip>
        )}
      </div>
      <div className="agx-inspect" aria-live="polite">
        {hoverPosition !== null ? (
          <>
            <strong>
              {chromosome}:{number(hoverPosition, 0)}
            </strong>
            {inspected.length ? (
              inspected.map((item) => (
                <span key={item.variant_id}>
                  {item.ref} → {item.alt}
                  {showTotal && (
                    <>
                      {' '}
                      · {scale === 'phred' ? 'PHRED' : 'Raw'}{' '}
                      <b>{num(item[scale])}</b>
                    </>
                  )}
                </span>
              ))
            ) : (
              <span>No loaded SNV at this coordinate</span>
            )}
            {hovered && (
              <button onClick={() => onSelect(hovered)}>
                Feature contributions
              </button>
            )}
          </>
        ) : !scores.length ? (
          'Select at least one score to display.'
        ) : density.crowded ? (
          'Overlapping SNVs at this zoom · drag across a region to expand'
        ) : (
          'Hover to inspect · click for SNV details'
        )}
      </div>
    </>
  );
}

function AviDetails({
  accession,
  item,
  groups,
  onClose,
  onFocus,
}: {
  accession: string;
  item: AviItem;
  groups: Group[];
  onClose: () => void;
  onFocus: () => void;
}) {
  const q = useQuery({
    queryKey: ['alphagenome-avi-detail', accession, item.variant_id],
    queryFn: ({ signal }) =>
      api<AviDetail>(
        `/variants/${encodeURIComponent(item.variant_id)}/avi?${params({ accession })}`,
        signal
      ),
    staleTime: 60000,
    retry: 1,
  });
  const contributions = q.data?.attribution.contributions ?? [];
  const peak =
    contributions.reduce(
      (max, c) =>
        finiteValue(c.value) ? Math.max(max, Math.abs(c.value)) : max,
      0
    ) || 1;
  const coverage = contributionCoverage({ ...item, contributions });
  return (
    <section className="agx-avi-detail" aria-label="Selected SNV AVI details">
      <header>
        <div>
          <strong>
            {number(item.position, 0)} {item.ref} → {item.alt}
          </strong>
          <span>
            AVI PHRED {num(q.data ? q.data.score.phred : item.phred)} · Raw{' '}
            {num(q.data ? q.data.score.raw : item.raw)}
          </span>
        </div>
        <div className="agx-avi-detail-actions">
          <button onClick={onFocus}>
            <ZoomIn size={13} />
            Zoom to variant
          </button>
          <button aria-label="Close SNV details" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
      </header>
      {q.error ? (
        <div className="agx-error">
          {q.error.message}
          <button onClick={() => q.refetch()}>Retry details</button>
        </div>
      ) : !q.data ? (
        <p>Loading feature contributions…</p>
      ) : (
        <>
          <p className="agx-footnote">
            Feature contributions ·{' '}
            {q.data.attribution.status.replaceAll('_', ' ')}. Original signed
            values; the independent AVI score is not reconstructed from their
            sum.
          </p>
          {coverage.partial && (
            <p className="agx-avi-attribution-status">
              Partial feature data: {coverage.finite}/{EXPECTED_FEATURES} values
              are available. Bars show only supplied values; missing entries
              remain unavailable.
            </p>
          )}
          {contributions.length ? (
            <div className="agx-contributions">
              {contributions.map((c) => (
                <div key={c.feature} className="agx-contribution">
                  <span title={c.feature}>{c.label}</span>
                  <div className="agx-contribution-bar">
                    <i />
                    <b
                      style={{
                        left: `${finiteValue(c.value) && c.value < 0 ? 50 - (Math.abs(c.value) / peak) * 50 : 50}%`,
                        width: `${finiteValue(c.value) ? (Math.abs(c.value) / peak) * 50 : 0}%`,
                        background:
                          groups.find((group) => group.id === groupId(c.group))
                            ?.color ?? '#8b96a4',
                      }}
                    />
                  </div>
                  <strong>{num(c.value)}</strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="agx-avi-attribution-status">
              Feature contributions are not available for this SNV. Its
              independent AVI score remains shown above.
            </p>
          )}
          {q.data.attribution.source_snapshot && (
            <details>
              <summary>Attribution source</summary>
              <p className="agx-footnote">
                {q.data.attribution.source_snapshot}
              </p>
            </details>
          )}
        </>
      )}
    </section>
  );
}

export function AviTrack({
  accession,
  gene,
  tile,
  view,
  position,
  onPosition,
  onFocusVariant,
  hoverPosition,
  onHover,
  brush,
}: AviTrackProps) {
  const [collapsed, setCollapsed] = useState(false),
    [scale, setScale] = useState<AviScale>('raw');
  const [scores, setScores] = useState<string[]>(['total']),
    [selected, setSelected] = useState<AviItem | null>(null),
    [listPage, setListPage] = useState(0);
  const previousContext = useRef(`${gene.ensembl_gene_id}:${tile.tile_id}`);
  const q = useInfiniteQuery({
    queryKey: [
      'alphagenome-avi-contributions',
      accession,
      gene.ensembl_gene_id,
      tile.tile_id,
      view[0],
      view[1],
    ],
    initialPageParam: null as string | null,
    queryFn: ({ signal, pageParam }) =>
      api<AviPage>(
        `/proteins/${accession}/expression/alphagenome/avi?${params({
          gene: gene.ensembl_gene_id,
          tile: tile.tile_id,
          start: view[0],
          end: view[1],
          cursor: pageParam,
          limit: 10000,
          include_contributions: 'true',
        })}`,
        signal
      ),
    getNextPageParam: (last) =>
      last.has_more ? (last.next_cursor ?? undefined) : undefined,
    enabled: !collapsed,
    staleTime: 60000,
    retry: 1,
  });
  const items = useMemo(
    () => q.data?.pages.flatMap((page) => page.items) ?? [],
    [q.data]
  );
  const groups = useMemo(
    () => knownGroups(items.flatMap((item) => item.contributions ?? [])),
    [items]
  );
  const first = q.data?.pages[0],
    missing = items.filter((item) => !finiteValue(item[scale])).length;
  const attributionCount = items.filter((item) =>
    (item.contributions ?? []).some((c) => finiteValue(c.value))
  ).length;
  const partialCount = items.filter(
    (item) => contributionCoverage(item).partial
  ).length;
  const visibleScores = useMemo(
    () => (scale === 'phred' ? scores.filter((id) => id === 'total') : scores),
    [scores, scale]
  );
  useEffect(() => {
    setListPage(0);
    onHover(null);
    const context = `${gene.ensembl_gene_id}:${tile.tile_id}`;
    const retain =
      previousContext.current === context &&
      selected !== null &&
      inView(selected.position, view);
    previousContext.current = context;
    if (!retain) setSelected(null);
    onPosition(retain ? selected.position : null);
  }, [view[0], view[1], gene.ensembl_gene_id, tile.tile_id]);
  const choose = (item: AviItem) => {
    setSelected(item);
    onPosition(item.position);
  };
  const toggleScore = (id: string) => {
    if (scale === 'phred' && id !== 'total') {
      setScale('raw');
      setScores((current) =>
        current.includes(id) ? current : [...current, id]
      );
    } else
      setScores((current) =>
        current.includes(id)
          ? current.filter((value) => value !== id)
          : [...current, id]
      );
    onHover(null);
  };
  return (
    <article
      className="agx-track agx-avi-track"
      style={styleColor('--ag-color', palette.blue)}
    >
      <header>
        <div className="agx-track-title">
          <span className="agx-track-kind">AVI score</span>
          <strong>Project SNVs</strong>
          <span>Variant impact</span>
        </div>
        {!collapsed && (
          <AviLegend
            groups={groups}
            scores={visibleScores}
            onToggle={toggleScore}
            onAll={() => {
              setScale('raw');
              setScores(['total', ...groups.map((g) => g.id)]);
              onHover(null);
            }}
            onTotal={() => {
              setScores(['total']);
              onHover(null);
            }}
          />
        )}
        <div className="agx-track-actions">
          <button
            aria-expanded={!collapsed}
            aria-label={`${collapsed ? 'Expand' : 'Collapse'} AVI score`}
            onClick={() => {
              setCollapsed(!collapsed);
              onHover(null);
            }}
          >
            {collapsed ? <Plus size={15} /> : <ChevronUp size={15} />}
          </button>
        </div>
      </header>
      <div className="agx-track-body">
        {collapsed ? (
          <span className="agx-collapsed-label">AVI score collapsed</span>
        ) : (
          <>
            <div className="agx-track-meta">
              <span>{scale === 'raw' ? 'AVI raw' : 'AVI PHRED'}</span>
              <div className="agx-segment">
                <button
                  aria-pressed={scale === 'raw'}
                  onClick={() => setScale('raw')}
                >
                  Raw
                </button>
                <button
                  aria-pressed={scale === 'phred'}
                  onClick={() => {
                    setScale('phred');
                    setScores((current) =>
                      current.includes('total')
                        ? current
                        : ['total', ...current]
                    );
                    onHover(null);
                  }}
                >
                  PHRED
                </button>
              </div>
            </div>
            {scale === 'raw' && scores.some((id) => id !== 'total') && (
              <p className="agx-footnote">
                Signed feature contributions · total score shown independently
              </p>
            )}
            {first?.attribution_status === 'not_available' && (
              <p className="agx-avi-attribution-status">
                Feature contributions are not available yet. Total AVI scores
                are available; colored contribution bars cannot yet be shown.
              </p>
            )}
            {scale === 'raw' && partialCount > 0 && (
              <p className="agx-avi-attribution-status">
                {partialCount.toLocaleString()} SNVs have partial feature data.
                Their stacks contain only available signed values; missing
                features are not zero.
              </p>
            )}
            {q.error ? (
              <div className="agx-error" role="alert">
                {q.error.message}
                <button onClick={() => q.refetch()}>Retry AVI</button>
              </div>
            ) : !q.data ? (
              <div className="agx-loading">Loading AVI scores…</div>
            ) : (
              <>
                <AviPlot
                  items={items}
                  chromosome={first?.chromosome ?? tile.chromosome}
                  view={view}
                  scale={scale}
                  groups={groups}
                  scores={visibleScores}
                  position={position}
                  hoverPosition={hoverPosition}
                  onHover={onHover}
                  brush={brush}
                  onSelect={choose}
                />
                <div className="agx-pagination">
                  <span>
                    {items.length.toLocaleString()} of {number(first?.total, 0)}{' '}
                    SNVs loaded
                    {missing
                      ? ` · ${missing.toLocaleString()} without ${scale} score`
                      : ''}
                    {first?.attribution_status === 'available' &&
                    attributionCount < items.length
                      ? ` · ${attributionCount.toLocaleString()} with contributions`
                      : ''}
                  </span>
                  {q.hasNextPage && (
                    <button
                      disabled={q.isFetchingNextPage}
                      onClick={() => q.fetchNextPage()}
                    >
                      {q.isFetchingNextPage ? 'Loading…' : 'Load more SNVs'}
                    </button>
                  )}
                </div>
                {q.hasNextPage && (
                  <p className="agx-footnote">
                    More SNVs remain. Load the next page or zoom in; the current
                    plot is incomplete.
                  </p>
                )}
                {!items.length && (
                  <p className="agx-footnote">
                    No project SNVs are available in this interval. This does
                    not describe uncollected positions.
                  </p>
                )}
                <details>
                  <summary>Inspect SNV records</summary>
                  <div className="agx-junction-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Position / allele</th>
                          <th>AVI PHRED</th>
                          <th>AVI raw</th>
                          <th>Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items
                          .slice(listPage * 50, listPage * 50 + 50)
                          .map((item) => (
                            <tr key={item.variant_id}>
                              <td>
                                {number(item.position, 0)} {item.ref} →{' '}
                                {item.alt}
                              </td>
                              <td>{num(item.phred)}</td>
                              <td>{num(item.raw)}</td>
                              <td>
                                <button
                                  onClick={() => choose(item)}
                                  aria-label={`Inspect ${item.variant_id}`}
                                >
                                  Inspect
                                </button>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="agx-pagination">
                    <span>
                      Records {items.length ? listPage * 50 + 1 : 0}–
                      {Math.min(items.length, listPage * 50 + 50)}
                    </span>
                    <button
                      disabled={!listPage}
                      onClick={() => setListPage(listPage - 1)}
                    >
                      Previous
                    </button>
                    <button
                      disabled={(listPage + 1) * 50 >= items.length}
                      onClick={() => setListPage(listPage + 1)}
                    >
                      Next
                    </button>
                  </div>
                </details>
              </>
            )}
            {selected && (
              <AviDetails
                accession={accession}
                item={selected}
                groups={groups}
                onFocus={() => onFocusVariant(selected.position)}
                onClose={() => {
                  setSelected(null);
                  onPosition(null);
                }}
              />
            )}
          </>
        )}
      </div>
    </article>
  );
}
