import { useState, type CSSProperties } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Boxes, GitBranch, Network, Shapes } from 'lucide-react';
import { api, display, number, params, type RecordData } from '../api';
import { HelpButton } from './HelpGuide';
import { LinkOut, Modal, Pager, Status } from './ui';
import { ReactomeEvidenceLabel } from './OverviewEvidence';

type GoCategory={category_id:string;name:string;namespace:string;url?:string;annotation_count:number;term_count:number;contexts:RecordData[]};
type GoSummary={totals:{annotation_count:number;term_count:number;negative_annotation_count:number};aspects:{aspect:string;annotation_count:number;term_count:number;negative_annotation_count:number}[];categories:GoCategory[];scope:string;notes:string[]};
export type GoSelection={aspect:string;slim_id?:string;name?:string};
const goAspects=[{aspect:'F',namespace:'molecular_function',title:'Molecular function',description:'Molecular activities',color:'#7145c5',icon:Shapes},{aspect:'P',namespace:'biological_process',title:'Biological process',description:'Processes and biological programmes',color:'#2379c3',icon:Network},{aspect:'C',namespace:'cellular_component',title:'Cellular component',description:'Locations of molecular activity',color:'#078f89',icon:Boxes}];
function GoAspect({spec,summary,onSelect}:{spec:typeof goAspects[number];summary:GoSummary;onSelect:(selection:GoSelection)=>void}){
 const [showAll,setShowAll]=useState(false);const categories=summary.categories.filter(item=>item.namespace===spec.namespace).sort((a,b)=>b.annotation_count-a.annotation_count||a.category_id.localeCompare(b.category_id));const maximum=Math.max(1,...categories.map(item=>item.annotation_count));const Icon=spec.icon;
 return <div className="ov-go-aspect" style={{'--go-color':spec.color} as CSSProperties}><div className="ov-go-aspect-heading"><Icon size={22}/><div><h4>{spec.title}</h4><p>{spec.description}</p></div></div><p className="ov-go-scale">GO-slim categories · source annotation records</p><div className="ov-go-bars">{!categories.length&&<p className="ov-no-data">No positive GO-slim category is available.</p>}{(showAll?categories:categories.slice(0,5)).map(category=><button key={category.category_id} onClick={()=>onSelect({aspect:spec.aspect,slim_id:category.category_id,name:category.name})} title={`${category.category_id} · ${category.annotation_count} source annotation records`}><div><span>{category.name}</span><strong>{number(category.annotation_count,0)}</strong></div><div className="ov-go-bar-track"><i style={{width:`${category.annotation_count/maximum*100}%`}}/></div></button>)}</div><div className="ov-go-aspect-actions">{categories.length>5&&<button className="ov-browse" onClick={()=>setShowAll(!showAll)}>{showAll?'Show fewer categories':`All ${categories.length} slim categories`}</button>}<button className="ov-browse" onClick={()=>onSelect({aspect:spec.aspect})}>Browse original annotations <ArrowRight size={13}/></button></div></div>;
}
export function OverviewGo({accession,onSelect}:{accession:string;onSelect:(selection:GoSelection)=>void}){
 const query=useQuery({queryKey:['overview-go-summary',accession],queryFn:({signal})=>api<GoSummary>(`/proteins/${accession}/overview/go/summary`,signal)});
 return <section className="ov-section ov-purple ov-wide ov-go-section"><header><span className="ov-icon"><Shapes size={22}/></span><h3>Gene Ontology <HelpButton topic="go"/></h3><span className="ov-source">GO · published slim mapping</span></header><div className="ov-section-body"><Status loading={query.isPending} error={query.error}>{query.data&&<div className="ov-go-grid">{goAspects.map(spec=><GoAspect key={spec.aspect} spec={spec} summary={query.data} onSelect={onSelect}/>)}</div>}</Status></div></section>;
}

type PathwaySummary={totals:{association_count:number;pathway_count:number};topics:{topic_id:string;name:string;association_count:number;pathway_count:number;filter:{topic_id:string}}[]};
type PathwayPage={items:RecordData[];has_more:boolean;total?:number};
function diagramUrl(pathway:RecordData){const id=String(pathway.pathway_id??'');return /^R-[A-Z]{3}-\d+$/.test(id)?`https://reactome.org/PathwayBrowser/#/${id}`:undefined;}
function PathwayCatalog({accession,summary,initialTopic}:{accession:string;summary?:PathwaySummary;initialTopic:string}){
 const [topic,setTopic]=useState(initialTopic);const [offset,setOffset]=useState(0);const limit=6;
 const query=useQuery({queryKey:['overview-pathway-cards',accession,topic,offset],queryFn:({signal})=>api<PathwayPage>(`/proteins/${accession}/overview/pathways?${params({topic_id:topic,limit,offset})}`,signal)});
 return <><div className="ov-location-controls"><label>Topic <select aria-label="Reactome topic" value={topic} onChange={event=>{setTopic(event.target.value);setOffset(0);}}><option value="">All topics</option>{summary?.topics.map(item=><option key={item.topic_id} value={item.topic_id}>{item.name} ({item.pathway_count} pathways)</option>)}</select></label></div>
 <Status loading={query.isPending} error={query.error} empty={!query.data?.items.length}>
  <p className="ov-visual-note">{number(query.data?.total,0)} source associations in this selection</p>
  <div className="ov-pathway-detail-list">{query.data?.items.map((pathway,index)=><article className="ov-pathway-record" key={String(pathway.association_id??index)}><div className="ov-pathway-record-main"><div><strong>{display(pathway.name)}</strong><small className="ov-pathway-id">{display(pathway.pathway_id)}</small></div><ReactomeEvidenceLabel code={pathway.evidence_code}/><LinkOut href={pathway.source_url}>Source record</LinkOut></div>{Array.isArray(pathway.topics)&&pathway.topics.length>0&&<div className="ov-pathway-record-topics">{pathway.topics.map((raw,i)=>{const item=raw as RecordData;return <span key={String(item.id??i)}>{display(item.name)}</span>;})}</div>}<div className="ov-pathway-card-actions"><LinkOut href={diagramUrl(pathway)}>Open official diagram</LinkOut></div></article>)}</div>
 </Status><Pager page={offset/limit} count={query.data?.items.length??0} next={query.data?.has_more?'next':null} onPrevious={()=>setOffset(Math.max(0,offset-limit))} onNext={()=>setOffset(offset+limit)} maxPage={Math.floor(100000/limit)} onJump={page=>setOffset(page*limit)} totalPages={query.data?.total == null ? undefined : Math.ceil(query.data.total/limit)} loading={query.isFetching}/></>;
}
export function OverviewReactome({accession}:{accession:string}){
 const [selection,setSelection]=useState<{topic:string}|null>(null);
 const summary=useQuery({queryKey:['overview-pathway-summary',accession],queryFn:({signal})=>api<PathwaySummary>(`/proteins/${accession}/overview/pathways/summary`,signal)});
 const preview=useQuery({queryKey:['overview-pathway-preview',accession],queryFn:({signal})=>api<PathwayPage>(`/proteins/${accession}/overview/pathways?limit=3&offset=0`,signal)});
 return <section className="ov-section ov-pathways ov-wide">
  <header><span className="ov-icon"><GitBranch size={22}/></span><h3>Reactome pathways <HelpButton title="Reactome pathways"><p>Curated pathways and reactions. Select a topic to browse linked pathways, then open the official diagram for molecular events.</p><p>Counts describe pathway associations, not pathway activity or enrichment.</p><div className="help-sources"><a href="https://reactome.org/userguide" target="_blank" rel="noreferrer">Reactome user guide ↗</a></div></HelpButton></h3><span className="ov-source">Reactome</span></header>
  <div className="ov-section-body ov-pathway-compact">
   <Status loading={summary.isPending} error={summary.error}>{summary.data&&<div className="ov-pathway-overview"><div className="ov-pathway-totals"><strong>{number(summary.data.totals.pathway_count,0)}</strong><span>pathways</span><small>{number(summary.data.totals.association_count,0)} source associations</small></div><div className="ov-pathway-topics">{summary.data.topics.slice(0,3).map(item=><button key={item.topic_id} onClick={()=>setSelection({topic:item.topic_id})}>{item.name}<span>{number(item.pathway_count,0)}</span></button>)}{summary.data.topics.length>3&&<button className="ov-pathway-more" onClick={()=>setSelection({topic:''})}>+{summary.data.topics.length-3} topics</button>}</div></div>}</Status>
   <Status loading={preview.isPending} error={preview.error} empty={!preview.data?.items.length}><ul className="ov-pathway-preview">{preview.data?.items.map((pathway,index)=><li key={String(pathway.association_id??index)}><GitBranch size={14}/><span>{display(pathway.name)}</span></li>)}</ul></Status>
  </div>
  <div className="ov-section-action"><button className="ov-browse" onClick={()=>setSelection({topic:''})}>View pathways <ArrowRight size={14}/></button></div>
  {selection&&<Modal title="Reactome pathways" onClose={()=>setSelection(null)}><PathwayCatalog accession={accession} summary={summary.data} initialTopic={selection.topic}/></Modal>}
 </section>;
}
