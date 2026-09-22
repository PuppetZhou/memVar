import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, ArrowUpRight, Layers, Microscope } from 'lucide-react';
import { api, display, label, number, params, type RecordData } from '../api';
import { Badge, Disclosure, Fields, LinkOut, Modal, Pager, Status } from './ui';
import './membrane-overview.css';
import { HelpButton } from './HelpGuide';
import { HtpPreview, TopologyPortrait, TopologySources, SourceCoverage, type TopologyRecord } from './MembraneTopology';
import SequenceRangeNavigator from './SequenceRangeNavigator';

type MembraneFeature = {
  id: string; source_type: string; start: number | null; end: number | null;
  description?: string | null; label?: string; evidence?: unknown; mapping_status?: string;
  coordinate_status?: string; can_locate_exactly?: boolean; start_modifier?: string; end_modifier?: string;
};
type Segment = { name: string; start: number; end: number; segment_order: number };
type Observation = { source: string; records: number; mapped_positions: number; pdb_entries: number; unit: string };
type TopologySource = { source: string; method: string | null; role: string; records: number; mapped_features: number; mapped_blocks: number; mapping_statuses: string[] };
type OpmStructure = { pdb_id: string; chain_id: string | null; models: number[]; geometry_types: string[]; mapping_methods: string[]; source_positions: string[] };
type OpmPosition = { position: number; residue: string; record_count: number; structures: OpmStructure[] };
type MembraneSequenceProjection = { sequence_id: string; sequence: string; length: number; coordinate_system: string; uniprot_features: MembraneFeature[]; opm: { positions: OpmPosition[]; mapping_statuses: { mapping_status: string; records: number }[]; unmapped_records: { mapping_status: string; pdb_id: string; chain_id: string | null; records: number; first_source_position: number; last_source_position: number; geometry_types: string[] }[]; unmapped_has_more: boolean; source_url: string; scope: string } };
type MembraneSummary = {
  sequence_id: string; length: number; classification?: RecordData | null; labels: RecordData[];
  uniprot: { counts: { transmembrane_features: number; intramembrane_features: number; topological_domains: number }; features: MembraneFeature[]; scope: string };
  deeptmhmm2: { status: string; mapping_status?: string; protein_type?: string; tm_helix_count?: number | null; beta_strand_count?: number | null; membrane_types?: unknown; has_signal_peptide?: boolean | null; segments: Segment[]; segment_counts: Record<string, number> };
  topology_records?: TopologyRecord[]; observations: Observation[]; topology_sources?: TopologySource[]; notes?: string[];
};
type DetailTab = 'overview' | 'sequence' | 'uniprot' | 'prediction' | 'topology' | 'evidence';
const membraneNames: Record<string, string> = { integral_membrane: 'Integral membrane protein', peripheral_membrane: 'Peripheral membrane protein', lipid_anchored: 'Lipid-anchored protein', membrane_related: 'Membrane-related protein', membrane_associated: 'Membrane-associated' };
const membraneName = (item: RecordData) => display(item.label_name ?? membraneNames[String(item.label)] ?? label(item.label));
const primaryMembraneName = (item: RecordData) => {
  if (item.primary_class === 'transmembrane') return item.transmembrane_subclass === 'single_pass' ? 'Single-pass transmembrane protein' : 'Multi-pass transmembrane protein';
  if (item.primary_class === 'lipid_anchored') return 'Lipid-anchored protein · non-TM';
  if (item.primary_class === 'peripheral_membrane') return 'Peripheral membrane protein';
  return 'Membrane-related · mechanism unannotated';
};
const featureColor = (type: string) => type === 'Transmembrane' || type === 'TMhelix' || type === 'TMbeta' ? '#d88708' : type === 'Intramembrane' ? '#a855c7' : '#7891ab';
const featurePosition = (feature: { start: number | null; end: number | null }) => feature.start == null || feature.end == null ? 'Unresolved position' : feature.start === feature.end ? String(feature.start) : `${feature.start}–${feature.end}`;
const exactFeature = (feature: MembraneFeature) => feature.can_locate_exactly === true;

function References({ value }: { value: unknown }) {
  if (!Array.isArray(value) || !value.length) return <span className="mov-no-reference">No reference supplied with this feature.</span>;
  return <div className="mov-references">{value.map((entry, index) => {
    const evidence = entry as RecordData;
    const source = evidence.source ?? evidence.namespace;
    const id = evidence.id ?? evidence.identifier ?? evidence.source_id;
    const url = evidence.url ?? (source === 'PubMed' && id ? `https://pubmed.ncbi.nlm.nih.gov/${id}/` : undefined);
    return <span key={index}><LinkOut href={url}>{source === 'PubMed' ? `PMID:${display(id)}` : [evidence.evidenceCode ?? evidence.evidence_code, source, id].filter(Boolean).map(display).join(' · ') || 'Source evidence'}</LinkOut></span>;
  })}</div>;
}

/** A positional sketch only: it preserves original boundaries and does not infer membrane sides. */
function MembraneSketch({ features, length, onOpen }: { features: MembraneFeature[]; length: number; onOpen?: () => void }) {
  const located = features.filter(feature => exactFeature(feature) && feature.start != null && feature.end != null && feature.start >= 1 && feature.end >= feature.start && feature.end <= length);
  if (!length || !located.length) return null;
  const picture = <><div className="mov-sketch-lanes">{['Membrane', 'Topology'].map((name, lane) => <div className="mov-sketch-row" key={name}><span>{name}</span><div className="mov-sketch-track">{located.filter(feature => lane === 0 ? feature.source_type !== 'Topological domain' : feature.source_type === 'Topological domain').map(feature => <i key={feature.id} style={{ left: `${(feature.start! - 1) / length * 100}%`, width: `${(feature.end! - feature.start! + 1) / length * 100}%`, background: featureColor(feature.source_type) }} title={`${feature.source_type} · ${featurePosition(feature)}${feature.description ? ` · ${feature.description}` : ''}`} />)}</div></div>)}</div><div className="mov-sketch-axis"><span>1</span><span>{length.toLocaleString()} aa</span></div></>;
  return onOpen ? <button type="button" className="mov-sketch mov-sketch-button" onClick={onOpen} aria-label="Open canonical UniProt membrane features">{picture}</button> : <div className="mov-sketch" role="img" aria-label={`Canonical UniProt membrane features, positions 1–${length}. Exact source coordinates only.`}>{picture}</div>;
}

function MembraneSequenceViewer({ accession, summary }: { accession: string; summary: MembraneSummary }) {
  const query = useQuery({ queryKey: ['membrane-sequence-viewer', accession], queryFn: ({ signal }) => api<MembraneSequenceProjection>(`/proteins/${accession}/overview/membrane/sequence`, signal) });
  const [range, setRange] = useState<[number, number]>([1, summary.length]);
  const [selectedPosition, setSelectedPosition] = useState<number | null>(null);
  const projection = query.data;
  const features = (projection?.uniprot_features ?? summary.uniprot.features).filter(feature => exactFeature(feature) && feature.start != null && feature.end != null);
  const opmPositions = projection?.opm.positions ?? [];
  const opmByPosition = new Map(opmPositions.map(item => [item.position, item]));
  const rangeLength = range[1] - range[0] + 1;
  const focus = (start: number, end: number) => setRange([Math.max(1, start - 30), Math.min(summary.length, end + 30)]);
  const selectedOpm = selectedPosition == null ? undefined : opmByPosition.get(selectedPosition);
  const selectedFeatures = selectedPosition == null ? [] : features.filter(feature => feature.start! <= selectedPosition && feature.end! >= selectedPosition);
  return <div className="mov-sequence-viewer"><div className="mov-detail-heading"><Badge tone="amber">Membrane-only sequence view</Badge><span>{summary.sequence_id} · canonical · 1-based inclusive</span></div>
    <p className="mov-context-note">UniProt intervals and OPM structure observations remain separate tracks. OPM points are drawn only after an explicit canonical mapping.</p>
    <div className="mov-sequence-shortcuts"><button onClick={()=>setRange([1,summary.length])}>Full sequence</button>{features.map(feature=><button key={feature.id} onClick={()=>focus(feature.start!,feature.end!)}><i style={{background:featureColor(feature.source_type)}}/>{feature.source_type} {featurePosition(feature)}</button>)}</div>
    <div className="mov-sequence-overview" role="group" aria-label="Membrane annotations across the canonical sequence"><div className="mov-sequence-lane"><span>UniProt</span><div>{features.map(feature=><button key={feature.id} style={{left:`${(feature.start!-1)/summary.length*100}%`,width:`${Math.max(.25,(feature.end!-feature.start!+1)/summary.length*100)}%`,background:featureColor(feature.source_type)}} onClick={()=>focus(feature.start!,feature.end!)} title={`${feature.source_type} · ${featurePosition(feature)} · ${feature.description??feature.label??''}`}/>)}</div></div><div className="mov-sequence-lane mov-opm-lane"><span>OPM</span><div>{opmPositions.map(item=><button key={item.position} style={{left:`${(item.position-1)/summary.length*100}%`}} onClick={()=>{setSelectedPosition(item.position);focus(item.position,item.position);}} title={`OPM · ${item.residue}${item.position} · ${item.structures.length} PDB/chain records`}/>)}</div></div></div>
    <SequenceRangeNavigator length={summary.length} range={range} onRange={setRange}/>
    <Status loading={query.isPending} error={query.error}>{projection&&<>{rangeLength<=240?<div className="mov-residue-grid" aria-label={`Sequence residues ${range[0]} to ${range[1]}`}>{Array.from(projection.sequence.slice(range[0]-1,range[1])).map((residue,index)=>{const position=range[0]+index;const opm=opmByPosition.get(position);const membrane=features.some(feature=>feature.start!<=position&&feature.end!>=position);return <button key={position} className={`${membrane?'is-membrane ':''}${opm?'has-opm ':''}${selectedPosition===position?'selected':''}`} onClick={()=>setSelectedPosition(position)} title={`${residue}${position}${opm?` · ${opm.record_count} OPM observations`:''}`}><small>{position%10===0||position===range[0]?position:''}</small><strong>{residue}</strong>{opm&&<i aria-label="OPM observation"/>}</button>;})}</div>:<p className="mov-sequence-zoom-note">Select a range of 240 residues or fewer to inspect sequence letters. The annotation tracks above always retain the full context.</p>}
      {selectedPosition!=null&&<section className="mov-sequence-selection"><header><strong>{projection.sequence[selectedPosition-1]}{selectedPosition}</strong><span>{selectedFeatures.length} UniProt membrane annotations · {selectedOpm?.record_count??0} OPM observation rows</span></header>{selectedFeatures.length>0&&<div className="mov-selected-features">{selectedFeatures.map(feature=><span key={feature.id}><i style={{background:featureColor(feature.source_type)}}/>{feature.source_type} · {featurePosition(feature)}{feature.description?` · ${feature.description}`:''}</span>)}</div>}{selectedOpm?<div className="mov-opm-structures">{selectedOpm.structures.map((structure,index)=><article key={`${structure.pdb_id}:${structure.chain_id}:${index}`}><div><LinkOut href={`https://www.rcsb.org/structure/${structure.pdb_id}`}>PDB {structure.pdb_id}</LinkOut><Badge tone="teal">Chain {structure.chain_id??'not supplied'}</Badge></div><Fields items={[{label:'Source residue',value:structure.source_positions},{label:'Model',value:structure.models},{label:'OPM geometry',value:structure.geometry_types},{label:'Canonical mapping method',value:structure.mapping_methods.map(value=>label(value))}]}/></article>)}</div>:<p className="mov-context-note">No mapped OPM structure observation is attached to this residue.</p>}</section>}
      <div className="mov-opm-summary"><strong>OPM</strong><span>{number(opmPositions.length,0)} mapped canonical positions</span><span>{number(opmPositions.reduce((total,item)=>total+item.record_count,0),0)} structure/model/chain observation rows</span><LinkOut href={projection.opm.source_url}>OPM source</LinkOut></div>{projection.opm.unmapped_records.length>0&&<Disclosure title={<span>OPM source-coordinate records not drawn · {number(projection.opm.unmapped_records.reduce((total,item)=>total+item.records,0),0)} rows shown</span>}><p className="mov-context-note">These records retain their PDB, chain and original residue range, but have no verified canonical position and therefore stay off the sequence track.</p><div className="mov-opm-unmapped">{projection.opm.unmapped_records.map((item,index)=><article key={`${item.mapping_status}:${item.pdb_id}:${item.chain_id}:${index}`}><div><LinkOut href={`https://www.rcsb.org/structure/${item.pdb_id}`}>PDB {item.pdb_id}</LinkOut><Badge>Chain {item.chain_id??'not supplied'}</Badge></div><Fields items={[{label:'Original residue range',value:`${item.first_source_position}–${item.last_source_position}`},{label:'Source rows',value:item.records},{label:'Mapping status',value:label(item.mapping_status)},{label:'OPM geometry',value:item.geometry_types}]}/></article>)}</div>{projection.opm.unmapped_has_more&&<p className="mov-context-note">Additional source-coordinate groups are retained in the service table.</p>}</Disclosure>}{projection.opm.mapping_statuses.some(item=>item.mapping_status!=='mapped')&&<p className="mov-context-note">Other OPM mapping states: {projection.opm.mapping_statuses.filter(item=>item.mapping_status!=='mapped').map(item=>`${label(item.mapping_status)} (${item.records})`).join(' · ')}.</p>}</>}</Status>
  </div>;
}

function UniProtFeatures({ data, accession }: { data: MembraneSummary; accession: string }) {
  return <><div className="mov-detail-heading"><Badge>UniProt annotations</Badge><span>{data.sequence_id} · canonical · 1-based inclusive</span></div><div className="mov-feature-counts"><span><b>{data.uniprot.counts.transmembrane_features}</b> transmembrane</span><span><b>{data.uniprot.counts.intramembrane_features}</b> intramembrane</span><span><b>{data.uniprot.counts.topological_domains}</b> topological domains</span></div><MembraneSketch features={data.uniprot.features} length={data.length} />
    <p className="mov-context-note">Unresolved coordinates are listed but not drawn.</p>
    {!data.uniprot.features.length ? <p className="ov-no-data">No UniProt membrane feature is available for this canonical sequence.</p> : <div className="mov-feature-list">{data.uniprot.features.map(feature => <Disclosure key={feature.id} title={<span className="mov-feature-title"><i style={{ background: featureColor(feature.source_type) }} /><strong>{feature.source_type}</strong><b>{featurePosition(feature)}</b><span>{feature.description ?? feature.label}</span></span>}>
      <Fields items={[{ label: 'Source type', value: feature.source_type }, { label: 'Description', value: feature.description }, { label: 'Original start', value: feature.start }, { label: 'Original end', value: feature.end }, { label: 'Start qualifier', value: feature.start_modifier }, { label: 'End qualifier', value: feature.end_modifier }, { label: 'Coordinate status', value: label(feature.coordinate_status) }, { label: 'Sequence association', value: label(feature.mapping_status) }]} />
      <References value={feature.evidence} />
    </Disclosure>)}</div>}<div className="mov-source-link"><LinkOut href={`https://www.uniprot.org/uniprotkb/${accession}/entry#subcellular_location`}>Original UniProt entry</LinkOut></div>
  </>;
}

function PredictionPreview({ prediction, loading, error, onOpen }: { prediction?: MembraneSummary['deeptmhmm2']; loading: boolean; error: boolean; onOpen: () => void }) {
  const available = prediction?.status === 'ok' && prediction.mapping_status === 'input_sequence_exact';
  return <section className="mov-prediction-preview" aria-label="DeepTMHMM2 preview">
    <div className="mov-preview-heading"><strong>DeepTMHMM2</strong><Badge tone="purple">Prediction</Badge><button type="button" onClick={onOpen} aria-label="View DeepTMHMM2 prediction details">View details<ArrowUpRight size={14} /></button></div>
    <p>Predicts membrane topology and signal peptides from the protein sequence.</p>
    {available ? <dl className="mov-preview-facts">
      <div><dt>Protein type</dt><dd>{display(prediction.protein_type)}</dd></div>
      <div><dt>TM helices</dt><dd>{prediction.tm_helix_count == null ? 'Not available' : number(prediction.tm_helix_count, 0)}</dd></div>
      <div><dt>Signal peptide</dt><dd>{prediction.has_signal_peptide == null ? 'Not available' : prediction.has_signal_peptide ? 'Predicted' : 'Not predicted'}</dd></div>
      {prediction.beta_strand_count != null && prediction.beta_strand_count > 0 && <div><dt>TM beta strands</dt><dd>{number(prediction.beta_strand_count, 0)}</dd></div>}
    </dl> : <p className="mov-preview-status">{loading ? 'Loading prediction…' : error ? 'Prediction summary unavailable.' : prediction?.status === 'no_local_prediction' ? 'No local prediction available.' : 'No verified prediction for this canonical sequence.'}</p>}
  </section>;
}

function Prediction({ data }: { data: MembraneSummary }) {
  const prediction = data.deeptmhmm2;
  const mapped = prediction.status === 'ok' && prediction.mapping_status === 'input_sequence_exact';
  return <><div className="mov-detail-heading"><Badge tone="purple">DeepTMHMM2</Badge><span>Computational prediction · {data.sequence_id}</span></div>
    <Fields items={[{ label: 'Prediction status', value: label(prediction.status) }, { label: 'Sequence mapping', value: label(prediction.mapping_status) }, { label: 'Original protein type', value: prediction.protein_type }, { label: 'Original membrane types', value: prediction.membrane_types }, { label: 'Signal peptide prediction', value: prediction.has_signal_peptide }]} />
    {mapped ? <><div className="mov-prediction-counts">{Object.entries(prediction.segment_counts ?? {}).map(([name, count]) => <span key={name}><b>{number(count, 0)}</b>{name}</span>)}</div>{prediction.segments.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Source segment type</th><th>Start</th><th>End</th></tr></thead><tbody>{prediction.segments.map(segment => <tr key={segment.segment_order}><td><span className="mov-source-segment"><i style={{ background: featureColor(segment.name) }} />{segment.name}</span></td><td>{segment.start}</td><td>{segment.end}</td></tr>)}</tbody></table></div> : <p className="ov-no-data">No segments were supplied with this prediction.</p>}</> : <p className="ov-no-data">No verified prediction is available for projection onto this canonical sequence.</p>}
    <p className="mov-context-note">Predicted topology · separate from UniProt features</p>
  </>;
}

const observationFields: Record<string, string> = {
  pdb_id: 'PDB', chain_id: 'Chain', source_chain_id: 'Source chain', target_position: 'Canonical position', position: 'Canonical position',
  pdb_resseq: 'Source residue number', residue_number: 'Source residue number', insertion_code: 'Insertion code', source_aa: 'Source residue', target_residue: 'Canonical residue',
  ligand_name: 'Ligand', ligand_id: 'Ligand ID', residue_name: 'Residue name', model_id: 'Model',
  site_coordinate_basis: 'Depth coordinate basis', site_signed_depth_A: 'Signed depth (Å)', distance_to_boundary_A: 'Boundary distance (Å)', heavy_atom_fraction_in_core: 'Heavy atoms in membrane core',
  distance_outside_membrane_A: 'Distance outside membrane', distance_to_midplane_A: 'Distance to membrane midplane', distance_to_observed_surface_A: 'Distance to observed surface', membrane_half_thickness_A: 'Membrane half-thickness',
  pdb_residue: 'Source residue', observed_dum_surface: 'Observed membrane-surface atoms', atoms_cross_boundary: 'Atoms cross membrane boundary',
  min_distance: 'Nearest candidate ligand distance (Å)', is_contact: 'Source contact label', confidence: 'Source confidence', label_source: 'Label source', geometry_type: 'Geometry type',
  mapping_status: 'Sequence mapping', mapping_method: 'Mapping method', is_wildtype_residue: 'Source matches target residue', pharmacological_class: 'Pharmacological class', coordinate_system: 'Source coordinate system',
};
const observationNotes: Record<string, string> = {
  OPM: 'Structure-specific membrane geometry. Depth follows its coordinate basis; the sign does not identify the intracellular or extracellular side.',
  MPLID: 'Original contact labels and candidate-ligand distances. Source confidence categories are retained.',
  BioDolphin: 'Ligand-binding observations retain the ligand and structure context; these are not all lipid contacts.',
};

function SourceEvidence({ data, accession }: { data: MembraneSummary; accession: string }) {
  const [source, setSource] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const query = useQuery({ queryKey: ['membrane-observations', accession, source, offset], enabled: source != null, queryFn: ({ signal }) => api<{ items: RecordData[]; has_more: boolean; total?: number }>(`/proteins/${accession}/overview/membrane/details?${params({ source, limit: 20, offset })}`, signal) });
  return <><h3 className="mov-subheading">Membrane association labels</h3>{data.labels.length ? data.labels.map((item, index) => <article className="mov-classification" key={index}><div><Badge tone="amber">{membraneName(item)}</Badge><span>{display(item.source ?? 'UniProt')} · {display(item.sequence_id ?? data.sequence_id)}</span></div>{Array.isArray(item.supporting_records) && item.supporting_records.length ? item.supporting_records.map((raw, i) => { const record = raw as RecordData; return <Fields key={i} items={[{ label: 'Original evidence', value: record.source_value }, { label: 'Applies to', value: label(record.scope) }]} />; }) : <p className="mov-context-note">{item.label === 'membrane_related' ? 'Fallback association label; no specific integral, peripheral or lipid-anchor assignment. This is not negative membrane evidence.' : 'No specific source classification evidence is attached to this label.'}</p>}</article>) : <p className="ov-no-data">No membrane association labels are available.</p>}
    <h3 className="mov-subheading">Mapped structure observations</h3><div className="mov-observation-sources">{data.observations.map(item => <button type="button" key={item.source} onClick={() => { setSource(item.source); setOffset(0); }} aria-pressed={source === item.source}><Microscope size={17} /><strong>{item.source}</strong><span>{number(item.records, 0)} source records</span><small>{number(item.mapped_positions, 0)} mapped positions · {number(item.pdb_entries, 0)} PDB entries</small><ArrowUpRight size={14} /></button>)}</div>
    <p className="mov-context-note">Records may share residues or structures.</p>
    {source && <section className="mov-observation-detail"><h4>{source} · original observations</h4><p className="mov-context-note">{observationNotes[source]}</p><Status loading={query.isPending} error={query.error} empty={!query.data?.items.length}>{query.data?.items.map((record, index) => <Disclosure key={String(record.id ?? index)} title={<span>{source} · {display(record.pdb_id ?? record.model_id)}{record.chain_id ? ` / ${display(record.chain_id)}` : ''} · {record.residue ? display(record.residue) : 'Position '}{display(record.position ?? record.target_position)}</span>}><Fields items={Array.isArray(record.fields) ? [
      { label: 'PDB', value: record.pdb_id }, { label: 'Chain', value: record.chain_id }, { label: 'Canonical position', value: record.position }, { label: 'Canonical residue', value: record.residue }, { label: 'Source position', value: record.source_position },
      ...record.fields.filter(raw => !['pdb_resseq', 'residue_number'].includes(String((raw as RecordData).label))).map(raw => { const field = raw as RecordData; const name = observationFields[String(field.label)] ?? label(field.label); return { label: `${name}${field.unit && !name.includes(String(field.unit)) ? ` (${display(field.unit)})` : ''}`, value: field.value }; }),
    ] : Object.entries(observationFields).filter(([key]) => record[key] != null).map(([key, name]) => ({ label: name, value: record[key] }))} /></Disclosure>)}</Status><Pager page={offset / 20} count={query.data?.items.length ?? 0} next={query.data?.has_more ? 'next' : null} onPrevious={() => setOffset(Math.max(0, offset - 20))} onNext={() => setOffset(offset + 20)} maxPage={5000} onJump={page=>setOffset(page*20)} totalPages={query.data?.total == null ? undefined : Math.ceil(query.data.total/20)} loading={query.isFetching} /></section>}
  </>;
}

export default function MembraneOverview({ accession, labels }: { accession: string; labels: RecordData[] }) {
  const [tab, setTab] = useState<DetailTab | null>(null);
  const [topologySource,setTopologySource]=useState('HTP');
  const openTopology=(source='HTP')=>{setTopologySource(source);setTab('topology');};
  const query = useQuery({ queryKey: ['membrane-overview', accession], queryFn: ({ signal }) => api<MembraneSummary>(`/proteins/${accession}/overview/membrane/summary`, signal) });
  const data = query.data;
  const classifications = data?.classification ? [{...data.classification,label_name:primaryMembraneName(data.classification)}] : data?.labels ?? labels;
  const metrics = [
    { key: 'transmembrane_features', name: 'Transmembrane', detail: 'source segments' },
    { key: 'intramembrane_features', name: 'Intramembrane', detail: 'source segments' },
    { key: 'topological_domains', name: 'Topology regions', detail: 'source annotations' },
  ] as const;
  const htpCandidates=(data?.topology_records??[]).filter(record=>record.source==='HTP');
  const htp=htpCandidates.find(record=>record.mapped_feature_count>0)??htpCandidates[0];
  const opm=data?.observations.find(item=>item.source==='OPM');
  const expandedOverview=(<div className="ov-section-body"><div className="mov-labels">{classifications.length?classifications.map((item,index)=><button type="button" key={index} onClick={()=>setTab('evidence')}>{membraneName(item)}<ArrowUpRight size={12}/></button>):<p className="ov-no-data">No membrane classification available.</p>}<span className="mtp-reference-sequence">{data?.sequence_id??accession} · {data?.length.toLocaleString()??'—'} aa</span></div>
    <div className="mtp-summary-grid"><section className="mtp-uniprot-preview"><div className="mov-preview-heading"><strong>UniProt</strong><Badge tone="amber">Annotation</Badge><button onClick={()=>setTab('uniprot')}>View features<ArrowUpRight size={14}/></button></div><p>Source membrane features on the canonical sequence.</p><div className="mov-metrics">{metrics.map(metric=><button type="button" key={metric.key} onClick={()=>setTab('uniprot')}><strong>{data?number(data.uniprot.counts[metric.key],0):'—'}</strong><span>{metric.name}</span></button>)}</div>{data&&<MembraneSketch features={data.uniprot.features} length={data.length} onOpen={()=>setTab('uniprot')}/>}</section>
    {query.isPending?<Status loading/>:query.isError?<Status error={query.error}/>:<HtpPreview records={data?.topology_records??[]} onOpen={()=>openTopology()}/>}
    <PredictionPreview prediction={data?.deeptmhmm2} loading={query.isPending} error={query.isError} onOpen={()=>setTab('prediction')}/></div>
    {data&&<TopologyPortrait records={data.topology_records??[]} onOpen={openTopology}/>}
    {data&&<Disclosure title={<span className="mtp-coverage-heading"><Microscope size={16}/> Explore source evidence <small>{new Set((data.topology_records??[]).map(r=>r.source)).size} topology collections · structure & ligand observations</small></span>}><SourceCoverage records={data.topology_records??[]} onOpen={openTopology}/><div className="mtp-structure-overview">{data.observations.map(item=><button key={item.source} onClick={()=>setTab('evidence')}><strong>{item.source}</strong><span>{number(item.pdb_entries,0)} PDB entries</span><small>{number(item.mapped_positions,0)} mapped positions · {number(item.records,0)} observation rows</small><ArrowUpRight size={14}/></button>)}</div><p className="mtp-note">Source entries and observations may overlap. Detailed evidence remains grouped by database and original record.</p></Disclosure>}
    {query.isError&&<button className="text-button" onClick={()=>{void query.refetch();}}>Retry membrane summary</button>}</div>);
  return <section className="ov-section ov-amber mov-panel mov-panel-expanded mov-panel-compact" id="membrane-association"><header><span className="ov-icon"><Layers size={20}/></span><h3>Membrane features <HelpButton title="Membrane evidence"><p>Source annotations, integrated topology and standalone predictions remain separate. HTP reliability is its original topology score, not an experimental validation rate.</p><p>Regions, method outputs and structure observations are different objects. Missing records do not prove biological absence; benchmark sets and shared source constraints are not independent votes.</p></HelpButton></h3><span className="ov-source">Protein context · canonical reference</span></header>
    <div className="ov-section-body"><div className="mov-labels">{classifications.length?classifications.map((item,index)=><button type="button" key={index} onClick={()=>setTab('evidence')}>{membraneName(item)}<ArrowUpRight size={12}/></button>):<span className="ov-no-data">No membrane classification available.</span>}<span className="mtp-reference-sequence">{data?.sequence_id??accession} · {data?.length.toLocaleString()??'—'} aa</span></div>
    <div className="mov-compact-sources">
      <button className="mov-compact-uniprot" onClick={()=>setTab('uniprot')}><span><strong>UniProt</strong><Badge tone="amber">Annotation</Badge><ArrowUpRight size={14}/></span><p>{data?<><b>{number(data.uniprot.counts.transmembrane_features,0)}</b> transmembrane · <b>{number(data.uniprot.counts.topological_domains,0)}</b> topology regions</>:query.isError?'Summary unavailable':'Loading…'}</p></button>
      <button className="mov-compact-htp" onClick={()=>openTopology()}><span><strong>HTP</strong><Badge tone="teal">Integrated topology</Badge><ArrowUpRight size={14}/></span><p>{htp?<><b>{htp.reported_tm_counts.join(' / ')||'Not supplied'}</b> TM segments · reliability <b>{htp.reliability_values.join(' / ')||'Not supplied'}</b></>:query.isPending?'Loading…':query.isError?'Summary unavailable':'No linked HTP record'}</p></button>
      <button className="mov-compact-opm" onClick={()=>setTab('sequence')}><span><strong>OPM</strong><Badge>Structure geometry</Badge><ArrowUpRight size={14}/></span><p>{opm?<><b>{number(opm.mapped_positions,0)}</b> mapped positions · <b>{number(opm.pdb_entries,0)}</b> PDB entries</>:query.isPending?'Loading…':query.isError?'Summary unavailable':'No mapped OPM observation'}</p></button>
      <button className="mov-compact-prediction" onClick={()=>setTab('prediction')}><span><strong>DeepTMHMM2</strong><Badge tone="purple">Prediction</Badge><ArrowUpRight size={14}/></span><p>{data?.deeptmhmm2.status==='ok'&&data.deeptmhmm2.mapping_status==='input_sequence_exact'?<><b>{display(data.deeptmhmm2.protein_type)}</b> · {data.deeptmhmm2.tm_helix_count??'—'} TM helices</>:query.isPending?'Loading…':query.isError?'Summary unavailable':'No verified prediction'}</p></button>
    </div>{query.isError&&<button className="text-button" onClick={()=>{void query.refetch();}}>Retry membrane summary</button>}</div>
    <div className="ov-section-action"><button className="ov-browse" onClick={()=>setTab('overview')}>Explore membrane features & evidence<ArrowRight size={14}/></button><button className="ov-browse" onClick={()=>setTab('sequence')}>Open membrane sequence viewer<ArrowRight size={14}/></button></div>
    {tab&&<Modal title="Membrane architecture & source evidence" onClose={()=>setTab(null)}><div className="mov-detail-tabs" role="group" aria-label="Membrane information view">{([{value:'overview',name:'Overview'},{value:'sequence',name:'Sequence viewer'},{value:'uniprot',name:'UniProt features'},{value:'topology',name:'Topology sources'},{value:'prediction',name:'DeepTMHMM2 prediction'},{value:'evidence',name:'Structure & association evidence'}] as const).map(item=><button key={item.value} type="button" aria-pressed={tab===item.value} onClick={()=>setTab(item.value)}>{item.name}</button>)}</div><Status loading={query.isPending} error={query.error}>{data&&(tab==='overview'?expandedOverview:tab==='sequence'?<MembraneSequenceViewer accession={accession} summary={data}/>:tab==='uniprot'?<UniProtFeatures data={data} accession={accession}/>:tab==='prediction'?<Prediction data={data}/>:tab==='topology'?<TopologySources key={topologySource} records={data.topology_records??[]} accession={accession} initialSource={topologySource}/>:<SourceEvidence data={data} accession={accession}/>)}</Status><div className="mov-detail-footer"><a className="ov-browse" href="#sequence" onClick={()=>setTab(null)}>Open all aligned sequence tracks<ArrowRight size={14}/></a></div></Modal>}
  </section>;
}
