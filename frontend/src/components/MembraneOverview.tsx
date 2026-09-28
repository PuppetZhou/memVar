import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, ArrowUpRight, Layers } from 'lucide-react';
import { api, display, label, number, params, type RecordData } from '../api';
import { Badge, Fields, LinkOut, Modal, Pager, Status } from './ui';
import './membrane-overview.css';
import { HelpButton } from './HelpGuide';
import { TopologySources, type TopologyRecord } from './MembraneTopology';
import MembraneSequenceViewer from './MembraneSequenceViewer';
import MembraneTrack from './MembraneTrack';

type MembraneFeature = {
  id: string; source_type: string; start: number | null; end: number | null;
  description?: string | null; label?: string; evidence?: unknown; mapping_status?: string;
  coordinate_status?: string; can_locate_exactly?: boolean; start_modifier?: string; end_modifier?: string;
};
type Segment = { name: string; start: number; end: number; segment_order: number };
type Observation = { source: string; records: number; mapped_positions: number; pdb_entries: number; unit: string };
type TopologySource = { source: string; method: string | null; role: string; records: number; mapped_features: number; mapped_blocks: number; mapping_statuses: string[] };
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
  if (!Array.isArray(value) || !value.length) return <span className="mov-no-reference">—</span>;
  return <div className="mov-references">{value.map((entry, index) => {
    const evidence = entry as RecordData;
    const source = evidence.source ?? evidence.namespace;
    const id = evidence.id ?? evidence.identifier ?? evidence.source_id;
    const url = evidence.url ?? (source === 'PubMed' && id ? `https://pubmed.ncbi.nlm.nih.gov/${id}/` : undefined);
    return <span key={index}><LinkOut href={url}>{source === 'PubMed' ? `PMID:${display(id)}` : [evidence.evidenceCode ?? evidence.evidence_code, source, id].filter(Boolean).map(display).join(' · ') || 'Source evidence'}</LinkOut></span>;
  })}</div>;
}

function UniProtFeatures({ data, accession }: { data: MembraneSummary; accession: string }) {
  return <section className="membrane-source-section"><div className="membrane-view-heading"><h3>UniProt membrane annotations</h3><LinkOut href={`https://www.uniprot.org/uniprotkb/${accession}/entry#subcellular_location`}>UniProt entry</LinkOut></div>
    <MembraneTrack title={`UniProt · ${data.sequence_id}`} length={data.length} intervals={data.uniprot.features.filter(f => exactFeature(f) && f.start != null && f.end != null).map(f => ({ id: f.id, start: f.start!, end: f.end!, name: f.source_type, description: f.description ?? '', color: featureColor(f.source_type) }))}/>
    {!data.uniprot.features.length ? <p className="ov-no-data">No UniProt membrane annotation available.</p> : <div className="table-wrap membrane-evidence-table"><table className="data-table"><thead><tr><th>Source type</th><th>Interval</th><th>Annotation</th><th>Evidence</th></tr></thead><tbody>{data.uniprot.features.map(feature => <tr key={feature.id}><td><span className="mov-source-segment"><i style={{background:featureColor(feature.source_type)}}/>{feature.source_type}</span></td><td>{featurePosition(feature)}{!exactFeature(feature) && <small className="membrane-cell-note">Uncertain boundary</small>}</td><td>{feature.description || '—'}</td><td><References value={feature.evidence}/></td></tr>)}</tbody></table></div>}
  </section>;
}

function Prediction({ data }: { data: MembraneSummary }) {
  const prediction = data.deeptmhmm2;
  const available = prediction.status === 'ok' && prediction.mapping_status === 'input_sequence_exact';
  return <section className="membrane-source-section"><div className="membrane-view-heading"><h3>DeepTMHMM2</h3><Badge tone="purple">Prediction</Badge></div>
    {available ? <><Fields items={[{ label: 'Membrane type', value: prediction.membrane_types }, { label: 'Signal peptide', value: prediction.has_signal_peptide == null ? 'Not available' : prediction.has_signal_peptide ? 'Predicted' : 'Not predicted' }]} />
    <MembraneTrack title={`Predicted topology · ${data.sequence_id}`} length={data.length} intervals={prediction.segments.map(segment => ({ id: String(segment.segment_order), start: segment.start, end: segment.end, name: segment.name }))}/>
    <div className="table-wrap membrane-evidence-table"><table className="data-table"><thead><tr><th>Predicted region</th><th>Interval</th></tr></thead><tbody>{prediction.segments.map(segment => <tr key={segment.segment_order}><td><span className="mov-source-segment"><i style={{background:featureColor(segment.name)}}/>{segment.name}</span></td><td>{segment.start}–{segment.end}</td></tr>)}</tbody></table></div></> : <p className="ov-no-data">No prediction available for this sequence.</p>}
  </section>;
}

const observationNotes: Record<string, string> = {
  OPM: 'Depth is relative to the membrane boundary: positive inside the core, negative outside. It does not identify intracellular / extracellular orientation.',
  MPLID: 'Contact labels and distances refer to the source candidate ligand set.',
  BioDolphin: 'Ligand observations include lipid-like and other compounds.',
};
function SourceEvidence({ data, accession }: { data: MembraneSummary; accession: string }) {
  const [source, setSource] = useState('OPM');
  const [offset, setOffset] = useState(0);
  const query = useQuery({ queryKey: ['membrane-observations', accession, source, offset], queryFn: ({ signal }) => api<{ items: RecordData[]; has_more: boolean; total?: number }>(`/proteins/${accession}/overview/membrane/details?${params({ source, limit: 20, offset })}`, signal) });
  return <section className="membrane-source-section"><div className="membrane-view-heading"><h3>Structure evidence</h3><span>{data.sequence_id}</span></div>
    <div className="mov-detail-tabs" role="group" aria-label="Structure evidence source">{data.observations.map(item => <button type="button" key={item.source} onClick={() => { setSource(item.source); setOffset(0); }} aria-pressed={source === item.source}>{item.source} · {number(item.pdb_entries, 0)} PDB entries</button>)}</div>
    <p className="mov-context-note">{observationNotes[source]}</p><Status loading={query.isPending} error={query.error} empty={!query.data?.items.length}>
      <div className="table-wrap membrane-evidence-table"><table className="data-table"><thead><tr><th>Residue</th><th>PDB / chain</th><th>PDB residue</th>{source === 'OPM' ? <><th>OPM geometry</th><th>Depth (Å)</th></> : source === 'MPLID' ? <><th>Contact</th><th>Distance (Å)</th></> : <><th>Ligand</th><th>Class</th></>}</tr></thead><tbody>{query.data?.items.map((record, index) => <tr key={String(record.id ?? index)}><td><strong>{display(record.residue)}{display(record.position)}</strong></td><td><LinkOut href={`https://www.rcsb.org/structure/${record.pdb_id}`}>{display(record.pdb_id).toUpperCase()}</LinkOut> · {display(record.chain_id)}</td><td>{display(record.pdb_residue ?? record.source_aa ?? record.residue_name)} {display(record.source_position)}{record.insertion_code ? display(record.insertion_code) : ''}</td>{source === 'OPM' ? <><td>{label(record.geometry_type)}</td><td title={display(record.site_coordinate_basis)}>{record.site_signed_depth_A == null ? 'Not available' : number(Number(record.site_signed_depth_A), 2)}</td></> : source === 'MPLID' ? <><td>{record.is_contact == null ? 'Not supplied' : record.is_contact ? 'Yes' : 'No'}</td><td>{record.min_distance == null ? 'Not available' : number(Number(record.min_distance), 2)}</td></> : <><td>{display(record.ligand_name ?? record.ligand_id)}</td><td>{display(record.pharmacological_class)}</td></>}</tr>)}</tbody></table></div>
    </Status><Pager page={offset / 20} count={query.data?.items.length ?? 0} next={query.data?.has_more ? 'next' : null} onPrevious={() => setOffset(Math.max(0, offset - 20))} onNext={() => setOffset(offset + 20)} maxPage={5000} onJump={page => setOffset(page * 20)} totalPages={query.data?.total == null ? undefined : Math.ceil(query.data.total / 20)} loading={query.isFetching}/>
  </section>;
}

export default function MembraneOverview({ accession, labels }: { accession: string; labels: RecordData[] }) {
  const [tab, setTab] = useState<DetailTab | null>(null);
  const [topologySource,setTopologySource]=useState('HTP');
  const openTopology=(source='HTP')=>{setTopologySource(source);setTab('topology');};
  const query = useQuery({ queryKey: ['membrane-overview', accession], queryFn: ({ signal }) => api<MembraneSummary>(`/proteins/${accession}/overview/membrane/summary`, signal) });
  const data = query.data;
  const classifications = data?.classification ? [{...data.classification,label_name:primaryMembraneName(data.classification)}] : data?.labels ?? labels;
  const htpCandidates=(data?.topology_records??[]).filter(record=>record.source==='HTP');
  const htp=htpCandidates.find(record=>record.mapped_feature_count>0)??htpCandidates[0];
  const opm=data?.observations.find(item=>item.source==='OPM');
  return <section className="ov-section ov-amber mov-panel mov-panel-expanded mov-panel-compact" id="membrane-association"><header><span className="ov-icon"><Layers size={20}/></span><h3>Membrane features <HelpButton title="Membrane evidence"><p>Source annotations, integrated topology and standalone predictions remain separate. HTP reliability is its original topology score, not an experimental validation rate.</p><p>Regions, method outputs and structure observations are different objects. Missing records do not prove biological absence; benchmark sets and shared source constraints are not independent votes.</p></HelpButton></h3><span className="ov-source">Protein context · canonical reference</span></header>
    <div className="ov-section-body"><div className="mov-labels">{classifications.length?classifications.map((item,index)=><button type="button" key={index} onClick={()=>setTab('evidence')}>{membraneName(item)}<ArrowUpRight size={12}/></button>):<span className="ov-no-data">No membrane classification available.</span>}<span className="mtp-reference-sequence">{data?.sequence_id??accession} · {data?.length.toLocaleString()??'—'} aa</span></div>
    <div className="mov-compact-sources">
      <button className="mov-compact-uniprot" onClick={()=>setTab('uniprot')}><span><strong>UniProt</strong><Badge tone="amber">Annotation</Badge><ArrowUpRight size={14}/></span><p>{data?<><b>{number(data.uniprot.counts.transmembrane_features,0)}</b> transmembrane · <b>{number(data.uniprot.counts.topological_domains,0)}</b> topology regions</>:query.isError?'Summary unavailable':'Loading…'}</p></button>
      <button className="mov-compact-htp" onClick={()=>openTopology()}><span><strong>HTP</strong><Badge tone="teal">Integrated topology</Badge><ArrowUpRight size={14}/></span><p>{htp?<><b>{htp.reported_tm_counts.join(' / ')||'Not supplied'}</b> TM segments · reliability <b>{htp.reliability_values.join(' / ')||'Not supplied'}</b></>:query.isPending?'Loading…':query.isError?'Summary unavailable':'No linked HTP record'}</p></button>
      <button className="mov-compact-opm" onClick={()=>setTab('sequence')}><span><strong>OPM</strong><Badge>Structure geometry</Badge><ArrowUpRight size={14}/></span><p>{opm?<><b>{number(opm.mapped_positions,0)}</b> residues · <b>{number(opm.pdb_entries,0)}</b> PDB entries</>:query.isPending?'Loading…':query.isError?'Summary unavailable':'No OPM observation'}</p></button>
      <button className="mov-compact-prediction" onClick={()=>setTab('prediction')}><span><strong>DeepTMHMM2</strong><Badge tone="purple">Prediction</Badge><ArrowUpRight size={14}/></span><p>{data?.deeptmhmm2.status==='ok'&&data.deeptmhmm2.mapping_status==='input_sequence_exact'?<><b>{display(data.deeptmhmm2.protein_type)}</b> · {data.deeptmhmm2.tm_helix_count??'—'} TM helices</>:query.isPending?'Loading…':query.isError?'Summary unavailable':'No verified prediction'}</p></button>
    </div>{query.isError&&<button className="text-button" onClick={()=>{void query.refetch();}}>Retry membrane summary</button>}</div>
    <div className="ov-section-action"><button className="ov-browse membrane-details-button" onClick={()=>setTab('overview')}>View membrane details<ArrowRight size={14}/></button><button className="ov-browse" onClick={()=>setTab('sequence')}>Open membrane sequence viewer<ArrowRight size={14}/></button></div>
    {tab&&<Modal title="Membrane architecture & source evidence" onClose={()=>setTab(null)}><div className="mov-detail-tabs" role="group" aria-label="Membrane information view">{([{value:'sequence',name:'Sequence & OPM'},{value:'uniprot',name:'UniProt features'},{value:'topology',name:'Topology sources'},{value:'prediction',name:'DeepTMHMM2 prediction'},{value:'evidence',name:'Structure evidence'}] as const).map(item=><button key={item.value} type="button" aria-pressed={tab===item.value||(tab==='overview'&&item.value==='sequence')} onClick={()=>setTab(item.value)}>{item.name}</button>)}</div><Status loading={query.isPending} error={query.error}>{data&&(tab==='overview'||tab==='sequence'?<MembraneSequenceViewer accession={accession} summary={data}/>:tab==='uniprot'?<UniProtFeatures data={data} accession={accession}/>:tab==='prediction'?<Prediction data={data}/>:tab==='topology'?<TopologySources key={topologySource} records={data.topology_records??[]} accession={accession} initialSource={topologySource}/>:<SourceEvidence data={data} accession={accession}/>)}</Status><div className="mov-detail-footer"><a className="ov-browse" href="#sequence" onClick={()=>setTab(null)}>Open all aligned sequence tracks<ArrowRight size={14}/></a></div></Modal>}
  </section>;
}
