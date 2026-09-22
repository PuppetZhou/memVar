import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, ChartNoAxesColumnIncreasing, Layers } from 'lucide-react';
import { api, display, label, params, type RecordData } from '../api';
import { Badge, Disclosure, Fields, LinkOut, Modal, PageJump, Status } from './ui';
import { featureStyle, sourceColors, type Feature, type Track, type VariantSummary } from './sequence-model';
import { VariantDistribution } from './VariantDistribution';
import './sequence-v2.css';

export function FeatureTrack({track,range,source,colourBy,onFeature}:{track:Track;range:[number,number];source:string;colourBy:string;onFeature:(f:Feature)=>void}) {
 const [hover,setHover]=useState<Feature[]|null>(null);const [cluster,setCluster]=useState<Feature[]|null>(null);
 const [localSource,setLocalSource]=useState('UniProt');const [expanded,setExpanded]=useState(false);const [regions,setRegions]=useState(false);
 const choices=Array.from(new Set(track.features.map(f=>f.source).filter(Boolean))) as string[];
 const scoped=track.id==='ptm'||track.id==='domains';const effectiveSource=source!=='all'?source:scoped?(localSource==='all'||choices.includes(localSource)?localSource:choices[0]??'all'):'all';
 const filtered=useMemo(()=>track.features.filter(f=>(effectiveSource==='all'||f.source===effectiveSource)&&f.end>=range[0]&&f.start<=range[1]&&(track.id!=='domains'||regions||f.source==='Pfam'||/^domain$/i.test(f.source_type??''))),[track,range,effectiveSource,regions]);
 const packed=useMemo(()=>{
   const span=range[1]-range[0]+1;const ends:number[]=[];const groups:Feature[][]=[];
   if(track.id==='ptm'&&!expanded){const width=Math.max(1,Math.ceil(span/80));const bins=new Map<number,Feature[]>();for(const f of filtered){const key=Math.floor((f.start-range[0])/width);const bin=bins.get(key)??[];bin.push(f);bins.set(key,bin);}groups.push(...bins.values());}
   else groups.push(...filtered.map(f=>[f]));
   return groups.sort((a,b)=>a[0].start-b[0].start).map(features=>{
     const lo=Math.min(...features.map(f=>f.start)),hi=Math.max(...features.map(f=>f.end));
     const rawStart=(Math.max(lo,range[0])-range[0])/span*1000,rawWidth=(Math.min(hi,range[1])-Math.max(lo,range[0])+1)/span*1000;
     const width=track.id==='ptm'&&!expanded?Math.max(9,rawWidth):Math.max(lo===hi?7:3,rawWidth);const start=rawStart+(rawWidth-width)/2;
     let lane=0;if(expanded){lane=ends.findIndex(x=>x+3<start);if(lane<0)lane=ends.length;ends[lane]=start+width;}
     return {features,start,width,lane,lo,hi};
   });
 },[filtered,range,track.id,expanded]);
 const lanes=Math.max(1,...packed.map(x=>x.lane+1));
 const tone=(f:Feature)=>colourBy==='source'?{name:f.source??'Source unavailable',color:sourceColors[f.source??'']??'#64748b'}:featureStyle(f,track.id);
 const legend=Array.from(new Map(filtered.map(f=>{const t=tone(f);return [t.name,t];})).values());
 const open=(features:Feature[])=>{const all=track.id==='ptm'||expanded?features:filtered.filter(f=>features.some(p=>f.start<=p.end&&f.end>=p.start));if(all.length===1)onFeature({...all[0],group:track.id});else setCluster(all);};
 return <div className="atlas-track"><div className="atlas-track-heading"><strong>{track.label}</strong><span>{filtered.length} annotations · {packed.length} markers</span>
   {scoped&&source==='all'&&<label className="track-source-control">Source <select aria-label={`${track.id} track source`} value={effectiveSource} onChange={e=>setLocalSource(e.target.value)}><option value="all">All sources</option>{choices.map(s=><option key={s}>{s}</option>)}</select></label>}
   {track.id==='domains'&&<label className="track-option"><input type="checkbox" checked={regions} onChange={e=>setRegions(e.target.checked)}/> Include regions / processing</label>}
   <button className="text-button" aria-pressed={expanded} onClick={()=>setExpanded(!expanded)}>{expanded?'Compact view':'Separate annotations'}</button>
  </div><div className="atlas-mini-legend">{legend.map(t=><span key={t.name}><i style={{background:t.color}}/>{t.name}</span>)}</div>
  <div className="atlas-track-scroll"><svg viewBox={`0 0 1000 ${Math.max(38,lanes*23+10)}`} preserveAspectRatio="none" style={{height:Math.max(38,lanes*23+10)}} aria-label={`${track.label} annotations`}>
   {packed.map(({features,start,width,lane,lo,hi},i)=>{const f=features[0];const colours=Array.from(new Set(features.map(f=>tone(f).color)));return <g key={`${f.id}-${i}`} role="button" tabIndex={0} aria-label={`${features.length>1?`${features.length} annotations`:f.label??f.source_type??track.label}, ${lo} to ${hi}, ${effectiveSource}. Open annotation details`} className="atlas-feature" onMouseEnter={()=>setHover(features)} onMouseLeave={()=>setHover(null)} onFocus={()=>setHover(features)} onBlur={()=>setHover(null)} onClick={()=>open(features)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open(features);}}}>
    <title>{lo}–{hi} · {features.length} annotations · click for source evidence</title>
    {colours.map((color,c)=><rect key={color} x={start} y={lane*23+8+c*18/colours.length} width={width} height={18/colours.length} rx={colours.length===1?4:0} fill={color} fillOpacity={track.id==='secondary'?.55:.9} stroke={color} strokeWidth={.8}/>)}
    {features.length>1&&width>=11&&<text x={start+width/2} y={lane*23+21} fontSize="10" fontWeight="700" textAnchor="middle" fill="white" pointerEvents="none">{features.length}</text>}
    {features.length===1&&width>100&&<text x={start+6} y={lane*23+21} fontSize="11" fill="white" pointerEvents="none">{String(f.label??f.source_type??'').slice(0,Math.floor(width/6))}</text>}
   </g>;})}
  </svg></div>
  <div className={`atlas-hover ${hover?'active':''}`} role="status">{hover?<><strong>{hover.length===1?hover[0].label??hover[0].source_type:`${hover.length} annotations · ${new Set(hover.map(f=>f.start)).size} positions`}</strong><span>{Math.min(...hover.map(f=>f.start))}–{Math.max(...hover.map(f=>f.end))}</span><span>{Array.from(new Set(hover.map(f=>tone(f).name))).join(' · ')}</span><small>Click for all source records</small></>:<span>{track.id==='ptm'&&!expanded?'Nearby sites share a marker; click to inspect individual positions and sources.':'Hover or focus to preview · click to inspect source evidence.'}</span>}</div>
  {cluster&&<Modal title={`${track.label} · ${Math.min(...cluster.map(f=>f.start))}–${Math.max(...cluster.map(f=>f.end))}`} onClose={()=>setCluster(null)}><p className="muted">{cluster.length} annotations share this display region. Their original positions and sources are retained.</p><div className="annotation-cluster-list">{cluster.map((f,i)=><button key={`${f.id}-${i}`} onClick={()=>{setCluster(null);onFeature({...f,group:track.id});}}><i style={{background:tone(f).color}}/><strong>{f.start===f.end?f.start:`${f.start}–${f.end}`}</strong><span>{f.label??f.source_type}<small>{f.source} · {tone(f).name}</small></span><ArrowRight size={16}/></button>)}</div></Modal>}
 </div>;
}

export function VariantDensity({summary,length,onRange}:{summary?:VariantSummary;length:number;onRange:(r:[number,number])=>void}) {
 const [,setSearch]=useSearchParams();
 const [selected,setSelected]=useState<[number,number]|null>(null);
 const showCatalog=()=>{if(!selected)return;setSearch(previous=>{const p=new URLSearchParams(previous);for(const k of Array.from(p.keys()))if(k.startsWith('variants_'))p.delete(k);p.set('variants_canonical_start',String(selected[0]));p.set('variants_canonical_end',String(selected[1]));return p;});document.getElementById('variants')?.scrollIntoView({behavior:'smooth'});};
 return <div className="atlas-density"><div className="atlas-subheading"><ChartNoAxesColumnIncreasing size={19}/><h3>Variant distribution</h3><span>{summary?`${summary.totals.canonical_mapped_variants.toLocaleString()} mapped variants · ${summary.canonical_sites.length.toLocaleString()} residues`:'Loading mapped variants…'}</span></div>
  {summary&&<VariantDistribution sites={summary.canonical_sites} length={length} selected={selected} onRange={r=>{setSelected(r);onRange(r);}}/>}
  <div className="atlas-density-footer"><p>Verified canonical mappings only. {summary?`${summary.totals.canonical_unmapped_variants.toLocaleString()} other catalogue variants have no verified position in this view.`:''}</p>{selected&&<button className="button" onClick={showCatalog}>Variants at {selected[0]}–{selected[1]} <ArrowRight size={14}/></button>}</div>
 </div>;
}

export { FullSequence } from './FullSequenceAtlas';

function SourceReference({record}:{record:RecordData}){const source=record.namespace??record.source;const id=record.identifier??record.id;const url=record.url??(source==='PubMed'&&id?`https://pubmed.ncbi.nlm.nih.gov/${id}/`:undefined);return <div className="sequence-source-reference"><LinkOut href={url}>{display(source??record.evidenceCode??'Source evidence')}{id?` · ${display(id)}`:''}</LinkOut>{!!record.evidenceCode&&<Badge>{display(record.evidenceCode)}</Badge>}{!!record.kind&&<span className="muted small">{display(record.kind)}</span>}</div>;}
function RecordEvidence({record}:{record:RecordData}) {
 const excluded=new Set(['sequence','sequence_id','accession','protein_accession','source_dataset','source_release','built_at','created_at','record_id','annotation_id','id','fields']);
 const scalar=Object.entries(record).filter(([k,v])=>!excluded.has(k)&&v!=null&&v!==''&&typeof v!=='object');
 const nested=Object.entries(record).filter(([k,v])=>!excluded.has(k)&&v!=null&&typeof v==='object');
 return <><Fields items={scalar.map(([k,v])=>({label:label(k),value:v}))}/>{nested.map(([k,v])=><Disclosure className="feature-nested" key={k} title={label(k)}>{(k==='evidence'||k==='evidences')&&Array.isArray(v)?v.map((e,i)=><SourceReference key={i} record={e as RecordData}/>):Array.isArray(v)?v.map((item,i)=><div className="feature-source-record" key={i}>{typeof item==='object'&&item?<RecordEvidence record={item as RecordData}/>:display(item)}</div>):<RecordEvidence record={v as RecordData}/>}</Disclosure>)}</>;
}
export function FeatureDetails({accession,feature,onClose}:{accession:string;feature:Feature;onClose:()=>void}) {
 const [offset,setOffset]=useState(0);
 useEffect(()=>{setOffset(0);},[accession,feature.id,feature.source,feature.group]);
 const source=feature.group==='ptm'?'PTM':feature.source==='Pfam'?'Pfam':feature.source==='DeepTMHMM2'?'DeepTMHMM2':feature.source==='UniProt'?'UniProt':'Topology';
 const query=useQuery<{feature:RecordData;records:RecordData[];evidence:RecordData[];has_more:boolean;coordinate_system:string;sequence_id:string}>({queryKey:['sequence-feature',accession,source,feature.id,offset],queryFn:({signal})=>api(`/proteins/${accession}/sequence/feature?${params({source,feature_id:feature.id,record_ids:feature.record_ids?.join(','),limit:10,offset})}`,signal)});
 return <Modal title={feature.label??feature.source_type??'Sequence annotation'} onClose={onClose}><div className="feature-detail-banner"><Layers size={25}/><div><strong>{feature.start===feature.end?`Residue ${feature.start}`:`Residues ${feature.start}–${feature.end}`}</strong><span>{feature.source} · {featureStyle(feature,feature.group??'').name}</span></div><Badge>{feature.source_type??feature.type??'Annotation'}</Badge></div>
  {feature.description&&<p className="feature-description">{feature.description}</p>}
  <Status loading={query.isPending} error={query.error}>{query.data&&<><p className="muted small">{query.data.sequence_id} · {query.data.coordinate_system}</p>{query.data.feature&&<RecordEvidence record={{...query.data.feature,evidence:undefined}}/>}<div className="feature-source-records">{query.data.records?.map((record,i)=><Disclosure className="feature-source-record" key={i} title={`Source annotation ${offset+i+1}`}><RecordEvidence record={record}/></Disclosure>)}</div>{query.data.evidence?.length>0&&<><h3>Source evidence</h3>{query.data.evidence.map((e,i)=><div className="feature-source-record" key={i}><SourceReference record={e}/></div>)}</>}{(offset>0||query.data.has_more)&&<div className="toolbar"><button className="button" disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-10))}>Previous annotations</button><PageJump page={offset/10} onJump={page=>setOffset(page*10)} maxPage={1000} loading={query.isFetching} label="Source annotation page"/><button className="button" disabled={!query.data.has_more||query.isFetching||offset>=10000} onClick={()=>setOffset(offset+10)}>More annotations</button></div>}</>}</Status>
 </Modal>;
}
