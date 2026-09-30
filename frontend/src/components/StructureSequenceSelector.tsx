import { useId, useLayoutEffect, useMemo, useRef, useState, type KeyboardEvent, type PointerEvent } from 'react';
import { RotateCcw, ScanLine } from 'lucide-react';
import { Button } from './ui/button';
import './structure-sequence-selector.css';

type Range = [number, number];
type MappedResidue = { position: number; chain_id: string; auth_residue_number: number; insertion_code: string };
type Drag = { anchor: number; edge: 0 | 1 | null; before: Range | null; next: Range; focus: number };

export default function StructureSequenceSelector({ sequence, mapping, value, focusedPosition, onCommit, onClear }: {
  sequence: string; mapping: MappedResidue[]; value: Range | null; focusedPosition?: number | null;
  onCommit: (range: Range, focus: number) => void; onClear: () => void;
}) {
  const length = sequence.length;
  const [preview, setPreview] = useState<Range | null>(null);
  const [dragging, setDragging] = useState(false);
  const [hovered, setHovered] = useState<number | null>(null);
  const drag = useRef<Drag | null>(null);
  const selector = useRef<HTMLDivElement>(null);
  const keyboardEdge = useRef<0 | 1 | null>(null);
  const overview = useRef<HTMLDivElement>(null);
  const captionId = useId();
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
  useLayoutEffect(() => {
    if (keyboardEdge.current === null) return;
    const handle = selector.current?.querySelector<HTMLButtonElement>(`.ssc-overview-handle[data-edge="${keyboardEdge.current}"]`);
    if (handle) { handle.focus({ preventScroll: true }); keyboardEdge.current = null; }
  }, [value?.[0], value?.[1]]);

  function pointerPosition(event: PointerEvent<HTMLDivElement>) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const fraction = Math.max(0, Math.min(.999999, (event.clientX - bounds.left) / bounds.width));
    return 1 + Math.floor(fraction * length);
  }
  function begin(event: PointerEvent<HTMLDivElement>) {
    if (event.button !== 0) return;
    const position = pointerPosition(event);
    const rawEdge = (event.target as HTMLElement).closest<HTMLElement>('[data-edge]')?.dataset.edge;
    const edge = value && rawEdge !== undefined ? Number(rawEdge) as 0 | 1 : null;
    const next: Range = edge === null ? [position, position] : [...value!];
    drag.current = { anchor: position, edge, before: value, next, focus: edge === null ? position : next[edge] };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.currentTarget.focus({ preventScroll: true });
    setPreview(next); setDragging(true);
  }
  function move(event: PointerEvent<HTMLDivElement>) {
    const rawPosition = pointerPosition(event);
    const current = drag.current;
    const hoveredEdge = (event.target as HTMLElement).closest<HTMLElement>('[data-edge]')?.dataset.edge;
    const position = current?.edge != null ? Math.max(1, Math.min(length, rawPosition + current.before![current.edge] - current.anchor))
      : !current && value && hoveredEdge !== undefined ? value[Number(hoveredEdge) as 0 | 1] : rawPosition;
    setHovered(position);
    if (!current) return;
    const next: Range = current.edge === 0 ? [Math.min(position, current.before![1]), current.before![1]]
      : current.edge === 1 ? [current.before![0], Math.max(position, current.before![0])]
      : [Math.min(current.anchor, position), Math.max(current.anchor, position)];
    current.next = next; current.focus = current.edge === null ? position : next[current.edge];
    setPreview(next);
  }
  function finish(event: PointerEvent<HTMLDivElement>) {
    if (!drag.current) return;
    move(event);
    const current = drag.current;
    drag.current = null; setDragging(false); setPreview(null);
    onCommit(current.next, current.focus);
  }
  function cancel() {
    drag.current = null; setDragging(false); setPreview(null);
  }
  function clear() {
    cancel(); keyboardEdge.current = null; setHovered(null); onClear();
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
  function startFromKeyboard(event: KeyboardEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget || !['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Enter', ' '].includes(event.key)) return;
    event.preventDefault();
    const position = event.key === 'End' ? length : event.key === 'Home' ? 1
      : Math.max(1, Math.min(length, (focusedPosition ?? value?.[0] ?? 1) + (event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0)));
    keyboardEdge.current = 1;
    onCommit([position, position], position);
  }
  const pointerHandlers = {
    onPointerDown: begin, onPointerMove: move, onPointerUp: finish,
    onPointerCancel: () => { cancel(); setHovered(null); },
    onPointerLeave: () => { if (!drag.current) setHovered(null); },
  };
  const hoverMapping = hovered == null ? undefined : positions.get(hovered);

  return <div className="ssc" ref={selector} onKeyDown={escape}>
    <header className="ssc-heading"><h3><ScanLine size={17}/>3D structure selection</h3><span className={dragging ? 'ssc-preview-state' : ''} role="status">
      {shown ? <><strong>{dragging ? 'Preview: ' : ''}{residue(shown[0])}–{residue(shown[1])}</strong><span>{shown[1] - shown[0] + 1} aa · {mappedCount} mapped</span></> : 'No structure range selected'}
    </span><Button variant="outline" size="sm" className="ssc-reset" onClick={clear} title="Clear the structure range and shared residue focus"><RotateCcw size={15}/>Reset structure selection</Button></header>
    <div className="ssc-overview-label"><span>Full sequence <b>{length.toLocaleString()} aa</b></span><span><i className="ssc-mapped-key"/>Mapped<i className="ssc-selected-key"/>Selected range</span></div>
    <div className="ssc-overview" ref={overview} tabIndex={0} role="group" aria-label="Full sequence structure range selector" aria-describedby={captionId} onKeyDown={startFromKeyboard} {...pointerHandlers}>
      <div className="ssc-overview-track" aria-hidden="true">{segments.map(([start, end]) => <i key={start} className="ssc-mapped-segment" style={{ left: `${(start - 1) / length * 100}%`, width: `${(end - start + 1) / length * 100}%` }}/>)}</div>

      {shown && <div className={`ssc-overview-selection${dragging ? ' is-preview' : ''}`} aria-hidden="true" style={{ left: `${(shown[0] - 1) / length * 100}%`, width: `max(4px, ${(shown[1] - shown[0] + 1) / length * 100}%)` }}/>}
      {shown && ([0,1] as const).map(edge => <button key={edge} type="button" className={`ssc-overview-handle ssc-overview-handle-${edge}${(shown[1]-shown[0]+1)/length<.15?" is-close":""}`} data-near-start={shown[edge]/length<.1} data-near-end={shown[edge]/length>.9} data-edge={edge} role="slider" aria-label={`Full sequence range ${edge===0?'start':'end'} handle`} aria-orientation="horizontal" aria-describedby={captionId} aria-valuemin={edge===0?1:shown[0]} aria-valuemax={edge===0?shown[1]:length} aria-valuenow={shown[edge]} aria-valuetext={residue(shown[edge])} style={{left:`${(shown[edge]-1+(edge===1?1:0))/length*100}%`}} onKeyDown={event=>moveEdge(event,edge)}><i className="ssc-thumb" aria-hidden="true"/><span>{edge===0?'Start':'End'} {residue(shown[edge])}</span></button>)}
      {hovered != null && <div className="ssc-hover-readout" role="tooltip" style={{ left: `${(hovered - 1) / Math.max(1, length - 1) * 100}%`, transform: hovered < length * .15 ? 'none' : hovered > length * .85 ? 'translateX(-100%)' : 'translateX(-50%)' }}><strong>{residue(hovered)}</strong><span>{hoverMapping ? `Chain ${hoverMapping.chain_id} · residue ${hoverMapping.auth_residue_number}${hoverMapping.insertion_code ?? ''}` : 'Not mapped to this structure'}</span></div>}
      <div className="ssc-overview-ticks" aria-hidden="true">{[0, .25, .5, .75, 1].map(fraction => <span key={fraction}>{Math.max(1, Math.round(length * fraction)).toLocaleString()}</span>)}</div>
    </div>
    <p className="ssc-caption" id={captionId} title="Reset clears the structure range and shared residue focus; variant filters stay unchanged.">Hover for residue · Drag to select a range · Arrow keys adjust endpoints · Esc clears selection.</p>
  </div>;
}
