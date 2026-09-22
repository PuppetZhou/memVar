import { useEffect, useId, useRef, useState, type CSSProperties, type PointerEvent, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { ArrowRight, ChevronDown, CircleDot, CircleHelp, Dna, ExternalLink, Layers, ScanLine, Search, Download, X } from 'lucide-react';
import { Popover } from 'radix-ui';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { CollapseRegion, SelectionFeedback } from '../lib/motion';
import { HelpButton } from './HelpGuide';
import { Disclosure, Modal, PageJump } from './ui';
import { FeatureDetails, FullSequence } from './SequenceAtlas';
import { annotationSourceGuide, type AnnotationSourceOption, type AnnotationSourceOptions, type Feature, type Track, type Score, type VariantSummary } from './sequence-model';
import { RangeControls, ResidueAxis, PtmExplorer } from './SequenceAnnotations';
import { InterfaceTrack } from './InterfaceAnnotations';
import { ResidueEvidence } from './ResidueEvidence';
import SequenceRangeNavigator from './SequenceRangeNavigator';
import ConservationPlot from './ConservationPlot';
import { CompactAnnotationTrack } from './CompactAnnotationTracks';
import { CompactVariantTrack } from './CompactVariantTrack';
import './sequence-composite.css';
import './viewers.css';

type SequenceData = { sequence_id: string; sequence: string; length: number; tracks: Track[]; conservation: Score[]; topology_options: AnnotationSourceOption[]; annotation_source_options:AnnotationSourceOptions; selected_topology:string[]; [key: string]: unknown };
const compactTracks=[{id:'variants',label:'Variant density',color:'#e8910c'},{id:'domains',label:'Domains / regions',color:'#f97316'},{id:'membrane',label:'Membrane',color:'#8b5cf6'},{id:'function',label:'Functional sites',color:'#e52b83'},{id:'ptm',label:'PTM',color:'#0891b2'},{id:'secondary',label:'Secondary structure',color:'#16a37b'},{id:'jsd',label:'JSD',color:'#7c3aed'},{id:'interface',label:'Binding interface',color:'#2563eb'}];
async function getData<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal }); if (!response.ok) throw new Error('Sequence data could not be loaded'); return response.json();
}
function sequenceUrl(accession:string,topologies:string[]){const query=new URLSearchParams();(topologies.length?topologies:['none']).forEach(value=>query.append('topology',value));return `/api/proteins/${accession}/sequence?${query}`;}
function SourceCheckboxGroup({label,options,selected,onToggle}:{label:string;options:AnnotationSourceOption[];selected:string[];onToggle:(id:string)=>void}){
  const groupId=useId();
  const [activeSource,setActiveSource]=useState<string|null>(null);
  const hierarchical=label==='Topology';
  const family=(option:AnnotationSourceOption)=>option.source.split('/')[0];
  const families=Array.from(new Set(options.map(family)));
  const currentSource=activeSource&&families.includes(activeSource)?activeSource:null;
  const visibleOptions=hierarchical?options.filter(option=>family(option)===currentSource):options;
  const SourceIcon=label==='Domains'?Layers:label==='PTM'?CircleDot:ScanLine;
  const [explained,setExplained]=useState<string|null>(null);
  const checked=options.filter(option=>selected.includes(option.id));
  const sourceNames=Array.from(new Set(checked.map(option=>option.source)));
  const summary=checked.length===0?'Off':checked.length===1?(checked[0].method?`${checked[0].source} · ${checked[0].method}`:checked[0].source):checked.length===2&&checked[0].source!==checked[1].source?checked.map(option=>option.source).join(' + '):sourceNames.length===1?`${sourceNames[0]} · ${checked.length} layers`:`${sourceNames[0]} + ${sourceNames.length-1} sources`;
  return <Popover.Root onOpenChange={open=>{if(open){setActiveSource(null);setExplained(null);}}}><Popover.Trigger asChild><Button variant="outline" size="sm" className="annotation-source-trigger" aria-label={`${label} sources: ${summary}`}><SourceIcon size={14} aria-hidden="true"/><strong>{label}</strong><span title={checked.map(option=>option.label).join('; ')||'No source selected'}>{summary}</span><ChevronDown className="annotation-source-chevron" size={14}/></Button></Popover.Trigger><Popover.Portal><Popover.Content className="annotation-source-popover" sideOffset={6} align="start" collisionPadding={16} aria-label={`${label} sources`}>
    <div className="annotation-source-heading"><strong>{label} sources</strong><span>{checked.length} of {options.length} selected</span></div>
    <p className="annotation-source-hint">{hierarchical?'1. Choose a source · 2. Select its types or methods. Selections across sources are kept.':'Choose source layers · Details shows descriptions and provenance.'}</p>
    {hierarchical&&!currentSource&&<div className="topology-source-grid" aria-label="Topology data sources">{families.map(source=><button key={source} type="button" aria-pressed={currentSource===source} onClick={()=>{setActiveSource(source);setExplained(null);}}><strong>{source}</strong><small>{options.filter(option=>family(option)===source&&selected.includes(option.id)).length} selected <ChevronDown size={13}/></small></button>)}</div>}
    {hierarchical&&currentSource&&<Button variant="ghost" size="sm" onClick={()=>setActiveSource(null)}>← All topology sources</Button>}
    {hierarchical&&<strong className="topology-layer-heading">{currentSource?`${currentSource} · types & methods`:'Choose a source above to see available types'}</strong>}
    <div className="annotation-source-options-list">{visibleOptions.length?visibleOptions.map((option,index)=>{
      const guide=annotationSourceGuide(option.source,option.kind);
      const description=option.kind==='method_prediction'||option.kind==='prediction'?`Computational prediction from ${option.source}${option.method?` using ${option.method}`:''}.`:guide.description;
      const provenance=option as AnnotationSourceOption&{source_record_id?:string;source_sequence_id?:string;model_id?:string|null};
      const detailId=`${groupId}-details-${index}`;
      const checkboxId=`${groupId}-source-${index}`;
      const isExplained=explained===option.id;
      return <div className="annotation-source-option" key={option.id}>
        <label className="annotation-source-choice" htmlFor={checkboxId}><Checkbox id={checkboxId} checked={selected.includes(option.id)} disabled={option.available===false} onCheckedChange={()=>onToggle(option.id)} aria-label={`${label}: ${option.label}`}/><span>{option.label}</span>{typeof option.count==='number'&&<small>{option.count.toLocaleString()}</small>}</label>
        <Button variant="ghost" size="sm" className="annotation-source-info-trigger" aria-label={`Details for ${label}: ${option.label}`} aria-expanded={isExplained} aria-controls={detailId} onClick={()=>setExplained(isExplained?null:option.id)}><CircleHelp size={14}/><span>Details</span></Button>
        <CollapseRegion open={isExplained} className="annotation-source-detail-region" id={detailId}><div className="annotation-source-detail"><p>{description}</p><dl><div><dt>Source</dt><dd>{option.source}</dd></div>{option.method&&<div><dt>Method</dt><dd>{option.method}</dd></div>}{option.kind&&<div><dt>Evidence kind</dt><dd>{option.kind.replaceAll('_',' ')}</dd></div>}{provenance.source_record_id&&<div><dt>Source record</dt><dd>{provenance.source_record_id}</dd></div>}{provenance.source_sequence_id&&<div><dt>Source sequence</dt><dd>{provenance.source_sequence_id}</dd></div>}{provenance.model_id&&<div><dt>Model</dt><dd>{provenance.model_id}</dd></div>}{typeof option.count==='number'&&<div><dt title="Count reported for this source layer">Source count</dt><dd>{option.count.toLocaleString()}</dd></div>}</dl>{option.available===false&&<p className="muted">This source layer is unavailable for the current protein.</p>}{guide.url&&<a href={guide.url} target="_blank" rel="noreferrer">Source documentation <ExternalLink size={12}/></a>}</div></CollapseRegion>
      </div>;
    }):(!hierarchical||currentSource)&&<p className="annotation-source-empty">No source layers are available for this protein.</p>}</div>
  </Popover.Content></Popover.Portal></Popover.Root>;
}

function DetailValues({ value }: { value: unknown }) {
  if (value == null) return null;
  if (typeof value !== 'object') return <span>{String(value)}</span>;
  if (Array.isArray(value)) return <>{value.slice(0, 12).map((v, i) => <div className="site-record" key={i}><DetailValues value={v} /></div>)}{value.length > 12 && <p className="muted">Showing the first 12 records in this group.</p>}</>;
  const object = value as Record<string, unknown>;
  const visible = ['source', 'label', 'type', 'source_type', 'feature_type', 'description', 'modification', 'modification_type', 'position', 'start', 'end', 'residue', 'jsd', 'value', 'mapping_status', 'status', 'text', 'pmid', 'reference', 'ligand', 'score', 'evalue', 'homology_status', 'occupancy', 'gap_frequency', 'pfam_accession', 'pfam_id', 'ali_start', 'ali_end', 'env_start', 'env_end', 'hmm_start', 'hmm_end', 'domain_i_evalue', 'domain_score', 'displayed_boundary', 'source_start', 'source_end', 'association_status', 'pdb_id', 'model_id', 'chain_id', 'source_chain_id', 'pdb_resseq', 'residue_number', 'insertion_code', 'pdb_residue', 'source_aa', 'residue_name', 'target_residue', 'is_wildtype_residue', 'geometry_type', 'site_coordinate_basis', 'site_signed_depth_A', 'distance_to_boundary_A', 'heavy_atom_fraction_in_core', 'is_contact', 'label_source', 'confidence', 'min_distance', 'coordinate_system', 'ligand_name', 'ligand_id', 'pharmacological_class'];
  const fieldLabels: Record<string,string> = {site_signed_depth_A:'Signed depth (Å)',distance_to_boundary_A:'Boundary distance (Å)',min_distance:'Nearest candidate ligand distance (Å)',heavy_atom_fraction_in_core:'Heavy atoms in membrane core (fraction)',is_wildtype_residue:'Source matches target residue',is_contact:'Source contact label',confidence:'Source confidence category',site_coordinate_basis:'Depth coordinate basis'};
  const refs = (object.evidence ?? object.evidences) as Record<string, unknown>[] | undefined;
  return <><dl className="site-fields">{visible.filter(key => object[key] != null && object[key] !== '' && typeof object[key] !== 'object').map(key => <div key={key}><dt>{fieldLabels[key]??key.replaceAll('_', ' ')}</dt><dd>{typeof object[key]==='boolean'?(object[key]?'Yes':'No'):String(object[key])}</dd></div>)}</dl>
    {Array.isArray(refs) && refs.length > 0 && <div className="evidence-links">{refs.slice(0,10).map((r,i)=>{const kind=r.namespace??r.source;const id=r.identifier??r.source_id;const url=typeof r.url==='string'?r.url:kind==='PubMed'&&id?`https://pubmed.ncbi.nlm.nih.gov/${id}/`:kind==='PDB'&&id?`https://www.rcsb.org/structure/${id}`:null;return url&&/^https?:\/\//.test(url)?<a key={i} href={url} target="_blank" rel="noreferrer">{String(kind)} {String(id??'source')}</a>:<span key={i}>{String(r.evidence_code??kind??'Evidence')}</span>;})}{refs.length>10&&<span className="muted">+ {refs.length-10} source references</span>}</div>}
  </>;
}

function UnmappedAnnotations({accession}:{accession:string}) {
  const [open,setOpen]=useState(false);const [source,setSource]=useState('dbPTM');const [offset,setOffset]=useState(0);
  const query=useQuery<{items:Record<string,unknown>[];has_more:boolean;source_options:string[]}>({queryKey:['unmapped',accession,source,offset],enabled:open,queryFn:({signal})=>getData(`/api/proteins/${accession}/sequence/unmapped?source=${source}&limit=10&offset=${offset}`,signal)});
  useEffect(()=>{setOffset(0);},[accession,source]);
  return <Disclosure className="unmapped-details" onOpenChange={setOpen} title="Additional PTM records without verified sequence positions">
    <p className="muted small">Protein-associated records · no canonical mapping.</p>
    <div className="toolbar"><label>Source <select aria-label="Unmapped annotation source" value={source} onChange={e=>setSource(e.target.value)}>{(query.data?.source_options??['dbPTM','GlyGen','ProteomeScout','UniProt']).filter(s=>s!=='PTMD2').map(s=><option key={s}>{s}</option>)}</select></label></div>
    {query.isPending?<p className="muted">Loading source records…</p>:query.isError?<p role="alert">These source records could not be loaded.</p>:!query.data?.items.length?<p className="muted">No records in this category.</p>:query.data.items.map((record,i)=>{const details=(record.details??{}) as Record<string,unknown>;return <div className="site-record" key={i}><strong>{String(record.source_type??'Source annotation')}</strong><span className="badge">{String(record.source)}</span><p>{String(record.description??'')}</p><dl className="site-fields">{['Disease','State','MutationSite','CellType','Enzyme'].filter(k=>details[k]!=null&&details[k]!=='').map(k=><div key={k}><dt>{k}</dt><dd>{String(details[k])}</dd></div>)}</dl><details><summary>Association status and source evidence</summary><DetailValues value={record}/></details></div>;})}
    <div className="toolbar"><button className="button" disabled={!offset||query.isFetching} onClick={()=>setOffset(Math.max(0,offset-10))}>Previous records</button><PageJump page={offset/10} onJump={page=>setOffset(page*10)} maxPage={10000} loading={query.isFetching} label="Unmapped annotation page"/><button className="button" disabled={!query.data?.has_more||query.isFetching||offset>=100000} onClick={()=>setOffset(offset+10)}>Next records</button></div>
  </Disclosure>;
}

export default function SequenceViewer({ accession, selectedPosition, onSelectPosition }: { accession: string; selectedPosition?: number | null; onSelectPosition: (position: number|null) => void }) {
  const [,setSearchParams]=useSearchParams();
  const [topologySources, setTopologySources] = useState<string[]>(['uniprot']);
  const query = useQuery<SequenceData>({ queryKey: ['sequence', accession, topologySources], placeholderData: (previous, previousQuery) => previousQuery?.queryKey[1] === accession ? previous : undefined, queryFn: ({ signal }) => getData(sequenceUrl(accession,topologySources), signal) });
  const data = query.data;
  const [viewRange, setRange] = useState<[number, number]|null>(null);
  const range:[number,number]=viewRange??[1,data?.length??100];
  const [searchMatches,setSearchMatches]=useState<number[]>([]);
  const [search, setSearch] = useState(''); const [searchError, setSearchError] = useState('');
  const [colourBy,setColourBy]=useState<'type'|'source'>('type');
  const [showRegions,setShowRegions]=useState(true);const [showProcessing,setShowProcessing]=useState(false);
  const [hoverPosition,setHoverPosition]=useState<number|null>(null);const [hoverTrackY,setHoverTrackY]=useState(0);const [ptmTableOpen,setPtmTableOpen]=useState(false);
  const [ptmTableCloseRequested,setPtmTableCloseRequested]=useState(false);
  const pendingPtmAction=useRef<(()=>void)|null>(null);
  const requestPtmClose=(action:()=>void)=>{pendingPtmAction.current=action;setPtmTableCloseRequested(true);};
  const finishPtmClose=()=>{setPtmTableOpen(false);setPtmTableCloseRequested(false);const action=pendingPtmAction.current;pendingPtmAction.current=null;action?.();};
  const [activeFeature,setActiveFeature]=useState<Feature|null>(null);
  const [siteOpen,setSiteOpen]=useState(false);
  const [siteCloseRequested,setSiteCloseRequested]=useState(false);
  const pendingSiteAction=useRef<(()=>void)|null>(null);
  const requestSiteClose=(action:()=>void)=>{pendingSiteAction.current=action;setSiteCloseRequested(true);};
  const finishSiteClose=()=>{setSiteOpen(false);setSiteCloseRequested(false);const action=pendingSiteAction.current;pendingSiteAction.current=null;action?.();};
  const [atlasSource,setAtlasSource]=useState('all');const [atlasPtmType,setAtlasPtmType]=useState('all');const [atlasLens,setAtlasLens]=useState('variants');const [atlasPredictor,setAtlasPredictor]=useState('AlphaMissense_score');
  const variantSummary=useQuery<VariantSummary>({queryKey:['sequence-variant-summary',accession],queryFn:({signal})=>getData(`/api/proteins/${accession}/variants/summary`,signal)});
  const [hidden, setHidden] = useState<string[]>([]);
  const [domainSources, setDomainSources] = useState<string[]>(['UniProt','Pfam']);
  const [ptmSources,setPtmSources]=useState<string[]>(['dbPTM']);
  const initializedSequence = useRef('');
  useEffect(()=>{setTopologySources(['uniprot']);},[accession]);
  useEffect(() => {
    if (!data) return;
    const identity = `${accession}:${data.sequence_id}`;
    if(initializedSequence.current===identity) return;
    initializedSequence.current=identity;
    const domainOptions=data.annotation_source_options?.domains??[];const ptmOptions=data.annotation_source_options?.ptm??[];
    const availableDomains=domainOptions.filter(option=>option.available!==false).map(option=>option.id);
    const availablePtm=ptmOptions.filter(option=>option.available!==false).map(option=>option.id);
    setRange([1,data.length]); setSearchMatches([]); setHidden([]); setSearch(''); setSearchError('');setDomainSources(availableDomains);
    setPtmSources(availablePtm.includes('dbPTM')?['dbPTM']:availablePtm.slice(0,1));
  }, [accession, data]);
  const tracks = (data?.tracks ?? []).map(track=>query.isPlaceholderData&&track.id==='membrane'?{...track,features:[]}:track);
  const sourceOptions=data?.annotation_source_options;
  useEffect(()=>setHoverPosition(null),[range[0],range[1],accession]);
  const select = (position: number) => { onSelectPosition(position); };
  const openSiteVariants=()=>{if(!selectedPosition)return;const position=selectedPosition;requestSiteClose(()=>{setSearchParams(previous=>{const p=new URLSearchParams(previous);for(const key of ['variants_search','variants_cursor','variants_page'])p.delete(key);p.set('variants_canonical_start',String(position));p.set('variants_canonical_end',String(position));p.set('variants_range_origin','sequence');return p;});requestAnimationFrame(()=>document.getElementById('variants')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));});};
  const jump = () => {
    if (!data) return;
    const text = search.trim().toUpperCase(); const interval = text.match(/^(\d+)(?:\s*[-:]\s*(\d+))?$/);
    let matches:number[]=[];
    if(interval){const start=Number(interval[1]),end=interval[2]?Number(interval[2]):start;if(start>=1&&end>=start&&end<=data.length)matches=Array.from({length:end-start+1},(_,i)=>start+i);}
    else if(text){let from=0;const found=new Set<number>();while(from<data.length){const at=data.sequence.indexOf(text,from);if(at<0)break;for(let i=0;i<text.length;i++)found.add(at+i+1);from=at+1;}matches=[...found].sort((a,b)=>a-b);}
    if(!matches.length){setSearchMatches([]);setSearchError('No match. Enter a valid residue, range, or sequence fragment.');return;}
    setSearchError('');setSearchMatches(matches);
    setRange([Math.max(1,matches[0]-15),Math.min(data.length,Math.max(matches[matches.length-1]+15,matches[0]+50))]);
  };
  const coordinatePosition=hoverPosition??selectedPosition;
  const hoverTracks=(event:PointerEvent<HTMLDivElement>)=>{const plot=(event.target as Element).closest<HTMLElement>('[data-composite-plot]');if(!plot||!data||!(event.target as Element).closest('svg'))return;const box=plot.getBoundingClientRect();setHoverTrackY(event.clientY-event.currentTarget.getBoundingClientRect().top);const width=box.width-24;if(width<=0)return;const ratio=Math.max(0,Math.min(1,(event.clientX-box.left-12)/width));setHoverPosition(Math.min(range[1],range[0]+Math.floor(ratio*(range[1]-range[0]+1))));};
  const alignedRow=(id:string,children:ReactNode,detail?:string)=>{const item=compactTracks.find(t=>t.id===id)!;return <div className="composite-track-row" key={id} data-track={id}><div className="composite-track-label"><i style={{background:item.color}}/><div><strong>{item.label}</strong>{detail&&<small>{detail}</small>}{id==='ptm'&&<button className="text-button" onClick={()=>setPtmTableOpen(true)}>View table</button>}</div></div><div className="composite-track-body" data-composite-plot>{children}</div></div>;};
  const featureRow=(id:string)=>{const track=tracks.find(t=>t.id===id);if(!track||hidden.includes(id))return null;if(id==='membrane'&&query.isPlaceholderData)return alignedRow(id,<p className="small muted" role="status">Loading selected topology layers…</p>);const selectedSources=id==='domains'?domainSources:id==='ptm'?ptmSources:'all';return alignedRow(id,<CompactAnnotationTrack track={track} range={range} source={selectedSources} colourBy={colourBy} showRegions={showRegions} showProcessing={showProcessing} selectedPosition={selectedPosition} onFeature={f=>{select(f.start);setActiveFeature({...f,group:id});}}/>,id==='ptm'?(ptmSources.length?ptmSources.join(' + '):'Off'):id==='domains'?(domainSources.length?domainSources.join(' + '):'Off'):id==='membrane'?(topologySources.length?`${topologySources.length} source layer${topologySources.length===1?'':'s'}`:'Off'):id==='secondary'||id==='function'?'UniProt':undefined);};
  const toggle=(setter:typeof setDomainSources,id:string)=>setter(current=>current.includes(id)?current.filter(value=>value!==id):[...current,id]);
  const ptmSourceForDetail=ptmSources.length===1?ptmSources[0]:'all';
  return <section className="panel sequence-section" id="sequence">
    <div className="section-heading"><span className="viewer-icon sequence-icon"><Dna size={24}/></span><div><h2>Protein sequence browser <HelpButton topic="sequence"/></h2><p>Canonical sequence & mapped annotations</p></div></div>
    {query.isPending ? <p className="empty-state">Loading sequence and annotation tracks…</p> : query.isError ? <div className="empty-state"><p>{query.error.message}</p><button className="button" onClick={() => query.refetch()}>Retry</button></div> : data && <>
      <div className="toolbar sequence-toolbar"><form onSubmit={e => { e.preventDefault(); jump(); }}><Search size={17}/><input aria-label="Find residue or sequence" placeholder="Residue, range or sequence fragment · e.g. 858 or 700–900" value={search} onChange={e => setSearch(e.target.value.replace('–','-'))}/><Button variant="outline" size="sm" type="submit">Find</Button></form>
        <Button variant="outline" size="sm" onClick={() => { const blob = new Blob([`>${accession}|${data.sequence_id}\n${data.sequence.match(/.{1,60}/g)?.join('\n')}\n`], {type:'text/plain'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=`${data.sequence_id}.fasta`; a.click(); URL.revokeObjectURL(url); }}><Download size={15}/> FASTA</Button>
      </div>
      {searchMatches.length>0&&<div className="sequence-search-state" role="status"><Search size={16}/><strong>Search · {searchMatches.length.toLocaleString()} matched residue{searchMatches.length===1?'':'s'}</strong><span>{searchMatches[0]}{searchMatches.length>1?`–${searchMatches[searchMatches.length-1]}`:''} · outline marks matches; tile colours retain their meaning</span><Button variant="outline" size="sm" onClick={()=>{const target=document.querySelector<HTMLElement>(`#sequence [data-residue="${searchMatches[0]}"]`);target?.scrollIntoView({block:'center',behavior:'instant'});target?.focus({preventScroll:true});}}>View matches in atlas</Button><Button variant="ghost" size="sm" onClick={()=>{setSearchMatches([]);setSearch('');setSearchError('');}}><X size={14}/>Clear search</Button></div>}
      {searchError && <p role="alert" className="viewer-warning">{searchError}</p>}
      <div className="composite-source-controls"><span className="badge">{data.sequence_id} · canonical · {data.length.toLocaleString()} aa</span>
       <SourceCheckboxGroup label="Domains" options={sourceOptions?.domains??[]} selected={domainSources} onToggle={id=>toggle(setDomainSources,id)}/>
       <SourceCheckboxGroup label="PTM" options={sourceOptions?.ptm??[]} selected={ptmSources} onToggle={id=>toggle(setPtmSources,id)}/>
       <SourceCheckboxGroup label="Topology" options={sourceOptions?.topology??data.topology_options??[]} selected={topologySources} onToggle={id=>toggle(setTopologySources,id)}/>
       <Popover.Root><Popover.Trigger asChild><Button variant="ghost" size="sm" className="composite-display-trigger">Display options</Button></Popover.Trigger><Popover.Portal><Popover.Content className="composite-display-popover" sideOffset={5} align="end" aria-label="Sequence display options"><label><Checkbox checked={showRegions} onCheckedChange={checked=>setShowRegions(checked===true)}/>Regions, repeats & motifs</label><label><Checkbox checked={showProcessing} onCheckedChange={checked=>setShowProcessing(checked===true)}/>Processing / composition</label><label>Colour by <select aria-label="Track colours" value={colourBy} onChange={e=>setColourBy(e.target.value as 'type'|'source')}><option value="type">Annotation type</option><option value="source">Data source</option></select></label></Popover.Content></Popover.Portal></Popover.Root>
      </div>
      <RangeControls range={range} length={data.length} onRange={setRange}/>
      <div className="composite-heading"><strong>Aligned sequence annotations</strong><span>Visible window {range[0]}–{range[1]}</span>{coordinatePosition!=null&&coordinatePosition>=range[0]&&coordinatePosition<=range[1]&&<code>{data.sequence[coordinatePosition-1]}{coordinatePosition}</code>}<button className="text-button" onClick={()=>document.getElementById('variants')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})}>Go to variant catalog <ArrowRight size={14}/></button></div>
      <div className="composite-track-switches" aria-label="Visible sequence tracks">{compactTracks.map(t=><label key={t.id}><Checkbox checked={!hidden.includes(t.id)} onCheckedChange={()=>setHidden(h=>h.includes(t.id)?h.filter(id=>id!==t.id):[...h,t.id])}/><i style={{background:t.color}}/>{t.label}</label>)}</div>
      <div className="composite-overview"><span>View window</span><div><SequenceRangeNavigator length={data.length} range={range} onRange={setRange}/></div></div>
      <div className="sequence-composite" onPointerMove={hoverTracks} onPointerLeave={()=>setHoverPosition(null)}>
       <div className="composite-track-row composite-ruler-row"><div className="composite-track-label"><strong>Residues</strong></div><div className="composite-track-body"><ResidueAxis sequence={data.sequence} range={range} onRange={setRange}/></div></div>
       {!hidden.includes('variants')&&alignedRow('variants',<CompactVariantTrack sites={variantSummary.data?.canonical_sites??[]} range={range} onSelectRange={setRange} inset={0} loading={variantSummary.isPending} error={variantSummary.isError?'Variant density unavailable':undefined}/>,variantSummary.data?`${variantSummary.data.totals.canonical_mapped_variants.toLocaleString()} mapped variants`:'Verified positions')}
       {featureRow('domains')}{featureRow('membrane')}{featureRow('function')}{featureRow('ptm')}{featureRow('secondary')}
       {!hidden.includes('jsd')&&alignedRow('jsd',<ConservationPlot compact scores={data.conservation??[]} sequence={data.sequence} range={range} onSelect={select}/>,'Conservation · 0–1')}
       {!hidden.includes('interface')&&alignedRow('interface',<InterfaceTrack compact accession={accession} sequence={data.sequence} range={range} onRange={setRange} selectedPosition={selectedPosition} onSelect={p=>{select(p);setAtlasLens('interface');setSiteOpen(true);}}/>,'Original score · 0–1')}
       <div className="composite-track-row composite-ruler-row bottom"><div className="composite-track-label"><strong>Residues</strong></div><div className="composite-track-body"><ResidueAxis sequence={data.sequence} range={range} onRange={setRange}/></div></div>
       {coordinatePosition!=null&&coordinatePosition>=range[0]&&coordinatePosition<=range[1]&&<div className="composite-guide-area" aria-hidden="true"><i style={{left:`${(coordinatePosition-range[0]+.5)/(range[1]-range[0]+1)*100}%`} as CSSProperties}/>{hoverPosition!=null&&<span className="composite-residue-readout" style={{left:`clamp(60px, ${(coordinatePosition-range[0]+.5)/(range[1]-range[0]+1)*100}%, calc(100% - 60px))`,top:Math.max(4,hoverTrackY-32)} as CSSProperties}>Residue {data.sequence[coordinatePosition-1]}{coordinatePosition.toLocaleString()}</span>}</div>}
      </div>
      
      {ptmTableOpen&&tracks.find(t=>t.id==='ptm')&&<Modal title={`PTM annotations · ${range[0]}–${range[1]}`} closeRequested={ptmTableCloseRequested} onClose={finishPtmClose}><div className="composite-ptm-table"><PtmExplorer track={tracks.find(t=>t.id==='ptm')!} sequence={data.sequence} range={range} onRange={setRange} onFeature={f=>requestPtmClose(()=>setActiveFeature(f))} onSelect={p=>requestPtmClose(()=>{select(p);setAtlasLens('ptm');setAtlasSource(ptmSourceForDetail);setAtlasPtmType('all');setSiteOpen(true);})} source={ptmSourceForDetail} onSource={value=>setPtmSources(value==='all'?(sourceOptions?.ptm??[]).filter(option=>option.available!==false).map(option=>option.id):[value])}/></div></Modal>}
      <FullSequence searchMatches={searchMatches} accession={accession} sequence={data.sequence} tracks={tracks} scores={data.conservation??[]} summary={variantSummary.data} sourceOptions={sourceOptions} selected={selectedPosition} onSelect={(p,lens,predictor,ptmSource,ptmType)=>{select(p);setAtlasLens(lens);setAtlasPredictor(predictor);setAtlasSource(ptmSource);setAtlasPtmType(ptmType);setSiteOpen(true);}}/>
      <SelectionFeedback visible={!!selectedPosition} className="sequence-selection-feedback"><div className="sequence-selected"><strong>{selectedPosition?`${data.sequence[selectedPosition-1]}${selectedPosition}`:''}</strong><span className="muted small">Selected residue · linked to the structure below</span><Button variant="outline" size="sm" onClick={()=>setSiteOpen(true)}>Inspect residue evidence</Button><Button variant="outline" size="sm" onClick={()=>{setSiteOpen(false);onSelectPosition(null);document.querySelector<HTMLButtonElement>(`#sequence [data-residue="${selectedPosition}"]`)?.focus({preventScroll:true});}}><X size={15}/>Clear residue selection</Button></div></SelectionFeedback>
      {activeFeature&&<FeatureDetails key={activeFeature.id} accession={accession} feature={activeFeature} onClose={()=>setActiveFeature(null)}/>}
      {selectedPosition && siteOpen && <Modal title={`${data.sequence[selectedPosition-1]}${selectedPosition} · residue evidence`} closeRequested={siteCloseRequested} onClose={finishSiteClose}><ResidueEvidence accession={accession} position={selectedPosition} residue={data.sequence[selectedPosition-1]} tracks={tracks} scores={data.conservation??[]} summary={variantSummary.data} lens={atlasLens} predictor={atlasPredictor} initialSource={atlasSource} initialPtmType={atlasPtmType} onFeature={feature=>requestSiteClose(()=>setActiveFeature(feature))} onVariants={openSiteVariants} onStructure={()=>requestSiteClose(()=>requestAnimationFrame(()=>document.getElementById('structure')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})))}/></Modal>}
      <UnmappedAnnotations accession={accession}/>
    </>}
  </section>;
}
