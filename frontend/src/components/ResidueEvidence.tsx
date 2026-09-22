import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Dna, Layers, MapPin } from 'lucide-react';
import { api, display, number, params, type RecordData } from '../api';
import { PageJump, Status } from './ui';
import { InterfaceSiteEvidence } from './InterfaceAnnotations';
import { ClinicalBadge, ConsequencePills, PredictionValue } from './VariantEvidencePanels';
import { type Predictor } from './variant-evidence-model';
import { PREDICTOR_GUIDES } from './predictor-guides';
import { featureStyle, sourceColors, type Feature, type Score, type Track, type VariantSummary } from './sequence-model';
import './residue-evidence.css';

export interface ResidueEvidenceProps {
  accession: string;
  position: number;
  residue: string;
  tracks: Track[];
  scores: Score[];
  summary?: VariantSummary;
  lens?: string;
  predictor?: string;
  initialSource?: string;
  initialPtmType?: string;
  onFeature: (feature: Feature) => void;
  onVariants?: () => void;
  onStructure?: () => void;
}
type Tab = 'variants' | 'ptm' | 'features' | 'jsd' | 'contacts';
type SiteVariant = RecordData & {variant_id:string;annotation_id:string;gene_id?:string;source_names?:string[];canonical_positions?:{position:number;ref_aa?:string;alt_aa?:string}[];predictions?:Predictor[];clinvar?:{classification?:string|null}[]};
type SiteData = {conservation?:RecordData;membrane_contacts?:Record<string,RecordData[]>;membrane_contacts_has_more?:Record<string,boolean>};
const PAGE_SIZE = 8;
const firstTab = (lens:string):Tab => lens==='ptm'?'ptm':lens==='jsd'?'jsd':lens==='interface'?'contacts':['secondary','domains','membrane','function'].includes(lens)?'features':'variants';
const sourceName = (feature:Feature) => feature.source || 'Source unavailable';
const featureName = (feature:Feature) => feature.label || feature.source_type || feature.type || 'Annotation';
function SourceTag({source}:{source:string}) {return <span className="re-source" style={{'--source-color':sourceColors[source]??'#526581'} as CSSProperties}>{source}</span>;}
function LocalPages({page,total,onJump}:{page:number;total:number;onJump:(page:number)=>void}) {return <div className="re-pagination"><span>{total?`${page*PAGE_SIZE+1}–${Math.min(total,(page+1)*PAGE_SIZE)} of ${total}`:'0 records'}</span><button className="button subtle" disabled={!page} onClick={()=>onJump(page-1)}>Previous</button><button className="button subtle" disabled={(page+1)*PAGE_SIZE>=total} onClick={()=>onJump(page+1)}>Next</button><PageJump page={page} onJump={onJump} totalPages={Math.max(1,Math.ceil(total/PAGE_SIZE))} label="Residue annotation page"/></div>;}

function AnnotationTable({features,kind,onFeature,initialSource='all',initialPtmType='all'}:{features:Feature[];kind:'ptm'|'features';onFeature:(feature:Feature)=>void;initialSource?:string;initialPtmType?:string}) {
  const [source,setSource]=useState(initialSource),[page,setPage]=useState(0),[category,setCategory]=useState('all'),[ptmType,setPtmType]=useState(initialPtmType);
  useEffect(()=>{setSource(initialSource);setPtmType(initialPtmType);},[initialSource,initialPtmType]);
  const sources=Array.from(new Set(features.map(sourceName)));
  const groups=Array.from(new Set(features.map(feature=>feature.group??'features')));
  useEffect(()=>{setPage(0);},[source,category,ptmType,features]);
  const filtered=features.filter(feature=>(source==='all'||sourceName(feature)===source)&&(category==='all'||feature.group===category)&&(kind!=='ptm'||ptmType==='all'||featureStyle(feature,'ptm').name===ptmType));
  return <><div className="re-filter-row"><label>Source<select aria-label={`Residue ${kind} source`} value={source} onChange={event=>setSource(event.target.value)}><option value="all">All sources · {features.length}</option>{source!=='all'&&!sources.includes(source)&&<option value={source}>{source} · 0</option>}{sources.map(name=><option key={name} value={name}>{name} · {features.filter(feature=>sourceName(feature)===name).length}</option>)}</select></label>{kind==='ptm'&&<label>Modification<select aria-label="Residue PTM type" value={ptmType} onChange={event=>setPtmType(event.target.value)}><option value="all">All modification types</option>{Array.from(new Set([...(ptmType==='all'?[]:[ptmType]),...features.map(feature=>featureStyle(feature,'ptm').name)])).map(name=><option key={name} value={name}>{name}</option>)}</select></label>}{kind==='features'&&groups.length>1&&<label>Annotation type<select aria-label="Residue feature type" value={category} onChange={event=>setCategory(event.target.value)}><option value="all">All types</option>{groups.map(group=><option key={group} value={group}>{group==='secondary'?'Secondary structure':group==='function'?'Functional sites':group==='domains'?'Domains / regions':group==='membrane'?'Membrane':group}</option>)}</select></label>}<span>{filtered.length} position/type annotations</span></div>
    {filtered.length?<div className="table-wrap"><table className="data-table re-table"><thead><tr><th>{kind==='ptm'?'Modification':'Annotation'}</th><th>Source</th><th>{kind==='ptm'?'Source records':'Span'}</th><th>Evidence</th></tr></thead><tbody>{filtered.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE).map((feature,index)=>{const tone=featureStyle(feature,feature.group??kind);return <tr key={`${feature.id}:${index}`}><td><span className="re-feature-label" style={{'--feature-color':tone.color} as CSSProperties}><i/>{featureName(feature)}</span></td><td><SourceTag source={sourceName(feature)}/></td><td>{kind==='ptm'?feature.record_ids?.length??1:feature.start===feature.end?feature.start:`${feature.start}–${feature.end}`}</td><td><button className="text-button" onClick={()=>onFeature(feature)}>View source <ArrowRight size={13}/></button></td></tr>;})}</tbody></table></div>:<p className="re-empty">No {kind==='ptm'?'PTM':'sequence'} annotation at this residue for this selection.</p>}
    {kind==='ptm'&&filtered.length>0&&<p className="re-caption">Source records are database records, not counts of independent experiments.</p>}
    {filtered.length>PAGE_SIZE&&<LocalPages page={page} total={filtered.length} onJump={setPage}/>}
  </>;
}

function ResidueVariants({accession,position,predictor,onVariants,predictionMode=false}:{accession:string;position:number;predictor:string;onVariants?:()=>void;predictionMode?:boolean}) {
  const [field,setField]=useState(predictor),[page,setPage]=useState(0);
  useEffect(()=>{setField(predictor);setPage(0);},[accession,position,predictor]);
  const query=useQuery({queryKey:['residue-variants',accession,position,field,page],queryFn:({signal})=>api<{items:SiteVariant[];next_cursor:string|null;filters?:{predictors?:Predictor[]}}>(`/proteins/${accession}/variants?${params({canonical_start:position,canonical_end:position,predictors:field,limit:PAGE_SIZE,offset:page*PAGE_SIZE})}`,signal)});
  const guide=PREDICTOR_GUIDES[field];
  const defaults=[{field:'AlphaMissense_score',tool:'AlphaMissense'},{field:'REVEL_score',tool:'REVEL'},{field:'SIFT_score',tool:'SIFT'}];
  const options=query.data?.filters?.predictors??defaults;
  return <><h3 className="re-mode-title">{predictionMode?'Predictor scores by substitution':'Mapped variants and source classifications'}</h3><div className="re-filter-row"><label>Predictor<select aria-label="Residue predictor" value={field} onChange={event=>{setField(event.target.value);setPage(0);}}>{options.map(option=><option key={option.field} value={option.field}>{PREDICTOR_GUIDES[option.field]?.name??option.tool} · {option.field}</option>)}</select></label>{onVariants&&<button className="text-button" onClick={onVariants}>View variants at residue {position} <ArrowRight size={14}/></button>}</div>
    <p className="re-caption">{guide?`${guide.name} · ${guide.scale}. ${guide.direction}`:'Original source scores by substitution.'}</p>
    <Status loading={query.isPending} error={query.error}>{query.data&&<>{query.data.items.length?<div className="table-wrap"><table className="data-table re-table re-variant-table"><thead><tr><th>Mapped substitution</th>{predictionMode&&<th>{guide?.name??field}</th>}<th>Genomic variant · GRCh38</th><th>Consequence</th><th>ClinVar source label<small className="re-column-note">— = not supplied</small></th>{!predictionMode&&<th>{guide?.name??field}</th>}</tr></thead><tbody>{query.data.items.map(row=>{const mapped=row.canonical_positions?.find(item=>item.position===position);const classifications=Array.from(new Set((row.clinvar??[]).map(item=>item.classification).filter(Boolean)));return <tr key={`${row.variant_id}:${row.annotation_id}:${row.gene_id}`}><td><strong className="re-substitution">{mapped?.ref_aa??'—'}{position}<span>→</span>{mapped?.alt_aa??'—'}</strong><div className="re-source-list">{row.source_names?.map(source=><SourceTag key={source} source={source}/>)}</div></td>{predictionMode&&<td><PredictionValue item={row.predictions?.find(item=>item.field===field)}/></td>}<td><span className="mono">{row.variant_id}</span></td><td><ConsequencePills value={row.consequence}/></td><td>{classifications.length?classifications.map(value=><ClinicalBadge key={value} value={value}/>):<span className="muted">—</span>}</td>{!predictionMode&&<td><PredictionValue item={row.predictions?.find(item=>item.field===field)}/></td>}</tr>;})}</tbody></table></div>:<p className="re-empty">{page?'No annotation rows on this page. Choose an earlier page.':'No verified genomic variants map to this residue.'}</p>}</>}</Status>
    <div className="re-pagination"><span>Page {page+1} · transcript annotation rows</span><button className="button subtle" disabled={!page||query.isFetching} onClick={()=>setPage(page-1)}>Previous</button><button className="button subtle" disabled={!query.data?.next_cursor||query.isFetching} onClick={()=>setPage(page+1)}>Next</button><PageJump page={page} onJump={setPage} loading={query.isFetching} label="Residue variant page"/></div>
    <p className="re-caption">Scores belong to each variant annotation. A scored variant is not a clinical classification.</p>
  </>;
}

function ConservationEvidence({accession,position,score}:{accession:string;position:number;score?:Score}) {
  const query=useQuery({queryKey:['residue-evidence',accession,position],queryFn:({signal})=>api<SiteData>(`/proteins/${accession}/sites/${position}?limit=1`,signal)});
  const item=query.data?.conservation;
  const value=item?.value??score?.value;
  const valid=typeof value==='number'&&Number.isFinite(value);
  return <div className="re-conservation"><div className="re-score-heading"><span>JSD conservation</span><strong>{valid?number(value,5):'No score'}</strong></div><div className="re-jsd-bar" aria-label={valid?`JSD conservation ${value} on the 0 to 1 scale`:'No JSD score'}><span>0</span><i>{valid&&<b style={{left:`${Math.min(1,Math.max(0,value))*100}%`}}/>}</i><span>1</span></div><p className="re-caption">Original conservation score · no substituted-residue effect prediction.</p><Status loading={query.isPending} error={query.error}>{item&&<dl className="re-conservation-meta">{[['Occupancy','occupancy'],['Gap frequency','gap_frequency'],['Non-gap sequences','n_nongap'],['Source status','status']].map(([name,key])=><div key={key}><dt>{name}</dt><dd>{display(item[key])}</dd></div>)}</dl>}</Status></div>;
}

function ContactEvidence({accession,position}:{accession:string;position:number}) {
  const [source,setSource]=useState('opm'),[page,setPage]=useState(0);
  const query=useQuery({queryKey:['residue-evidence',accession,position],queryFn:({signal})=>api<SiteData>(`/proteins/${accession}/sites/${position}?limit=1`,signal)});
  useEffect(()=>{setPage(0);},[accession,position,source]);
  const rows=query.data?.membrane_contacts?.[source]??[];
  return <><div className="re-filter-row"><label>Structural source<select aria-label="Residue structural source" value={source} onChange={event=>setSource(event.target.value)}>{[['opm','OPM'],['mplid','MPLID'],['biodolphin','BioDolphin']].map(([value,name])=><option key={value} value={value}>{name}</option>)}</select></label></div><Status loading={query.isPending} error={query.error}>{query.data&&(rows.length?<div className="table-wrap"><table className="data-table re-table"><thead><tr><th>Structure</th><th>Chain</th><th>Source residue</th><th>{source==='opm'?'Depth / boundary (Å)':source==='mplid'?'Source contact':'Lipid'}</th></tr></thead><tbody>{rows.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE).map((row,index)=><tr key={index}><td>{display(row.pdb_id)}</td><td>{display(row.chain_id??row.source_chain_id)}</td><td>{display(row.pdb_residue??row.source_aa??row.residue_name)} {display(row.pdb_resseq??row.residue_number)}{row.insertion_code?String(row.insertion_code):''}</td><td>{source==='opm'?`${number(row.site_signed_depth_A)} / ${number(row.distance_to_boundary_A)}`:source==='mplid'?display(row.is_contact):display(row.ligand_name??row.ligand_id)}</td></tr>)}</tbody></table></div>:<p className="re-empty">No mapped structural observations from this source at this residue.</p>)}</Status>{rows.length>PAGE_SIZE&&<LocalPages page={page} total={rows.length} onJump={setPage}/>}<p className="re-caption">Structure-specific observations retain their source residue numbering.{query.data?.membrane_contacts_has_more?.[source]?' First 50 observations shown; more records remain in the source.':''}</p></>;
}

function OpenInterfaceEvidence({accession,position}:{accession:string;position:number}) {
  const host=useRef<HTMLDivElement>(null);
  useEffect(()=>{const details=host.current?.querySelector('details');if(details)details.open=true;},[accession,position]);
  return <div ref={host}><InterfaceSiteEvidence accession={accession} position={position}/></div>;
}

export function ResidueEvidence({accession,position,residue,tracks,scores,summary,lens='variants',predictor='AlphaMissense_score',initialSource='all',initialPtmType='all',onFeature,onVariants,onStructure}:ResidueEvidenceProps) {
  const [tab,setTab]=useState<Tab>(()=>firstTab(lens)),[extraInterfaceOpen,setExtraInterfaceOpen]=useState(false);
  useEffect(()=>{setTab(firstTab(lens));setExtraInterfaceOpen(false);},[accession,position,lens]);
  const annotations=useMemo(()=>tracks.flatMap(track=>track.features.filter(feature=>feature.start<=position&&feature.end>=position).map(feature=>({...feature,group:track.id}))),[tracks,position]);
  const ptm=useMemo(()=>annotations.filter(feature=>feature.group==='ptm'),[annotations]);
  const features=useMemo(()=>annotations.filter(feature=>feature.group!=='ptm').sort((a,b)=>Number(b.group===lens)-Number(a.group===lens)),[annotations,lens]);
  const site=summary?.canonical_sites.find(item=>item.position===position),score=scores.find(item=>item.position===position);
  const tabs:{id:Tab;name:string;count?:number}[]=[{id:'variants',name:'Variants & scores',count:site?.variant_count},{id:'ptm',name:'PTM',count:ptm.length},{id:'features',name:'Sequence features',count:features.length},{id:'jsd',name:'Conservation'},{id:'contacts',name:lens==='interface'?'Binding interface':'Structural contacts'}];
  const ordered=[...tabs.filter(item=>item.id===firstTab(lens)),...tabs.filter(item=>item.id!==firstTab(lens))];
  return <div className="residue-evidence"><div className="re-overview"><div className="re-residue"><Dna size={20}/><strong>{residue}{position}</strong><span>Canonical residue</span></div><div className="re-overview-stats"><span><b>{site?.variant_count??(summary?0:'—')}</b> mapped variants</span><span><b>{ptm.length}</b> PTM annotations</span><span><b>{features.length}</b> sequence features</span></div>{onStructure&&<button className="text-button" onClick={onStructure}><MapPin size={14}/>View in structure</button>}</div>
    <nav className="re-tabs" aria-label="Residue evidence type">{ordered.map(item=><button key={item.id} aria-pressed={tab===item.id} onClick={()=>setTab(item.id)}>{item.name}{item.count!=null&&<b>{item.count}</b>}</button>)}</nav>
    <section className="re-tab-body" aria-label={tabs.find(item=>item.id===tab)?.name}>
      {tab==='variants'&&<ResidueVariants key={`${accession}:${position}`} accession={accession} position={position} predictor={predictor} predictionMode={lens==='predictions'||lens==='predictor'} onVariants={onVariants}/>}
      {tab==='ptm'&&<AnnotationTable key={`ptm:${accession}:${position}`} features={ptm} kind="ptm" initialSource={initialSource} initialPtmType={initialPtmType} onFeature={onFeature}/>}
      {tab==='features'&&<AnnotationTable key={`features:${accession}:${position}`} features={features} kind="features" onFeature={onFeature}/>}
      {tab==='jsd'&&<ConservationEvidence accession={accession} position={position} score={score}/>}
      {tab==='contacts'&&(lens==='interface'?<OpenInterfaceEvidence accession={accession} position={position}/>:<ContactEvidence accession={accession} position={position}/>)}
    </section>
    {lens!=='interface'&&<div className="re-secondary-evidence"><span><Layers size={14}/>Additional prediction context</span><details className="re-lazy-interface" open={extraInterfaceOpen} onToggle={event=>setExtraInterfaceOpen(event.currentTarget.open)}><summary>Predicted binding interface evidence</summary>{extraInterfaceOpen&&<OpenInterfaceEvidence accession={accession} position={position}/>}</details></div>}
  </div>;
}
