import { useEffect, useId, useRef, useState, type PointerEvent } from 'react';
import type { Range } from './SequenceAnnotations';

type Drag = { mode: 'select' | 'start' | 'end'; anchor: number; initial: Range; pointerId: number };
const TRACK_INSET = 24;

/** Changes only the displayed annotation window; search and residue focus stay independent. */
export default function SequenceRangeNavigator({ length, range, onRange }: { length: number; range: Range; onRange: (range: Range) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const drag = useRef<Drag | null>(null);
  const helpId = useId();
  const [width, setWidth] = useState(800);
  const [preview, setPreview] = useState<Range | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const [hover, setHover] = useState<number | null>(null);
  useEffect(() => {
    const element = host.current;
    if (!element) return;
    const observer = new ResizeObserver(entries => setWidth(Math.max(1, entries[0].contentRect.width)));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  useEffect(() => { drag.current = null; setPreview(null); }, [length, range[0], range[1]]);
  useEffect(() => { setAnnouncement(''); }, [length]);
  const shown = preview ?? range;
  const trackWidth = Math.max(1, width - TRACK_INSET * 2);
  const clamp = (position: number) => Math.max(1, Math.min(length, position));
  // Unclamped coordinates preserve pointer deltas when a handle sits outside the track.
  const pointerPosition = (event: PointerEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    return 1 + Math.floor(((event.clientX - box.left) * width / box.width - TRACK_INSET) / trackWidth * length);
  };
  const pending = (position: number): Range => {
    const state = drag.current!;
    if (state.mode === 'start') return [Math.min(clamp(state.initial[0] + position - state.anchor), state.initial[1]), state.initial[1]];
    if (state.mode === 'end') return [state.initial[0], Math.max(clamp(state.initial[1] + position - state.anchor), state.initial[0])];
    const next = clamp(position);
    return [Math.min(state.anchor, next), Math.max(state.anchor, next)];
  };
  const cancelDrag = (element?: SVGSVGElement) => {
    const state = drag.current;
    if (!state) return;
    drag.current = null;
    setPreview(null);
    setAnnouncement(`Window change cancelled. Window ${state.initial[0]}–${state.initial[1]} restored.`);
    if (element?.hasPointerCapture(state.pointerId)) element.releasePointerCapture(state.pointerId);
  };
  const reset = () => {
    drag.current = null;
    setPreview(null);
    onRange([1, length]);
    setAnnouncement(`Full sequence visible. Window 1–${length}.`);
  };
  const tickCount = Math.max(2, Math.min(7, Math.floor(trackWidth / 100) + 1));
  const ticks = [...new Set(Array.from({ length: tickCount }, (_, i) => Math.round(1 + (length - 1) * i / (tickCount - 1))))];
  const left = TRACK_INSET + (shown[0] - 1) / length * trackWidth;
  const right = TRACK_INSET + shown[1] / length * trackWidth;
  return <div className="sequence-range-navigator" ref={host}>
    <div className="range-navigator-caption"><strong>{preview ? 'Preview: ' : 'Visible window: '}{shown[0].toLocaleString()}–{shown[1].toLocaleString()}</strong><span>{(shown[1] - shown[0] + 1).toLocaleString()} aa</span></div>
    <svg viewBox={`0 0 ${width} 48`} role="group" tabIndex={-1} aria-label="Adjust visible sequence window" aria-describedby={helpId} onDoubleClick={reset}
      onKeyDown={event => { if (event.key === 'Escape' && drag.current) { event.preventDefault(); cancelDrag(event.currentTarget); } }}
      onPointerDown={event => {
        if (event.button !== 0) return;
        const handleElement = (event.target as Element).closest<SVGGElement>('[data-range-handle]');
        const handle = handleElement?.getAttribute('data-range-handle');
        const mode = handle === 'start' || handle === 'end' ? handle : 'select';
        const position = pointerPosition(event);
        drag.current = { mode, anchor: mode === 'select' ? clamp(position) : position, initial: range, pointerId: event.pointerId };
        setPreview(pending(position));
        setHover(mode==='start'?range[0]:mode==='end'?range[1]:clamp(position));
        setAnnouncement('');
        (handleElement ?? event.currentTarget).focus({ preventScroll: true });
        event.currentTarget.setPointerCapture(event.pointerId);
        event.preventDefault();
      }}
      onPointerMove={event => { const position=pointerPosition(event); if (drag.current) { const next=pending(position); setPreview(next); setHover(drag.current.mode==='start'?next[0]:drag.current.mode==='end'?next[1]:clamp(position)); } else { const handle=(event.target as Element).closest('[data-range-handle]')?.getAttribute('data-range-handle'); setHover(handle==='start'?shown[0]:handle==='end'?shown[1]:clamp(position)); } }}
      onPointerLeave={() => { if (!drag.current) setHover(null); }}
      onPointerUp={event => {
        if (!drag.current) return;
        const next = pending(pointerPosition(event));
        drag.current = null;
        setPreview(null);
        onRange(next);
        setAnnouncement(`Window ${next[0]}–${next[1]} applied.`);
        if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
      }}
      onPointerCancel={event => cancelDrag(event.currentTarget)}
      onLostPointerCapture={() => cancelDrag()}>
      <rect className="range-track" x={TRACK_INSET} y="11" width={trackWidth} height="6" rx="3" />
      <rect className="range-selection" x={left} y="11" width={Math.max(1, right - left)} height="6" rx="3" />
      {(['start', 'end'] as const).map((handle, index) => {
        const edge = index === 0 ? left : right;
        const value = shown[index];
        return <g key={handle} data-range-handle={handle} role="slider" tabIndex={0} aria-label={`Sequence window ${handle} handle`} aria-orientation="horizontal" aria-valuemin={handle === 'start' ? 1 : shown[0]} aria-valuemax={handle === 'start' ? shown[1] : length} aria-valuenow={value} aria-valuetext={`Residue ${value}; visible window ${shown[0]}–${shown[1]} of ${length}`} aria-describedby={helpId} onFocus={() => setHover(value)} onBlur={() => setHover(null)}
          onKeyDown={event => {
            const step = event.shiftKey ? 10 : 1;
            const change = event.key === 'ArrowLeft' || event.key === 'ArrowDown' ? -step : event.key === 'ArrowRight' || event.key === 'ArrowUp' ? step : event.key === 'PageUp' ? 10 : event.key === 'PageDown' ? -10 : 0;
            if (!change && event.key !== 'Home' && event.key !== 'End') return;
            event.preventDefault();
            const minimum = handle === 'start' ? 1 : range[0], maximum = handle === 'start' ? range[1] : length;
            const nextValue = event.key === 'Home' ? minimum : event.key === 'End' ? maximum : Math.max(minimum, Math.min(maximum, range[index] + change));
            const next: Range = handle === 'start' ? [nextValue, range[1]] : [range[0], nextValue];
            setHover(nextValue);
            onRange(next);
            setAnnouncement(`Window ${next[0]}–${next[1]} applied.`);
          }}>
          <rect className="range-handle-hit" x={index === 0 ? edge - 24 : edge} y="0" width="24" height="28" rx="4" />
          <circle className="range-handle" cx={edge + (index === 0 ? -6 : 6)} cy="14" r="6" />
        </g>;
      })}
      <g aria-hidden="true" pointerEvents="none">{ticks.map((position, index) => {
        const x = TRACK_INSET + (position - 1) / Math.max(1, length - 1) * trackWidth;
        return <g key={position}><line x1={x} x2={x} y1="25" y2="29"/><text x={x} y="43" textAnchor={index === 0 ? 'start' : index === ticks.length - 1 ? 'end' : 'middle'}>{position.toLocaleString()}</text></g>;
      })}</g>
    </svg>
    {hover!=null&&<span className="range-residue-readout" style={{left:`clamp(52px, ${TRACK_INSET+(hover-.5)/length*trackWidth}px, calc(100% - 52px))`}}>Residue {hover.toLocaleString()}</span>}
    <span id={helpId} className="range-navigator-status">Click to show one residue, or drag for a window. Arrow keys adjust a focused endpoint; Shift moves ten residues. Escape cancels a drag. Window changes keep search matches and selected residue.</span>
    <span className="range-navigator-status" role="status" aria-live="polite">{announcement}</span>
  </div>;
}
