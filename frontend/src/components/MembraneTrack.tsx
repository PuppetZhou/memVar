import { useId, useState } from 'react';

export type TrackInterval = { id: string; start: number; end: number; name: string; description?: string; color?: string };
export const membraneColor = (name: string) => /transmembrane|^membrane$|^M$|TMhelix|TMbeta/i.test(name) ? '#c47c13' : /signal|^s$/.test(name.toLowerCase()) ? '#9470af' : /intramembrane/i.test(name) ? '#a855c7' : /cytoplasmic|^Inside$|^I$/.test(name) ? '#598d87' : '#7891ab';

/** Intervals supplied by the caller must share the explicitly labelled sequence coordinate system. */
export default function MembraneTrack({ title, length, intervals, onSelect }: { title: string; length: number; intervals: TrackInterval[]; onSelect?: (interval: TrackInterval) => void }) {
  const [active, setActive] = useState<TrackInterval | null>(null);
  const hintId = useId();
  const valid = intervals.filter(item => item.start >= 1 && item.end >= item.start && item.end <= length);
  return <section className="membrane-track" aria-label={title}>
    <header><strong>{title}</strong><span>N → C · {length.toLocaleString()} aa</span></header>
    <div className="membrane-track-bar">{valid.map(item => <button key={item.id} type="button" aria-label={`${item.name} ${item.start}–${item.end}${item.description ? ` · ${item.description}` : ''}`} aria-describedby={hintId}
      style={{ left: `${(item.start - 1) / length * 100}%`, width: `${(item.end - item.start + 1) / length * 100}%`, background: item.color ?? membraneColor(item.name) }}
      onMouseEnter={() => setActive(item)} onMouseLeave={() => setActive(null)} onFocus={() => setActive(item)} onBlur={() => setActive(null)} onClick={() => onSelect?.(item)}>
      {(item.end - item.start + 1) / length > .13 && <span>{item.description || item.name}</span>}
    </button>)}</div>
    <div className="membrane-track-axis"><span>1</span><span>{Math.round(length / 2).toLocaleString()}</span><span>{length.toLocaleString()}</span></div>
    <div id={hintId} className={`membrane-track-hint${active ? ' is-active' : ''}`} role="status">{active ? <><strong>{active.name}</strong><b>{active.start}–{active.end}</b><span>{active.description}</span></> : <span>{valid.length ? 'Hover or focus a segment to read its annotation.' : 'No intervals available for this sequence.'}</span>}</div>
  </section>;
}
