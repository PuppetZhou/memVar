import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'motion/react';
import { useReducedMotion } from '@/lib/use-reduced-motion';
import type { VariantSummary } from './sequence-model';
import './compact-variant-track.css';

type Range = [number, number];
type Site = VariantSummary['canonical_sites'][number];
const categories = [
  { key: 'pathogenic', short: 'P / LP', label: 'Pathogenic / likely pathogenic', color: '#ef4444' },
  { key: 'uncertain', short: 'VUS', label: 'Uncertain significance', color: '#f59e0b' },
  { key: 'benign', short: 'B / LB', label: 'Benign / likely benign', color: '#10b981' },
  { key: 'conflicting', short: 'Conflict', label: 'Conflicting source classifications', color: '#a855f7' },
  { key: 'other', short: 'Other', label: 'Other source classification', color: '#38bdf8' },
  { key: 'unclassified', short: 'No label', label: 'No source classification', color: '#cbd5e1' },
] as const;
type Category = typeof categories[number]['key'];
type Bin = { start: number; end: number; count: number; counts: Record<Category, number>; groupingComplete: boolean };
type Preview = { index: number; x: number; top: number; bottom: number };

export type CompactVariantTrackProps = {
  sites: VariantSummary['canonical_sites'];
  range: Range;
  onSelectRange: (range: Range) => void;
  selectedRange?: Range | null;
  /** Set to zero when the shared track layout already provides its coordinate inset. */
  inset?: number;
  loading?: boolean;
  error?: string | null;
};

function validCount(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}

// Bin bounds and widths stay in the same 1-based inclusive coordinate system as the ruler.
export function buildCompactVariantBins(sites: Site[], range: Range, targetBins: number): Bin[] {
  const [start, end] = range;
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 1 || end < start) return [];
  const span = end - start + 1;
  const target = Number.isFinite(targetBins) ? Math.max(1, Math.floor(targetBins)) : 1;
  const size = Math.max(1, Math.ceil(span / target));
  const bins: Bin[] = Array.from({ length: Math.ceil(span / size) }, (_, i) => ({
    start: start + i * size,
    end: Math.min(end, start + (i + 1) * size - 1),
    count: 0,
    counts: { pathogenic: 0, uncertain: 0, benign: 0, conflicting: 0, other: 0, unclassified: 0 },
    groupingComplete: true,
  }));
  for (const site of sites) {
    if (!Number.isSafeInteger(site.position) || site.position < start || site.position > end) continue;
    const count = site.variant_count ?? site.count;
    if (!validCount(count)) continue;
    const bin = bins[Math.floor((site.position - start) / size)];
    bin.count += count;
    let classified = 0;
    for (const category of categories) {
      const value = site.clinical_counts?.[category.key] ?? 0;
      if (!validCount(value)) { bin.groupingComplete = false; continue; }
      bin.counts[category.key] += value;
      classified += value;
    }
    // Missing grouping is not the same as the API's explicit "unclassified" bucket.
    if (!site.clinical_counts || classified !== count) bin.groupingComplete = false;
  }
  return bins;
}

function describeBin(bin: Bin): string {
  const range = bin.start === bin.end ? `Residue ${bin.start}` : `Residues ${bin.start}–${bin.end}`;
  const groups = bin.groupingComplete
    ? categories.map(category => `${category.label}: ${bin.counts[category.key]}`).join('; ')
    : 'ClinVar grouping unavailable or incomplete';
  return `${range}: ${bin.count.toLocaleString()} variant–position links. ${groups}. Select this range.`;
}

export function CompactVariantTrack({ sites, range, onSelectRange, selectedRange, inset = 12, loading = false, error = null }: CompactVariantTrackProps) {
  const host = useRef<HTMLDivElement>(null);
  const controls = useRef<(SVGGElement | null)[]>([]);
  const [width, setWidth] = useState(600);
  const [activeIndex, setActiveIndex] = useState(0);
  const [hover, setHover] = useState<Preview | null>(null);
  const [focus, setFocus] = useState<Preview | null>(null);
  const tooltipId = useId();
  const noteId = useId();
  const reduceMotion = useReducedMotion();
  const bins = useMemo(() => buildCompactVariantBins(sites, range, Math.min(64, Math.max(1, Math.floor(width / 16)))), [sites, range[0], range[1], width]);
  const max = Math.max(1, ...bins.map(bin => bin.count));
  const total = bins.reduce((sum, bin) => sum + bin.count, 0);
  const span = Math.max(1, range[1] - range[0] + 1);
  const preview = hover ?? focus;
  const previewBin = preview == null ? null : bins[preview.index];
  const unavailable = loading || !!error || !bins.length;

  useEffect(() => {
    const element = host.current;
    if (!element) return;
    const measure = () => setWidth(Math.max(1, element.getBoundingClientRect().width));
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => { setActiveIndex(0); setHover(null); setFocus(null); }, [range[0], range[1], sites, bins.length]);
  useEffect(() => {
    if (!preview) return;
    const hide = () => { setHover(null); setFocus(null); };
    window.addEventListener('scroll', hide, true);
    window.addEventListener('resize', hide);
    return () => { window.removeEventListener('scroll', hide, true); window.removeEventListener('resize', hide); };
  }, [!!preview]);

  const anchor = (index: number, element: SVGGElement): Preview => {
    const rect = element.getBoundingClientRect();
    return { index, x: rect.left + rect.width / 2, top: rect.top, bottom: rect.bottom };
  };
  const moveFocus = (index: number) => {
    const next = Math.max(0, Math.min(bins.length - 1, index));
    setActiveIndex(next);
    setHover(null);
    controls.current[next]?.focus();
  };

  return <div className="compact-variant-track" style={{ marginInline: inset }}>
    <div className="cvt-canvas" ref={host} aria-busy={loading}>
      <svg viewBox={`0 0 ${width} 82`} preserveAspectRatio="none" role="group" aria-label={`Verified canonical variant density, residues ${range[0]}–${range[1]}`} aria-describedby={noteId}>
        <line x1="0" x2={width} y1="76" y2="76" className="cvt-baseline" />
        {!unavailable && bins.map((bin, index) => {
          const x = (bin.start - range[0]) / span * width;
          const binWidth = (bin.end - bin.start + 1) / span * width;
          const gap = Math.min(1.5, binWidth * .12);
          const height = bin.count / max * 68;
          const selected = !!selectedRange && bin.start <= selectedRange[1] && bin.end >= selectedRange[0];
          let accumulated = 0;
          return <g key={`${bin.start}-${bin.end}`} ref={element => { controls.current[index] = element; }}
            className={`cvt-bin${selected ? ' cvt-selected' : ''}`} role="button" tabIndex={activeIndex === index ? 0 : -1}
            aria-label={describeBin(bin)} aria-describedby={preview?.index === index ? tooltipId : undefined}
            onPointerEnter={event => setHover(anchor(index, event.currentTarget))} onPointerLeave={() => setHover(null)}
            onFocus={event => { setActiveIndex(index); setFocus(anchor(index, event.currentTarget)); }} onBlur={() => setFocus(null)}
            onClick={() => onSelectRange([bin.start, bin.end])}
            onKeyDown={event => {
              if (event.key === 'ArrowRight' || event.key === 'ArrowLeft' || event.key === 'Home' || event.key === 'End') {
                event.preventDefault();
                moveFocus(event.key === 'Home' ? 0 : event.key === 'End' ? bins.length - 1 : index + (event.key === 'ArrowRight' ? 1 : -1));
              } else if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault(); onSelectRange([bin.start, bin.end]);
              } else if (event.key === 'Escape') { setHover(null); setFocus(null); }
            }}>
            <rect className="cvt-hit" x={x} y="1" width={binWidth} height="78" />
            {bin.groupingComplete ? categories.map(category => {
              const count = bin.counts[category.key];
              const segmentHeight = count / max * 68;
              const y = 76 - (accumulated + count) / max * 68;
              accumulated += count;
              return count > 0 && <rect key={category.key} x={x + gap / 2} y={y} width={Math.max(0, binWidth - gap)} height={segmentHeight} fill={category.color} />;
            }) : bin.count > 0 && <rect x={x + gap / 2} y={76 - height} width={Math.max(0, binWidth - gap)} height={height} className="cvt-ungrouped" />}
          </g>;
        })}
      </svg>
      {(unavailable || total === 0) && <span className="cvt-state" role="status">{loading ? 'Loading mapped variants…' : error ? 'Variant data unavailable' : !bins.length ? 'Invalid sequence range' : 'No verified mapped variants in this range'}</span>}
    </div>
    <div className="cvt-legend" id={noteId}>
      <span className="cvt-unit" title="Verified canonical subset only. Counts sum variant–position links across residues, not distinct variants across the range. Heights use the largest bin in the current view; colours are existing ClinVar source-label groups, not prediction scores.">{loading || error ? 'Variant–position links' : `${total.toLocaleString()} links`}<span aria-hidden="true"> · </span></span>
      {categories.map(category => <span key={category.key} title={category.label}><i style={{ background: category.color }} />{category.short}</span>)}
      <span className="cvt-scale" title="Vertical scale is relative to the largest bin in the current view.">max {unavailable?'—':max === 1 && !total ? 0 : max}</span>
    </div>
    {typeof document !== 'undefined' && createPortal(<AnimatePresence>{preview && previewBin && !unavailable &&
      <motion.div className="cvt-tooltip" id={tooltipId} role="tooltip" initial={{opacity:reduceMotion?1:0,y:reduceMotion?0:3}} animate={{opacity:1,y:0}} exit={{opacity:0,y:reduceMotion?0:2}} transition={{duration:reduceMotion?0:.12}} style={{
        left: Math.max(8, Math.min(window.innerWidth - Math.min(288, window.innerWidth - 16) - 8, preview.x - Math.min(288, window.innerWidth - 16) / 2)),
        ...(preview.top > 255 ? { bottom: Math.max(8, window.innerHeight - preview.top + 8) } : { top: Math.max(8, Math.min(preview.bottom + 8, window.innerHeight - 248)) }),
      }}>
        <strong>{previewBin.start === previewBin.end ? `Residue ${previewBin.start}` : `Residues ${previewBin.start}–${previewBin.end}`}</strong>
        <span className="cvt-tooltip-total">{previewBin.count.toLocaleString()} variant–position links</span>
        {previewBin.groupingComplete ? categories.map(category => <span className="cvt-tooltip-category" key={category.key}><i style={{ background: category.color }} /><span>{category.label}</span><b>{previewBin.counts[category.key].toLocaleString()}</b></span>) : <span>ClinVar grouping unavailable or incomplete.</span>}
        <small>Verified canonical subset · click to select this range</small>
      </motion.div>}</AnimatePresence>, document.body,
    )}
  </div>;
}

export default CompactVariantTrack;
