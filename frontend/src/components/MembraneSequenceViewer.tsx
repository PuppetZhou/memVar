import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, label } from '../api';
import { LinkOut, Status } from './ui';
import MembraneTrack, { membraneColor } from './MembraneTrack';
import SequenceRangeNavigator from './SequenceRangeNavigator';

type Feature = { id: string; source_type: string; start: number | null; end: number | null; description?: string | null; can_locate_exactly?: boolean };
type OpmObservation = { model: number | null; source_position: string; source_residue: string | null; geometry: string | null; depth: number | null; basis: string | null };
type OpmStructure = { pdb_id: string; chain_id: string | null; observations: OpmObservation[] };
type OpmPosition = { position: number; residue: string; structures: OpmStructure[] };
type Projection = { sequence: string; opm: { positions: OpmPosition[]; unmapped_records: { pdb_id: string; chain_id: string | null; first_source_position: number; last_source_position: number; geometry_types: string[] }[]; unmapped_has_more: boolean } };
type DepthPoint = OpmObservation & { position: number; residue: string; pdb: string; chain: string | null };
const depthText = (depth: number | null) => depth == null ? 'Not available' : `${depth > 0 ? '+' : ''}${depth.toFixed(2)} Å`;
const geometryText = (geometry: string | null) => geometry ? label(geometry) : 'Not supplied';

function OpmResidueTable({ positions }: { positions: OpmPosition[] }) {
  return <div className="table-wrap membrane-evidence-table"><table className="data-table"><thead><tr><th>Residue</th><th>PDB / chain</th><th>PDB residue</th><th>OPM geometry</th><th>Depth (Å)</th></tr></thead><tbody>{positions.flatMap(item => item.structures.flatMap((structure, si) => (structure.observations ?? []).map((observation, oi) => <tr key={`${item.position}:${si}:${oi}`}><td><strong>{item.residue}{item.position}</strong></td><td><LinkOut href={`https://www.rcsb.org/structure/${structure.pdb_id}`}>{structure.pdb_id.toUpperCase()}</LinkOut> · {structure.chain_id ?? '—'}{structure.observations.length > 1 && <small className="membrane-cell-note">Model {observation.model ?? '—'}</small>}</td><td>{observation.source_residue} {observation.source_position}</td><td>{geometryText(observation.geometry)}</td><td title={observation.basis ?? ''}>{depthText(observation.depth)}</td></tr>)))}</tbody></table></div>;
}

function OpmDepth({ positions, selected, onSelect }: { positions: OpmPosition[]; selected: number | null; onSelect: (position: number) => void }) {
  const groups = new Map<string, DepthPoint[]>();
  for (const item of positions) for (const structure of item.structures) for (const observation of structure.observations ?? []) {
    const key = `${structure.pdb_id.toUpperCase()} · Chain ${structure.chain_id ?? '—'} · Model ${observation.model ?? '—'}`;
    const points = groups.get(key) ?? [];
    points.push({ ...observation, position: item.position, residue: item.residue, pdb: structure.pdb_id, chain: structure.chain_id });
    groups.set(key, points);
  }
  const [choice, setChoice] = useState('');
  const [hovered, setHovered] = useState<DepthPoint | null>(null);
  const key = groups.has(choice) ? choice : [...groups.keys()][0];
  const points = groups.get(key) ?? [];
  const measured = points.filter((p): p is DepthPoint & { depth: number } => p.depth != null && Number.isFinite(p.depth));
  const active = hovered ?? points.find(p => p.position === selected);
  if (!groups.size) return <section className="membrane-depth"><h3>OPM · membrane depth</h3><p className="mov-context-note">No residue geometry is available on this sequence.</p></section>;
  const first = Math.min(...points.map(p => p.position)), last = Math.max(...points.map(p => p.position));
  const low = Math.min(0, ...measured.map(p => p.depth)), high = Math.max(0, ...measured.map(p => p.depth));
  const pad = Math.max(2, (high - low) * .12), bottom = low - pad, top = high + pad;
  const x = (position: number) => 62 + (position - first) / Math.max(1, last - first) * 820;
  const y = (depth: number) => 18 + (top - depth) / (top - bottom) * 142;
  const zero = y(0);
  return <section className="membrane-depth" aria-label="OPM depth by residue">
    <header><div><h3>OPM · membrane depth</h3><span>{[...new Set(points.map(p => geometryText(p.geometry)))].join(' · ')}</span></div><label>PDB / chain<select aria-label="OPM structure and chain" value={key} onChange={event => { setChoice(event.target.value); setHovered(null); }}>{[...groups.keys()].map(value => <option key={value}>{value}</option>)}</select></label></header>
    {measured.length ? <svg viewBox="0 0 920 202" className="membrane-depth-chart" role="group" aria-label={`OPM signed depth for ${key}, sequence residues ${first} to ${last}`}>
      <rect x="62" y="18" width="820" height={Math.max(0, zero - 18)} fill="#e9f3f0" />
      <rect x="62" y={zero} width="820" height={160 - zero} fill="#f0f3f7" />
      {[...new Set([low, 0, high])].map(value => <g key={value}><line x1="62" x2="882" y1={y(value)} y2={y(value)} stroke={value === 0 ? '#7d9390' : '#d9e2e5'} strokeDasharray={value === 0 ? '5 4' : undefined}/><text x="53" y={y(value) + 4} textAnchor="end">{value.toFixed(1)}</text></g>)}
      <text x="12" y="13">Å</text>
      {measured.map((point, i) => <circle key={i} cx={x(point.position)} cy={y(point.depth)} r={selected === point.position || hovered?.position === point.position ? 5 : 3.2} fill={point.depth >= 0 ? '#397f73' : '#74859d'} stroke="white" strokeWidth=".8" tabIndex={0} role="button" aria-label={`${point.residue}${point.position}, depth ${depthText(point.depth)}, PDB residue ${point.source_position}`} onMouseEnter={() => setHovered(point)} onMouseLeave={() => setHovered(null)} onFocus={() => setHovered(point)} onBlur={() => setHovered(null)} onClick={() => onSelect(point.position)} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(point.position); } }} />)}
      {[first, Math.round((first + last) / 2), last].filter((value, index, all) => all.indexOf(value) === index).map(value => <text key={value} x={x(value)} y="181" textAnchor="middle">{value}</text>)}<text x="472" y="199" textAnchor="middle">Sequence residue · N → C</text>
    </svg> : <p className="mov-context-note">Depth values were not supplied for this structure.</p>}
    <div className="membrane-depth-readout" role="status">{active ? <><strong>{active.residue}{active.position}</strong><span>PDB {active.source_residue} {active.source_position}</span><b>{depthText(active.depth)}</b></> : <span>Hover a point to read its residue and depth; click to inspect the residue.</span>}</div>
    <p className="membrane-depth-legend"><span><i style={{ background: '#397f73' }}/>Positive: inside membrane core</span><span><i style={{ background: '#74859d' }}/>Negative: outside core</span></p>
    <p className="mov-context-note">Depth is relative to the membrane boundary, not an intracellular / extracellular direction. {[...new Set(points.map(p => p.basis).filter(Boolean))].map(value => label(value)).join(' · ')}.</p>
  </section>;
}

export default function MembraneSequenceViewer({ accession, summary }: { accession: string; summary: { sequence_id: string; length: number; uniprot: { features: Feature[] } } }) {
  const query = useQuery({ queryKey: ['membrane-sequence-viewer', accession], queryFn: ({ signal }) => api<Projection>(`/proteins/${accession}/overview/membrane/sequence`, signal) });
  const features = summary.uniprot.features.filter((feature): feature is Feature & { start: number; end: number } => feature.can_locate_exactly === true && feature.start != null && feature.end != null);
  const membrane = features.find(feature => /^(Transmembrane|Intramembrane)$/.test(feature.source_type));
  const [range, setRange] = useState<[number, number]>(() => membrane ? [Math.max(1, membrane.start - 25), Math.min(summary.length, membrane.end + 25)] : [1, Math.min(summary.length, 120)]);
  const [selected, setSelected] = useState<number | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const projection = query.data;
  const positions = projection?.opm.positions ?? [];
  const opmByPosition = new Map(positions.map(item => [item.position, item]));
  const atPosition = (position: number) => features.filter(feature => feature.start <= position && feature.end >= position);
  const focus = (start: number, end: number) => setRange([Math.max(1, start - 25), Math.min(summary.length, end + 25)]);
  const inspect = (position: number) => { setSelected(position); if (position < range[0] || position > range[1]) focus(position, position); };
  const active = hovered ?? selected;
  return <div className="mov-sequence-viewer">
    <div className="membrane-view-heading"><h3>Sequence & membrane geometry</h3><span>{summary.sequence_id} · {summary.length.toLocaleString()} aa</span></div>
    <MembraneTrack title="UniProt · topology & membrane regions" length={summary.length} intervals={features.map(feature => ({ id: feature.id, start: feature.start, end: feature.end, name: feature.source_type, description: feature.description ?? '', color: membraneColor(feature.source_type) }))} onSelect={feature => focus(feature.start, feature.end)}/>
    {projection && <OpmDepth positions={positions} selected={selected} onSelect={inspect}/>}
    <div className="membrane-window-heading"><strong>Residue detail</strong><button type="button" onClick={() => { setRange([1, Math.min(120, summary.length)]); setSelected(null); }}>Reset window</button></div>
    <SequenceRangeNavigator length={summary.length} range={range} onRange={setRange}/>
    <Status loading={query.isPending} error={query.error}>{projection && <>
      {range[1] - range[0] < 240 ? <div className="mov-residue-grid" aria-label={`Sequence residues ${range[0]} to ${range[1]}`}>{Array.from(projection.sequence.slice(range[0] - 1, range[1])).map((residue, index) => {
        const position = range[0] + index, annotations = atPosition(position), opm = opmByPosition.get(position);
        const isMembrane = annotations.some(feature => /^(Transmembrane|Intramembrane)$/.test(feature.source_type));
        return <button key={position} type="button" aria-label={`${residue}${position}${annotations.length ? ` · ${annotations.map(f => `${f.source_type} ${f.start}–${f.end} ${f.description ?? ''}`).join('; ')}` : ''}${opm ? ' · OPM' : ''}`} className={`${isMembrane ? 'is-membrane ' : ''}${opm ? 'has-opm ' : ''}${selected === position ? 'selected' : ''}`} onMouseEnter={() => setHovered(position)} onMouseLeave={() => setHovered(null)} onFocus={() => setHovered(position)} onBlur={() => setHovered(null)} onClick={() => setSelected(position)}><small>{position}</small><strong>{residue}</strong>{opm && <i aria-label="OPM observation"/>}</button>;
      })}</div> : <p className="mov-sequence-zoom-note">Narrow the window to 240 residues to show sequence letters.</p>}
      <div className="membrane-residue-readout" role="status">{active == null ? 'Hover a residue for annotations. Click to keep its structure evidence below.' : <><strong>{projection.sequence[active - 1]}{active}</strong>{atPosition(active).map(feature => <span key={feature.id}>{feature.source_type} · {feature.start}–{feature.end}{feature.description ? ` · ${feature.description}` : ''}</span>)}{opmByPosition.has(active) && <span>OPM · {opmByPosition.get(active)!.structures.length} PDB / chain records</span>}{!atPosition(active).length && !opmByPosition.has(active) && <span>No membrane annotation at this residue.</span>}</>}</div>
      {selected != null && <section className="membrane-selected"><header><h3>Residue {projection.sequence[selected - 1]}{selected}</h3><button type="button" onClick={() => setSelected(null)}>Clear selection</button></header>{opmByPosition.has(selected) ? <OpmResidueTable positions={[opmByPosition.get(selected)!]}/> : <p className="mov-context-note">No OPM structure observation at this residue.</p>}</section>}
      {projection.opm.unmapped_records.length > 0 && <section className="membrane-selected"><h3>Additional OPM structures · PDB numbering</h3><div className="table-wrap membrane-evidence-table"><table className="data-table"><thead><tr><th>PDB / chain</th><th>PDB residue interval</th><th>OPM geometry</th></tr></thead><tbody>{projection.opm.unmapped_records.map((item, i) => <tr key={i}><td><LinkOut href={`https://www.rcsb.org/structure/${item.pdb_id}`}>{item.pdb_id.toUpperCase()}</LinkOut> · {item.chain_id ?? '—'}</td><td>{item.first_source_position}–{item.last_source_position}</td><td>{item.geometry_types.map(geometryText).join(', ')}</td></tr>)}</tbody></table></div>{projection.opm.unmapped_has_more && <p className="mov-context-note">First 100 structure groups shown.</p>}</section>}
    </>}</Status>
  </div>;
}
