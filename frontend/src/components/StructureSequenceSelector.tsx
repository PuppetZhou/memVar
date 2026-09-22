import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent, type PointerEvent } from 'react';
import { ChevronLeft, ChevronRight, Crosshair, RotateCcw, ScanLine } from 'lucide-react';
import { Button } from './ui/button';
import './structure-sequence-selector.css';

type Range = [number, number];
type MappedResidue = { position: number; chain_id: string; auth_residue_number: number; insertion_code: string };
type Drag = { anchor: number; edge: 0 | 1 | null; before: Range | null; next: Range; focus: number };
const WINDOW_SIZE = 32;

export default function StructureSequenceSelector({ sequence, mapping, value, focusedPosition, onCommit, onClear }: {
  sequence: string; mapping: MappedResidue[]; value: Range | null; focusedPosition?: number | null;
  onCommit: (range: Range, focus: number) => void; onClear: () => void;
}) {
  const length = sequence.length;
  const [windowStart, setWindowStart] = useState(1);
  const [preview, setPreview] = useState<Range | null>(null);
  const [dragging, setDragging] = useState(false);
  const [draft, setDraft] = useState({ start: '', end: '' });
  const [error, setError] = useState('');
  const drag = useRef<Drag | null>(null);
  const selector = useRef<HTMLDivElement>(null);
  const residueStrip = useRef<HTMLDivElement>(null);
  const keyboardEdge = useRef<0 | 1 | null>(null);
  const overview = useRef<HTMLDivElement>(null);
  const captionId = useId();
  const windowEnd = Math.min(length, windowStart + WINDOW_SIZE - 1);
  const visibleCount = windowEnd - windowStart + 1;
  const shown = dragging ? preview : value;
  const positions = useMemo(() => new Map(mapping.map(residue => [residue.position, residue])), [mapping]);
  const segments = useMemo(() => {
    const result: Range[] = [];
    for (const position of [...positions.keys()].sort((a, b) => a - b)) {
      const last = result.at(-1);
      if (last && position === last[1] + 1) last[1] = position;
      else result.push([position, position]);
    }
    return result;
  }, [positions]);
  const mappedCount = shown ? mapping.filter(residue => residue.position >= shown[0] && residue.position <= shown[1]).length : 0;
  const residue = (position: number) => `${sequence[position - 1] ?? '?'}${position}`;
  const clampWindow = (start: number) => Math.max(1, Math.min(Math.max(1, length - WINDOW_SIZE + 1), start));
  const showPosition = (position: number) => setWindowStart(clampWindow(position - Math.floor(WINDOW_SIZE / 2)));

  useEffect(() => {
    setDraft({ start: value ? String(value[0]) : '', end: value ? String(value[1]) : '' });
    setError('');
    if (value) setWindowStart(current => {
      if (value[0] >= current && value[1] < current + WINDOW_SIZE) return current;
      if (value[1] - value[0] < WINDOW_SIZE) {
        const centered = Math.floor((value[0] + value[1]) / 2) - Math.floor(WINDOW_SIZE / 2);
        // A 32-residue range must keep both endpoints in the even-sized window.
        return clampWindow(Math.max(value[1] - WINDOW_SIZE + 1, Math.min(value[0], centered)));
      }
      return clampWindow((focusedPosition ?? value[0]) - Math.floor(WINDOW_SIZE / 2));
    });
  // Window browsing is independent; recenter only when the committed range changes.
  }, [value?.[0], value?.[1], length]);

  useEffect(() => {
    const strip=residueStrip.current;
    if(!strip)return;
    let accumulated=0;
    const wheel=(event:WheelEvent)=>{
      if(event.ctrlKey||event.metaKey||drag.current)return;
      const delta=(Math.abs(event.deltaX)>Math.abs(event.deltaY)?event.deltaX:event.deltaY)*(event.deltaMode===1?16:event.deltaMode===2?strip.clientWidth:1);
      if(!delta)return;
      const atBoundary=(delta<0&&windowStart===1)||(delta>0&&windowEnd===length);
      if(atBoundary)return;
      event.preventDefault();
      accumulated+=delta;
      const step=Math.trunc(accumulated/24);
      if(step){accumulated-=step*24;setWindowStart(current=>clampWindow(current+step));}
    };
    strip.addEventListener('wheel',wheel,{passive:false});
    return ()=>strip.removeEventListener('wheel',wheel);
  },[windowStart,windowEnd,length]);

  useLayoutEffect(() => {
    if (keyboardEdge.current === null) return;
    const handle = selector.current?.querySelector<HTMLButtonElement>(`.ssc-overview-handle[data-edge="${keyboardEdge.current}"]`);
    if (handle) { handle.focus({ preventScroll: true }); keyboardEdge.current = null; }
  }, [windowStart, value?.[0], value?.[1]]);

  function pointerPosition(event: PointerEvent<HTMLDivElement>, local: boolean) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const fraction = Math.max(0, Math.min(.999999, (event.clientX - bounds.left) / bounds.width));
    return (local ? windowStart : 1) + Math.floor(fraction * (local ? visibleCount : length));
  }
  function begin(event: PointerEvent<HTMLDivElement>, local: boolean) {
    if (event.button !== 0) return;
    const position = pointerPosition(event, local);
    const rawEdge = (event.target as HTMLElement).closest<HTMLElement>('[data-edge]')?.dataset.edge;
    const edge = value && rawEdge !== undefined ? Number(rawEdge) as 0 | 1 : null;
    const next: Range = edge === null ? [position, position] : [...value!];
    drag.current = { anchor: position, edge, before: value, next, focus: edge === null ? position : next[edge] };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.currentTarget.focus({ preventScroll: true });
    setPreview(next); setDragging(true);
  }
  function move(event: PointerEvent<HTMLDivElement>, local: boolean) {
    const rawPosition = pointerPosition(event, local);
    const current = drag.current;
    const hoveredEdge = (event.target as HTMLElement).closest<HTMLElement>('[data-edge]')?.dataset.edge;
    const position = current?.edge != null ? Math.max(1, Math.min(length, rawPosition + current.before![current.edge] - current.anchor))
      : !current && value && hoveredEdge !== undefined ? value[Number(hoveredEdge) as 0 | 1] : rawPosition;
    if (!current) return;
    const next: Range = current.edge === 0 ? [Math.min(position, current.before![1]), current.before![1]]
      : current.edge === 1 ? [current.before![0], Math.max(position, current.before![0])]
      : [Math.min(current.anchor, position), Math.max(current.anchor, position)];
    current.next = next; current.focus = current.edge === null ? position : next[current.edge];
    setPreview(next);
  }
  function finish(event: PointerEvent<HTMLDivElement>, local: boolean) {
    if (!drag.current) return;
    move(event, local);
    const current = drag.current;
    drag.current = null; setDragging(false); setPreview(null);
    onCommit(current.next, current.focus);
  }
  function cancel() {
    drag.current = null; setDragging(false); setPreview(null);
  }
  function clear() {
    cancel(); keyboardEdge.current = null; setError(''); setWindowStart(1); onClear();
    requestAnimationFrame(() => overview.current?.focus({ preventScroll: true }));
  }
  function escape(event: KeyboardEvent) {
    if (event.key !== 'Escape') return;
    event.preventDefault(); event.stopPropagation();
    if (drag.current) cancel(); else if (value || focusedPosition) clear();
  }
  function moveEdge(event: KeyboardEvent<HTMLButtonElement>, edge: 0 | 1) {
    if (!value || !['ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) return;
    event.preventDefault(); event.stopPropagation();
    const minimum = edge === 0 ? 1 : value[0], maximum = edge === 0 ? value[1] : length;
    const next = event.key === 'Home' ? minimum : event.key === 'End' ? maximum
      : Math.max(minimum, Math.min(maximum, value[edge] + (event.key === 'PageUp' ? -10 : event.key === 'PageDown' ? 10 : event.key === 'ArrowLeft' ? -1 : 1)));
    if (next === value[edge]) return;
    const range: Range = [...value]; range[edge] = next;
    keyboardEdge.current = edge;
    onCommit(range, next);
  }
  function apply(event: FormEvent) {
    event.preventDefault();
    const start = Number(draft.start), end = Number(draft.end);
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 1 || end < start || end > length) {
      setError(`Use canonical positions 1–${length.toLocaleString()}, with end at or after start.`); return;
    }
    cancel(); setError(''); onCommit([start, end], end);
  }
  const pointerHandlers = (local: boolean) => ({
    onPointerDown: (event: PointerEvent<HTMLDivElement>) => begin(event, local),
    onPointerMove: (event: PointerEvent<HTMLDivElement>) => move(event, local),
    onPointerUp: (event: PointerEvent<HTMLDivElement>) => finish(event, local),
    onPointerCancel: cancel,
  });

  return <div className="ssc" ref={selector} onKeyDown={escape}>
    <header className="ssc-heading"><h3><ScanLine size={17}/>3D structure selection</h3><span className={dragging ? 'ssc-preview-state' : ''} role="status">
      {shown ? <><strong>{dragging ? 'Preview: ' : ''}{residue(shown[0])}–{residue(shown[1])}</strong><span>{shown[1] - shown[0] + 1} aa · {mappedCount} mapped</span></> : 'No structure range selected'}
    </span><Button variant="outline" size="sm" className="ssc-reset" onClick={clear} title="Clear the structure range and shared residue focus; return local sequence view to the start"><RotateCcw size={15}/>Reset structure selection</Button></header>
    <div className="ssc-overview-label"><span>Full sequence <b>{length.toLocaleString()} aa</b></span><span><i className="ssc-mapped-key"/>Mapped<i className="ssc-selected-key"/>Selected range<i className="ssc-window-key"/>Local window</span></div>
    <div className="ssc-overview" ref={overview} tabIndex={0} role="group" aria-label="Full sequence structure range selector" aria-describedby={captionId} {...pointerHandlers(false)}>
      <div className="ssc-overview-track" aria-hidden="true">{segments.map(([start, end]) => <i key={start} className="ssc-mapped-segment" style={{ left: `${(start - 1) / length * 100}%`, width: `${(end - start + 1) / length * 100}%` }}/>)}</div>
      <div className="ssc-window" aria-hidden="true" style={{ left: `${(windowStart - 1) / length * 100}%`, width: `${visibleCount / length * 100}%` }}/>
      {shown && <div className={`ssc-overview-selection${dragging ? ' is-preview' : ''}`} aria-hidden="true" style={{ left: `${(shown[0] - 1) / length * 100}%`, width: `max(4px, ${(shown[1] - shown[0] + 1) / length * 100}%)` }}/>}
      {shown && ([0,1] as const).map(edge => <button key={edge} type="button" className={`ssc-overview-handle ssc-overview-handle-${edge}${(shown[1]-shown[0]+1)/length<.15?" is-close":""}`} data-near-start={shown[edge]/length<.1} data-near-end={shown[edge]/length>.9} data-edge={edge} role="slider" aria-label={`Full sequence range ${edge===0?'start':'end'} handle`} aria-orientation="horizontal" aria-describedby={captionId} aria-valuemin={edge===0?1:shown[0]} aria-valuemax={edge===0?shown[1]:length} aria-valuenow={shown[edge]} aria-valuetext={residue(shown[edge])} style={{left:`${(shown[edge]-1+(edge===1?1:0))/length*100}%`}} onKeyDown={event=>moveEdge(event,edge)}><i className="ssc-thumb" aria-hidden="true"/><span>{edge===0?'Start':'End'} {residue(shown[edge])}</span></button>)}
      <div className="ssc-overview-ticks" aria-hidden="true">{[0, .25, .5, .75, 1].map(fraction => <span key={fraction}>{Math.max(1, Math.round(length * fraction)).toLocaleString()}</span>)}</div>
    </div>
    <div className="ssc-local-heading"><strong>Visible residues {windowStart}–{windowEnd}</strong><span>Scroll to browse left / right · click or drag to select.</span><div>
      {value && <><Button variant="ghost" size="sm" onClick={() => showPosition(value[0])}>View start</Button><Button variant="ghost" size="sm" onClick={() => showPosition(value[1])}>View end</Button></>}
      <Button variant="outline" size="icon-sm" aria-label="Previous residues in structure selector" disabled={windowStart === 1} onClick={() => setWindowStart(current => clampWindow(current - WINDOW_SIZE))}><ChevronLeft/></Button>
      <Button variant="outline" size="icon-sm" aria-label="Next residues in structure selector" disabled={windowEnd === length} onClick={() => setWindowStart(current => clampWindow(current + WINDOW_SIZE))}><ChevronRight/></Button>
    </div></div>
    <div ref={residueStrip} className={`ssc-residues${dragging ? ' is-dragging' : ''}`} tabIndex={0} role="group" aria-label="Local sequence detail; click or drag residues to select a structure range" style={{ gridTemplateColumns: `repeat(${visibleCount}, minmax(0, 1fr))` }} {...pointerHandlers(true)}>
      {Array.from({ length: visibleCount }, (_, index) => {
        const position = windowStart + index, mapped = positions.has(position), selected = !!shown && position >= shown[0] && position <= shown[1];
        const start = shown?.[0] === position, end = shown?.[1] === position, focused = position === focusedPosition;
        return <button type="button" key={position} data-position={position} className={`ssc-residue${selected ? ' is-selected' : ''}${mapped ? '' : ' is-unmapped'}${start ? ' is-start' : ''}${end ? ' is-end' : ''}${focused ? ' is-focused' : ''}`} aria-label={`${residue(position)}, ${mapped ? 'mapped' : 'not mapped'}${focused ? ', shared residue focus' : ''}`} aria-pressed={selected}
          onClick={event => { if (event.detail === 0) onCommit([position, position], position); }}>
          <span>{sequence[position - 1]}</span><small>{position % 5 === 0 || index === 0 || index === visibleCount - 1 || start || end || focused ? position : '\u00a0'}</small>{focused && <i aria-hidden="true"/>}
        </button>;
      })}
    </div>
    <form className="ssc-form" onSubmit={apply}>
      <label>Start<input aria-label="Structure range start" inputMode="numeric" value={draft.start} placeholder="1" aria-invalid={!!error} onChange={event => setDraft(current => ({ ...current, start: event.target.value }))}/></label><span>–</span>
      <label>End<input aria-label="Structure range end" inputMode="numeric" value={draft.end} placeholder={String(length)} aria-invalid={!!error} onChange={event => setDraft(current => ({ ...current, end: event.target.value }))}/></label>
      <Button type="submit" variant="outline" size="sm" disabled={!draft.start.trim() || !draft.end.trim()}>Apply structure range</Button>
      <span className="ssc-shared-focus"><Crosshair size={14}/>{focusedPosition ? `Shared focus: ${residue(focusedPosition)}` : 'No shared residue focus'}</span>

      {error && <span className="ssc-error" role="alert">{error}</span>}
    </form>
    <p className="ssc-caption" id={captionId}>Drag an endpoint to adjust the 3D range, or drag the bar to draw a new range. Arrow keys move a focused endpoint; Esc cancels a drag or clears the selection. Reset clears this range and shared residue focus; variant filters stay unchanged.</p>
  </div>;
}
