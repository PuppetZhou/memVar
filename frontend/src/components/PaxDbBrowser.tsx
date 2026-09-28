import { useState, type ReactNode } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { api, display, params } from '../api';
import { Status, Modal, LinkOut } from './ui';
import './paxdb.css';
export interface PaxContext {organ:string;context_type:string;body_region:string;records:number;}
interface PaxRow {record_key:string;organ:string;name:string;abundance:string;description:string;score:string;coverage:string;publication_year:string;link:string|null;integrated:boolean;}
interface PaxData {contexts:PaxContext[];items:PaxRow[];total:number;offset:number;limit:number;maximum:number|null;}
const kinds=[['tissue','Tissues'],['cell','Cells'],['fluid','Fluids & secretions'],['fraction','Cell fractions'],['whole','Whole organism']];
const contextName=(value:string)=>value.toLowerCase().replaceAll('_',' ').replace(/^./,s=>s.toUpperCase());
export function PaxDbBrowser({accession,dataset,renderTissues}:{accession:string;dataset:string;renderTissues:(contexts:PaxContext[],onChoose:(organ:string)=>void)=>ReactNode}){
 const [kind,setKind]=useState('tissue'),[organ,setOrgan]=useState(''),[selected,setSelected]=useState<PaxRow|null>(null);
 const collection=dataset==='paxdb_studies'?'studies':'integrated';
 const result=useInfiniteQuery({queryKey:['paxdb',accession,collection,kind,organ],initialPageParam:0,queryFn:({signal,pageParam})=>api<PaxData>(`/proteins/${accession}/expression/paxdb?${params({collection,context_type:kind,organ,offset:pageParam,limit:100})}`,signal),getNextPageParam:last=>last.offset+last.items.length<last.total?last.offset+last.items.length:undefined});
 const data=result.data?.pages[0];const rows=result.data?.pages.flatMap(page=>page.items)??[];const choose=(value:string)=>setOrgan(value);
 const maximum=Number(data?.maximum??0);

 return <section className="pax-browser" aria-label="PaxDB protein abundance">
  <p className="pax-note">Human protein abundance · ppm. Bars use a linear scale relative to the maximum in this selection.</p>
  <nav className="pax-kinds" aria-label="PaxDB context type">{kinds.map(([key,name])=><button key={key} aria-pressed={kind===key} onClick={()=>{setKind(key);choose('');}}>{name}</button>)}</nav>
  <Status loading={result.isPending} error={result.error}>{data&&<>
   {kind==='tissue'?renderTissues(data.contexts.filter(c=>c.context_type==='tissue'),choose):<div className="pax-context-list"><button onClick={()=>choose('')} aria-pressed={!organ}>All {kinds.find(([k])=>k===kind)?.[1].toLowerCase()}</button>{data.contexts.filter(c=>c.context_type===kind).map(c=><button key={c.organ} aria-pressed={organ===c.organ} onClick={()=>choose(c.organ)}>{contextName(c.organ)} <small>{c.records}</small></button>)}</div>}
   {kind==='cell'&&data.contexts.some(c=>c.organ==='CELL_LINE')&&<p className="pax-note">The source “Cell line” category also contains primary immune-cell datasets; individual dataset names retain this distinction.</p>}
   <div className="pax-table-heading"><strong>{organ?contextName(organ):kinds.find(([k])=>k===kind)?.[1]} · {data.total} records</strong>{organ&&<button onClick={()=>choose('')}>Clear selection</button>}</div>
   {data.total?<div className="table-wrap" key={`${collection}:${kind}:${organ}`} tabIndex={0} role="region" aria-label="PaxDB abundance records" onScroll={event=>{const el=event.currentTarget;if(el.scrollHeight-el.scrollTop-el.clientHeight<160&&result.hasNextPage&&!result.isFetching&&!result.isFetchNextPageError)void result.fetchNextPage();}}><table className="data-table"><thead><tr><th>{kind==='tissue'?'Tissue':'Context'}</th><th>Abundance (ppm)</th></tr></thead><tbody>{rows.map(row=><tr key={row.record_key}><td><button className="pax-record" onClick={()=>setSelected(row)}>{contextName(row.organ)}{collection==='studies'&&<small>{row.name.replace(/^H\.sapiens - /,'')}</small>}</button></td><td className="pax-value"><div className="pax-abundance"><span className="pax-abundance-track" aria-hidden="true"><span style={{width:`${maximum?Math.min(100,Number(row.abundance)/maximum*100):0}%`}}/></span><span>{display(row.abundance)}</span></div></td></tr>)}</tbody></table><div className="pax-scroll-status" role="status">{result.isFetchingNextPage?'Loading…':result.isFetchNextPageError?<button onClick={()=>result.fetchNextPage()}>Could not load more · Retry</button>:result.hasNextPage?'Scroll for more':`${rows.length} records`}</div></div>:<p>No values for this protein in this context. Missing is not zero.</p>}

  </>}</Status>
  {selected&&<Modal title={selected.integrated?contextName(selected.organ):selected.name.replace(/^H\.sapiens - /,'')} onClose={()=>setSelected(null)}><div className="pax-detail"><strong>{display(selected.abundance)} <small>ppm</small></strong><p>{contextName(selected.organ)} · {selected.integrated?'Integrated estimate':'Individual study'}</p><p>{selected.description}</p><dl><div><dt>Dataset score</dt><dd>{selected.score||'—'}</dd></div><div><dt>Coverage</dt><dd>{selected.coverage?`${selected.coverage}%`:'—'}</dd></div>{!selected.integrated&&selected.publication_year&&<div><dt>Publication year</dt><dd>{selected.publication_year}</dd></div>}</dl>{selected.link&&/^https?:\/\//.test(selected.link)&&<LinkOut href={selected.link}>Original study</LinkOut>}</div></Modal>}
 </section>;
}
