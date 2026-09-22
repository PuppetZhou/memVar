import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { ArrowRight, ArrowUpRight, MapPin, X } from 'lucide-react';
import { display, type RecordData } from '../api';
import { Badge, Disclosure, Fields, LinkOut, Modal } from './ui';
import { SelectionFeedback } from '../lib/motion';
import { Button } from './ui/button';
import './cell-location.css';

type LocationLabel={name:string;source:string;scopeKey:string;scopeLabel:string;reliability?:string;records:{parent:RecordData;item:RecordData}[]};
type LocationRegionKey='extracellular'|'plasma_membrane'|'cytoplasm'|'nucleus'|'endoplasmic_reticulum'|'golgi'|'mitochondrion'|'endosome'|'lysosome'|'peroxisome'|'vesicle'|'cytoskeleton';
type LocationRegion={key:LocationRegionKey;label:string;color:string;matches:(name:string)=>boolean};
const locationRegions:LocationRegion[]=[
 {key:'extracellular',label:'Extracellular',color:'#7b95c6',matches:name=>/secreted|extracellular/i.test(name)},
 {key:'cytoplasm',label:'Cytoplasm',color:'#d0e2c0',matches:name=>/cytoplasm|cytosol/i.test(name)},
 {key:'endoplasmic_reticulum',label:'Endoplasmic reticulum',color:'#67a583',matches:name=>/endoplasmic reticulum|\bER membrane\b/i.test(name)},
 {key:'plasma_membrane',label:'Plasma membrane',color:'#49a6a9',matches:name=>/cell membrane|plasma membrane|cell surface/i.test(name)},
 {key:'nucleus',label:'Nucleus',color:'#7b95c6',matches:name=>/nucle|chromosome|chromatin/i.test(name)},
 {key:'golgi',label:'Golgi',color:'#f59c7c',matches:name=>/golgi/i.test(name)},
 {key:'mitochondrion',label:'Mitochondrion',color:'#fded95',matches:name=>/mitochond/i.test(name)},
 {key:'endosome',label:'Endosome',color:'#49c2d9',matches:name=>/endosom/i.test(name)},
 {key:'lysosome',label:'Lysosome',color:'#c85e62',matches:name=>/lysosom/i.test(name)},
 {key:'peroxisome',label:'Peroxisome',color:'#a2c986',matches:name=>/peroxisom/i.test(name)},
 {key:'vesicle',label:'Vesicle',color:'#a1d8e8',matches:name=>/vesicle|granule|secretory/i.test(name)},
 {key:'cytoskeleton',label:'Cytoskeleton / junction',color:'#9b7b59',matches:name=>/cytoskeleton|junction|adhesion|cili|basal body|centrosome|microtubule|actin|end piece|mid piece|principal piece/i.test(name)},
];
function regionFor(name:string){return locationRegions.find(region=>region.matches(name))?.key;}
function sourceText(value:unknown):string{if(value==null)return '';if(Array.isArray(value))return value.map(sourceText).filter(Boolean).join('\n');if(typeof value==='object'){const row=value as RecordData;return sourceText(row.text??row.texts??row.value??'');}return String(value);}
function labelsForSource(uniprot:RecordData[],hpa:RecordData[]):LocationLabel[]{
 const rows:LocationLabel[]=[];
 const add=(row:LocationLabel)=>{const existing=rows.find(item=>item.source===row.source&&item.scopeKey===row.scopeKey&&item.name===row.name);if(existing)existing.records.push(...row.records);else rows.push(row);};
 for(const parent of uniprot){const ids=Array.isArray(parent.isoform_ids)?parent.isoform_ids.map(String):[];const scopeKey=JSON.stringify([parent.scope_type,parent.scope_label,ids]);const scopeLabel=parent.scope_label?display(parent.scope_label):parent.scope_type==='entry'?'Protein entry':display(parent.scope_type);for(const raw of Array.isArray(parent.locations)?parent.locations:[]){const item=raw as RecordData;add({name:display(item.location),source:'UniProt',scopeKey,scopeLabel,records:[{parent,item}]});}}
 for(const parent of hpa){const scopeKey=String(parent.gene_id);const names=[...String(parent.main_location??'').split(';'),...String(parent.additional_location??'').split(';')].map(name=>name.trim()).filter(Boolean);for(const name of new Set(names)){const reliability=['enhanced','supported','approved','uncertain'].filter(key=>String(parent[key]??'').split(';').some(value=>value.trim()===name)).join(' / ');add({name,source:'HPA',scopeKey,scopeLabel:`Gene ${scopeKey}`,reliability,records:[{parent,item:parent}]});}}
 return rows;
}
function LocationEvidence({row,onClose}:{row:LocationLabel;onClose:()=>void}){
 return <Modal title={row.name} onClose={onClose}><div className="ov-location-evidence-heading"><Badge>{row.source}</Badge><strong>{row.scopeLabel}</strong>{row.reliability&&<span>{row.reliability}</span>}</div>{row.records.map(({parent,item},index)=>{const location=(item.location??{}) as RecordData;const evidence=[...(Array.isArray(location.evidences)?location.evidences:[]),...(Array.isArray((item.topology as RecordData)?.evidences)?(item.topology as RecordData).evidences as RecordData[]:[])];return <article className="annotation" key={index}><Fields items={[{label:'Original location',value:row.name},{label:'Location ID',value:location.id},{label:'Applies to',value:row.scopeLabel},{label:'Specified isoforms',value:parent.isoform_ids},{label:'Topology',value:item.topology},{label:'Orientation',value:item.orientation},{label:'Association status',value:parent.mapping_status},{label:'Location reliability',value:row.reliability}]}/>{evidence.length>0&&<div className="badge-list">{evidence.map((entry,i)=><LinkOut key={i} href={entry.source==='PubMed'&&entry.id?`https://pubmed.ncbi.nlm.nih.gov/${entry.id}/`:undefined}>{entry.source==='PubMed'?`PMID:${display(entry.id)}`:display(entry.evidenceCode??entry.source)}</LinkOut>)}</div>}{!!parent.notes&&<Disclosure title="Source location notes"><p className="preserve-lines">{sourceText(parent.notes)}</p></Disclosure>}{row.source==='HPA'&&<LinkOut href={parent.url}>Human Protein Atlas subcellular evidence</LinkOut>}</article>;})}</Modal>;
}
// These IDs identify illustration geometry only. Source-label grouping remains in regionFor.
const illustrationRegions:Record<LocationRegionKey,{id:string;short:string;x:number;y:number}>={
 extracellular:{id:'SL0243',short:'Ex',x:88,y:9},
 plasma_membrane:{id:'SL0039',short:'PM',x:92,y:43},
 cytoplasm:{id:'SL0086',short:'Cy',x:28,y:35},
 nucleus:{id:'SL0191',short:'Nu',x:48,y:53},
 endoplasmic_reticulum:{id:'SL0095',short:'ER',x:66,y:55},
 golgi:{id:'SL0132',short:'Go',x:67,y:26},
 mitochondrion:{id:'SL0173',short:'Mt',x:52,y:77},
 endosome:{id:'SL0101',short:'En',x:56,y:13},
 lysosome:{id:'SL0158',short:'Ly',x:41,y:28},
 peroxisome:{id:'SL0204',short:'Px',x:27,y:24},
 vesicle:{id:'SL0075',short:'Ve',x:63,y:36},
 cytoskeleton:{id:'SL0090',short:'Ck',x:25,y:68},
};
function CellLocationMap({rows,selected,onSelect}:{rows:LocationLabel[];selected:LocationRegionKey|null;onSelect:(region:LocationRegionKey|null)=>void}){
 const [animalCell,setAnimalCell]=useState('');
 const [artError,setArtError]=useState(false);
 const [hovered,setHovered]=useState<LocationRegionKey|null>(null);
 const illustration=useRef<HTMLDivElement>(null);
 const regionList=useRef<HTMLDivElement>(null);
 const counts=new Map<LocationRegionKey,number>();
 for(const row of rows){const region=regionFor(row.name);if(region)counts.set(region,(counts.get(region)??0)+1);}
 const active=hovered??selected;
 const coverageKey=[...counts.keys()].join(',');
 useEffect(()=>{
  let mounted=true;
  import('../assets/animal-cell.svg?raw').then(asset=>{if(mounted)setAnimalCell(asset.default);})
   .catch(()=>{if(mounted)setArtError(true);});
  return ()=>{mounted=false;};
 },[]);
 useEffect(()=>{
  const root=illustration.current;
  if(!root)return;
  for(const [key,{id}] of Object.entries(illustrationRegions)){
   root.querySelectorAll(`[id="${id}"]`).forEach(node=>node.setAttribute('data-memvar-region',key));
  }
  const present=new Set(coverageKey.split(','));
  root.querySelectorAll<SVGElement>('.coloured').forEach(node=>{
   const key=node.closest('[data-memvar-region]')?.getAttribute('data-memvar-region');
   const region=locationRegions.find(region=>region.key===key);
   if(region&&node.tagName!=='rect')node.setAttribute('data-cell-owner',region.key);
   // Keep the white canvas and unannotated geometry neutral; category tint is not abundance.
   if(region&&present.has(region.key)&&node.tagName!=='rect'&&node.getAttribute('fill')!=='#FFFFFF'){
    node.style.fill=`color-mix(in srgb, ${region.color} 55%, white)`;
   }else node.style.removeProperty('fill');
  });
 },[coverageKey,animalCell]);
 useEffect(()=>{
  const root=illustration.current;
  root?.querySelectorAll('[data-cell-active="true"]').forEach(node=>node.removeAttribute('data-cell-active'));
  if(active)root?.querySelectorAll(`[data-cell-owner="${active}"]`).forEach(node=>node.setAttribute('data-cell-active','true'));
 },[active,coverageKey,animalCell]);
 const pointerRegion=(target:EventTarget)=>{
  const key=target instanceof Element?target.closest('[data-memvar-region]')?.getAttribute('data-memvar-region') as LocationRegionKey|undefined:undefined;
  return key&&counts.has(key)?key:null;
 };
 const annotated=locationRegions.filter(region=>counts.has(region.key));
 const unannotated=locationRegions.filter(region=>!counts.has(region.key));
 return <div className="cell-location-map">
  <div className="cell-location-guide"><MapPin size={14}/><span>Select a region to inspect its original source labels</span></div>
  <div className="cell-location-layout">
   <div className="cell-location-figure" onPointerLeave={()=>setHovered(null)}>
    {/* Trusted, bundled CC BY 4.0 illustration; no remote or API HTML is injected. */}
    <div ref={illustration} className="cell-location-art" aria-hidden="true"
     onPointerOver={event=>setHovered(pointerRegion(event.target))}
     onClick={event=>{const key=pointerRegion(event.target);if(key)onSelect(key);}}
     dangerouslySetInnerHTML={{__html:animalCell}}/>
    {artError&&<span className="cell-location-art-status">Illustration unavailable. Source labels remain accessible.</span>}
    {animalCell&&<div className="cell-location-pins" aria-hidden="true">{annotated.map(region=>{
     const pin=illustrationRegions[region.key];
     return <span key={region.key} data-active={active===region.key} style={{left:`${pin.x}%`,top:`${pin.y}%`,'--region-color':region.color} as CSSProperties}>{pin.short}</span>;
    })}</div>}
    <span className="cell-location-figure-caption">Animal cell · schematic</span>
   </div>
   <div ref={regionList} className="cell-location-region-list" role="group" aria-label="Cellular regions with source annotations">
    <p>Annotated regions <span>{annotated.length}</span></p>
    {annotated.map(region=><button key={region.key} type="button"
     className="cell-location-region" aria-pressed={selected===region.key}
     data-highlighted={active===region.key} style={{'--region-color':region.color} as CSSProperties}
     onPointerEnter={()=>setHovered(region.key)} onPointerLeave={()=>setHovered(null)}
     onFocus={()=>setHovered(region.key)} onBlur={()=>setHovered(null)}
     onClick={()=>onSelect(region.key)}>
     <span className="cell-location-abbr" aria-hidden="true">{illustrationRegions[region.key].short}</span>
     <span className="cell-location-region-name">{region.label}<small>{[...new Set(rows.filter(row=>regionFor(row.name)===region.key).map(row=>`${row.source} · ${row.name}`))].slice(0,2).join(' / ')}</small></span>
     <span className="cell-location-count" aria-label={`${counts.get(region.key)} source labels`}>{counts.get(region.key)}</span>
     <ArrowRight size={13} aria-hidden="true"/>
    </button>)}
    {!annotated.length&&<span className="muted">No labels match the illustrated regions.</span>}
    <Button variant="ghost" size="sm" disabled={!selected} onClick={()=>{
     const trigger=regionList.current?.querySelector<HTMLButtonElement>('[aria-pressed="true"]');
     onSelect(null);requestAnimationFrame(()=>trigger?.focus({preventScroll:true}));
    }} className="cell-location-clear"><X/>Clear region</Button>
   </div>
  </div>
  <footer className="cell-location-footer"><details className="cell-location-notes"><summary>Reading notes{unannotated.length?` · ${unannotated.length} unannotated regions`:''}</summary><p>Counts are source labels, not abundance. No annotation does not establish biological absence.</p>{unannotated.length>0&&<p>{unannotated.map(region=>region.label).join(' · ')}</p>}</details><span className="cell-location-credit"><a href="https://www.swissbiopics.org/" target="_blank" rel="noreferrer">SwissBioPics / SIB</a> · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a> · adapted</span></footer>
 </div>;
}
export default function OverviewLocations({accession,uniprot,hpa}:{accession:string;uniprot:RecordData[];hpa:RecordData[]}){
 const rows=labelsForSource(uniprot,hpa);
 const [selection,setSelection]=useState({source:'All sources',scope:''});
 const [selected,setSelected]=useState<LocationLabel|null>(null);
 const [selectedRegion,setSelectedRegion]=useState<LocationRegionKey|null>(null);
 const [showAll,setShowAll]=useState(false);
 const availableSources=['UniProt','HPA'].filter(source=>rows.some(row=>row.source===source));
 const sources=['All sources',...availableSources];
 const source=sources.includes(selection.source)?selection.source:'All sources';
 const sourceRows=source==='All sources'?rows:rows.filter(row=>row.source===source);
 const scopes=[...new Map(sourceRows.map(row=>[row.scopeKey,row.scopeLabel])).entries()];
 const scopeKey=scopes.some(([key])=>key===selection.scope)?selection.scope:'';
 const scoped=scopeKey?sourceRows.filter(row=>row.scopeKey===scopeKey):sourceRows;
 const mapped=scoped.filter(row=>regionFor(row.name));
 const unmapped=scoped.filter(row=>!regionFor(row.name));
 const regionRows=selectedRegion?mapped.filter(row=>regionFor(row.name)===selectedRegion):[];
 const selectedRegionName=locationRegions.find(region=>region.key===selectedRegion)?.label;
 return <section className="ov-section ov-teal ov-location-section">
  <header><span className="ov-icon"><MapPin size={22}/></span><h3>Cellular location</h3><span className="ov-source">{scoped.length} source labels</span></header>
  <div className="ov-section-body">
   <div className="ov-location-controls">
    <label>Source <select aria-label="Location source" value={source} onChange={event=>{setSelection({source:event.target.value,scope:''});setSelectedRegion(null);setShowAll(false);}}>{sources.map(candidate=><option key={candidate}>{candidate}</option>)}</select></label>
    <label>Applies to <select aria-label="Location biological scope" value={scopeKey} onChange={event=>{setSelection(current=>({...current,scope:event.target.value}));setSelectedRegion(null);setShowAll(false);}}><option value="">All available objects</option>{scopes.map(([key,name])=><option key={key} value={key}>{name}</option>)}</select></label>
   </div>
   {!scoped.length?<p className="ov-no-data">No location annotations available.</p>:<><CellLocationMap rows={mapped} selected={selectedRegion} onSelect={setSelectedRegion}/><SelectionFeedback visible={Boolean(selectedRegion)}><section className="ov-location-region-records"><h4>{selectedRegionName}</h4><p>{regionRows.length} original source {regionRows.length===1?'label':'labels'} mapped to this display region.</p><div>{regionRows.map((row,index)=><button key={`${row.source}:${row.scopeKey}:${row.name}:${index}`} onClick={()=>setSelected(row)}><span><Badge tone={row.source==='HPA'?'teal':'neutral'}>{row.source}</Badge><strong>{row.name}</strong></span><small>{row.scopeLabel}{row.reliability?` · ${row.reliability}`:''}</small><ArrowUpRight size={13}/></button>)}</div></section></SelectionFeedback>{unmapped.length>0&&<section className="ov-location-unmapped"><h4>Other source locations</h4><p>These original terms are kept accessible but are not forced into a diagram region.</p><div className="ov-location-chips">{(showAll?unmapped:unmapped.slice(0,4)).map((row,index)=><button key={`${row.source}:${row.scopeKey}:${row.name}:${index}`} onClick={()=>setSelected(row)} title="View original location evidence"><Badge tone={row.source==='HPA'?'teal':'neutral'}>{row.source}</Badge><span>{row.name}</span><ArrowUpRight size={13}/></button>)}{unmapped.length>4&&<button className="ov-location-more" onClick={()=>setShowAll(!showAll)}>{showAll?'Show fewer':`+${unmapped.length-4} other locations`}</button>}</div></section>}</>}
  </div>
  <div className="ov-section-action">{source!=='HPA'&&<LinkOut href={`https://www.uniprot.org/uniprotkb/${accession}/entry#subcellular_location`}>UniProt location evidence</LinkOut>}{source!=='UniProt'&&typeof hpa[0]?.url==='string'&&<LinkOut href={hpa[0].url}>Human Protein Atlas location evidence</LinkOut>}</div>
  {selected&&<LocationEvidence row={selected} onClose={()=>setSelected(null)}/>} 
 </section>;
}
