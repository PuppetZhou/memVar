import { useState, type CSSProperties } from 'react';
import { ArrowLeft, ArrowRight, Database, Search } from 'lucide-react';
import { number, label } from '../api';
import './ppi-overview.css';
import { HelpButton } from './HelpGuide';

export interface PpiCollection {dataset_id:string;source:string;kind:string;context:string|null;source_release:string|null;records:number;}
// Presentation order only; explicit collection choices and record scopes stay intact.
export function sortPpiCollections(collections:PpiCollection[]){
 const rank=(c:PpiCollection)=>c.kind.endsWith('_full')?0:c.kind==='intact_mutation'?2:1;
 const sourceRank=(source:string)=>source==='IntAct'?0:source==='BioGRID'?1:2;
 return [...collections].sort((a,b)=>rank(a)-rank(b)||sourceRank(a.source)-sourceRank(b.source));
}
interface TypeGroup {key:string;label:string;count:number|null;source?:string;}
export function collectionLabel(collection:PpiCollection){
 if(collection.kind==='intact_mutation')return 'IntAct mutation';
 if(collection.kind.endsWith('_full'))return `${collection.source} · full collection`;
 return (collection.context??collection.kind).replaceAll('_',' ').replace(/\s+project$/i,'').replace(/\s+/g,' ').trim();
}
export function collectionTopicLabel(collection:PpiCollection){
 if(collection.kind==='intact_mutation')return 'Mutation evidence';
 if(collection.kind.endsWith('_full'))return 'Full collection';
 return collectionLabel(collection);
}
const colours=['#0d9488','#6366f1','#f59e0b','#ec4899','#06b6d4','#8b5cf6','#f97316','#2563eb','#65a30d','#d946ef','#14b8a6','#64748b'];
const knownColours:Record<string,string>={'BioGRID: physical':'#0d9488','BioGRID: genetic':'#6366f1','IntAct: association':'#2563eb','IntAct: physical association':'#0891b2','IntAct: direct interaction':'#10b981','IntAct: colocalization':'#eab308','IntAct: proximity':'#f97316','IntAct: phosphorylation reaction':'#db2777','IntAct: dephosphorylation reaction':'#9333ea','IntAct: phosphotransfer reaction':'#65a30d'};
const mutationColours:Record<string,string>={'mutation increasing':'#168b79','mutation increasing strength':'#168b79','mutation increasing rate':'#168b79','mutation decreasing':'#d18124','mutation decreasing strength':'#d18124','mutation decreasing rate':'#d18124','mutation disrupting':'#ce466f','mutation disrupting strength':'#ce466f','mutation with no effect':'#3b78ba','mutation causing':'#8b55ba','mutation':'#7b879d'};
const typeColour=(key:string)=>{const mutationColour=mutationColours[key.replace(/^IntAct: /,'')];if(mutationColour)return mutationColour;if(knownColours[key])return knownColours[key];let hash=0;for(const c of key)hash=(hash*31+c.charCodeAt(0))>>>0;return colours[hash%colours.length];};
function CategoryRing({groups,mutation,title}:{groups:TypeGroup[];mutation:boolean;title:string}){
 const [hover,setHover]=useState<string|null>(null);const total=groups.reduce((sum,g)=>sum+(g.count??0),0);let offset=0;
 const slices=groups.map(g=>{const start=offset;offset+=(g.count??0)/(total||1)*100;return {...g,start,size:(g.count??0)/(total||1)*100};});
 return <div className="ppi-ring-card"><div><h3>{mutation?'Effects on interaction':'Interaction categories'}</h3><p>{title} · current filters</p></div><div className="ppi-ring-layout"><svg viewBox="0 0 160 160" role="img" aria-label={`${total} ${mutation?'mutation feature':'interaction'} records across ${groups.length} source categories`}><circle cx="80" cy="80" r="59" fill="none" stroke="#e7edf5" strokeWidth="19"/>{slices.map(g=><circle key={g.key} cx="80" cy="80" r="59" fill="none" stroke={typeColour(g.key)} strokeWidth={hover===g.key?23:19} pathLength="100" strokeDasharray={`${g.size} ${100-g.size}`} strokeDashoffset={-g.start} transform="rotate(-90 80 80)" opacity={!hover||hover===g.key?1:.35} onPointerEnter={()=>setHover(g.key)} onPointerLeave={()=>setHover(null)}><title>{g.label}: {number(g.count,0)} records ({g.size.toFixed(1)}%)</title></circle>)}<text x="80" y="78" textAnchor="middle" className="ppi-ring-total">{number(total,0)}</text><text x="80" y="98" textAnchor="middle" className="ppi-ring-unit">{mutation?'feature records':'source records'}</text></svg><ul className="ppi-ring-legend">{slices.map(g=><li key={g.key} tabIndex={0} onFocus={()=>setHover(g.key)} onBlur={()=>setHover(null)} onPointerEnter={()=>setHover(g.key)} onPointerLeave={()=>setHover(null)} title={`${g.label}: ${g.size.toFixed(1)}%`}><i style={{background:typeColour(g.key)}}/><span>{label(g.label)}</span><strong>{number(g.count,0)}</strong><small>{g.size.toFixed(1)}%</small></li>)}{!groups.length&&<li>No category records match these filters.</li>}</ul></div></div>;
}

export function PpiOverview({collections,groups,dataset,source,onChoose}:{collections:PpiCollection[];groups:TypeGroup[];dataset:string;source:string;onChoose:(filter:Record<string,string>)=>void}){
 const [search,setSearch]=useState(''),[showAll,setShowAll]=useState(false);
 const ordered=sortPpiCollections(collections),full=ordered.filter(c=>c.kind.endsWith('_full'));
 const sources=[...new Set(ordered.map(c=>c.source))];
 const topics=source?ordered.filter(c=>c.source===source&&c.records>0):[];
 const searchText=search.trim().toLowerCase().replace(/['’]/g,'');
 const shown=topics.filter(c=>`${collectionTopicLabel(c)} ${c.kind}`.replaceAll('_',' ').toLowerCase().replace(/['’]/g,'').includes(searchText));
 const selected=collections.find(c=>c.dataset_id===dataset);const title=selected?collectionLabel(selected):source?`${source} collections`:'All sources';
 const choose=(c:PpiCollection)=>onChoose({dataset:c.dataset_id,source:c.source});
 const chooseSource=(value:string)=>{setSearch('');setShowAll(false);onChoose({source:value});};
 return <div className="ppi-overview"><div className="ppi-overview-intro"><div><span className="ppi-eyebrow">Source collections</span><h3>Interaction evidence <HelpButton topic="ppi"/></h3></div>{source&&<button className="button subtle" onClick={()=>chooseSource('')}><ArrowLeft size={14}/>Sources</button>}</div>
 <nav className="ppi-path" aria-label="Current interaction evidence selection"><button onClick={()=>chooseSource('')}>Sources</button>{source&&<><ArrowRight size={13}/><button className={dataset?'':'is-current'} onClick={()=>chooseSource(source)}>{source}</button></>}{selected&&<><ArrowRight size={13}/><strong>{collectionTopicLabel(selected)}</strong></>}</nav>
 <CategoryRing groups={groups} mutation={selected?.kind==='intact_mutation'} title={title}/>
 {!source?<section className="ppi-stage"><header><Database size={18} aria-hidden="true"/><div><h3>Sources</h3><p>Source definitions remain separate.</p></div></header><div className="ppi-entry-grid ppi-source-grid">{sources.map(provider=>{const collection=full.find(c=>c.source===provider);return <button className="ppi-entry" key={provider} style={{'--ppi-accent':provider==='BioGRID'?'#0d9488':'#6366f1'} as CSSProperties} disabled={!collection?.records} onClick={()=>chooseSource(provider)}><div className="ppi-entry-top"><span className="ppi-entry-icon"><Database size={20}/></span><span className="ppi-entry-tag">Source</span><ArrowRight size={17}/></div><h3>{provider}</h3><div className="ppi-entry-count">{number(collection?.records,0)}<span>full-collection records</span></div></button>;})}</div></section>:
 <section className="ppi-context-panel ppi-topic-stage"><header><div><span className="ppi-eyebrow">{source}</span><h3>Collections</h3><p>{topics.length} available collections · overlapping memberships stay distinct</p></div><label className="ppi-context-search"><Search size={15}/><input aria-label={`Search ${source} PPI topics`} value={search} onChange={e=>{setSearch(e.target.value);setShowAll(false);}} placeholder="Full collection, cancer, autophagy…"/></label></header>
 <div className="ppi-context-grid">{(showAll?shown:shown.slice(0,12)).map(c=><button key={c.dataset_id} className={dataset===c.dataset_id?'is-selected':''} aria-pressed={dataset===c.dataset_id} onClick={()=>choose(c)} title={`${c.source} · ${label(c.context??c.kind)} · ${c.records} stored records`}><span className={`ppi-source-label ppi-source-${c.source.toLowerCase()} ppi-kind-${c.kind==='intact_mutation'?'mutation':c.kind.endsWith('_full')?'full':'topic'}`}>{c.kind==='intact_mutation'?'Mutation':c.kind.endsWith('_full')?'Full':'Topic'}</span><strong>{collectionTopicLabel(c)}</strong><span className="ppi-context-count">{number(c.records,0)} records <ArrowRight size={13}/></span></button>)}{!shown.length&&<p>No topic matches this search.</p>}</div>
 {shown.length>12&&<button className="ppi-more" onClick={()=>setShowAll(!showAll)}>{showAll?'Show fewer topics':`Show all ${shown.length} matching topics`}</button>}</section>}
 </div>;
}
