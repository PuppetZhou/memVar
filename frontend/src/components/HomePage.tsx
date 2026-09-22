import { useId, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Droplets, Network, Search, Waves, MapPin, X, Database } from 'lucide-react';
import { api } from '../api';
import './homepage.css';
import HomeEvidence from './HomeEvidence';
import { Button } from './ui/button';
import { ModeToggleGroup } from './ui/mode-toggle-group';
import { CollapseRegion } from '@/lib/motion';

export const membraneClasses = [
 {key:'integral_membrane',label:'Integral membrane · all',description:'Transmembrane or non-transmembrane lipid-anchored proteins.',color:'blue'},
 {key:'transmembrane',label:'Transmembrane · all',description:'Canonical UniProt transmembrane annotation.',color:'blue'},
 {key:'single_pass',label:'Single-pass transmembrane',description:'Exactly one canonical UniProt transmembrane feature.',color:'blue'},
 {key:'multi_pass',label:'Multi-pass transmembrane',description:'Two or more canonical UniProt transmembrane features.',color:'blue'},
 {key:'lipid_anchored',label:'Lipid-anchored · non-TM',description:'Explicit lipid-anchor evidence without a canonical transmembrane feature.',color:'orange'},
 {key:'peripheral_membrane',label:'Peripheral membrane',description:'Explicit peripheral topology after excluding integral proteins.',color:'purple'},
 {key:'membrane_related',label:'Mechanism unannotated',description:'Membrane-related entries without an explicit mechanism in this classification.',color:'teal'},
];
const homeMembraneClasses=membraneClasses.filter(item=>['integral_membrane','peripheral_membrane','membrane_related'].includes(item.key));
const integralChildren=membraneClasses.filter(item=>['single_pass','multi_pass','lipid_anchored'].includes(item.key));
interface CatalogSummary {total_proteins:number;classes:{key:string;label:string;count:number}[];locations:{id:string;label:string;count:number}[]}
export function useCatalogSummary(){return useQuery({queryKey:['catalog-summary'],queryFn:({signal})=>api<CatalogSummary>('/catalog/summary',signal),staleTime:300000});}
export function ProteinSearchForm({initial='',onSearch}:{initial?:string;onSearch:(value:string)=>void}){
 const [text,setText]=useState(initial);
 function submit(e:FormEvent){e.preventDefault();onSearch(text.trim());}
 return <form className="home-search" role="search" onSubmit={submit}><Search size={23} aria-hidden="true"/><input aria-label="Search a gene, protein name or UniProt ID" placeholder="Search a gene, protein name or UniProt ID" maxLength={120} value={text} onChange={e=>setText(e.target.value)}/><Button type="submit" size="lg">Search <ArrowRight data-icon="inline-end"/></Button></form>;
}
const membraneArtFrames:Record<string,string>={
 integral_membrane:'720 90 300 345',
 single_pass:'45 48 265 455',
 multi_pass:'355 68 330 420',
 lipid_anchored:'56 550 325 325',
 peripheral_membrane:'770 515 290 480',
};
function MembraneIcon({kind}:{kind:string}){
 const cropId=useId();
 if(kind==='membrane_related')return <svg className="home-membrane-art home-membrane-unknown" viewBox="0 0 180 180" aria-hidden="true">
  <rect x="12" y="91" width="59" height="29" fill="#d4ddd6"/><rect x="109" y="91" width="59" height="29" fill="#d4ddd6"/>
  <path d="M35 64c10-30 27 17 37-16 9-29 27 10 39-13 8-16 23-5 27 10" fill="none" stroke="#83bc41" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round"/>
  <circle cx="90" cy="106" r="23" fill="#f3f8ed" stroke="#8bbd50" strokeWidth="2" strokeDasharray="4 4"/>
  <text x="90" y="119" textAnchor="middle" fontSize="34" fontWeight="600" fill="#6f9e42">?</text>
 </svg>;
 const [x,y,width,height]=membraneArtFrames[kind].split(' ').map(Number);
 return <svg className="home-membrane-art" viewBox={membraneArtFrames[kind]} aria-hidden="true"><defs><clipPath id={cropId}><rect x={x} y={y} width={width} height={height}/></clipPath></defs><image clipPath={`url(#${cropId})`} href="/images/home/membrane-protein-reference.png" width="1448" height="1086"/></svg>;
}
function MembraneClassBrowser({summary}:{summary?:CatalogSummary}){
 const [expanded,setExpanded]=useState(false);
 const integralTrigger=useRef<HTMLButtonElement>(null);
 const count=(key:string)=>summary?.classes.find(item=>item.key===key)?.count;
 const cardBody=(item:(typeof membraneClasses)[number])=><>
  <MembraneIcon kind={item.key}/><h3>{item.key==='integral_membrane'?'Integral membrane':item.label}</h3><p>{item.description}</p>
  <div className="home-class-bottom"><span>{count(item.key)===undefined?'Count unavailable':<><strong>{count(item.key)?.toLocaleString('en-US')}</strong> entries</>}</span><span className="home-card-link">{item.key==='integral_membrane'?'Explore types':'Browse'} <ArrowRight size={17}/></span></div>
 </>;
 return <section className="home-classes" aria-labelledby="membrane-class-title"><div className="home-container">
  <h2 id="membrane-class-title">Browse by membrane class</h2>
  <p className="home-section-note">Three mutually exclusive main branches. Open integral membrane to see transmembrane subtypes and non-TM lipid anchoring.</p>
  <div className="home-class-grid home-class-grid-primary">{homeMembraneClasses.map(item=>item.key==='integral_membrane'
   ?<button ref={integralTrigger} type="button" className={`home-class-card home-tone-${item.color}`} key={item.key} aria-expanded={expanded} aria-controls="integral-membrane-branches" onClick={()=>setExpanded(value=>!value)}>{cardBody(item)}</button>
   :<Link to={`/search?membrane_class=${item.key}`} className={`home-class-card home-tone-${item.color}`} key={item.key}>{cardBody(item)}</Link>)}</div>
  <CollapseRegion open={expanded} id="integral-membrane-branches"><div className="home-integral-branches">
   <div className="home-branches-heading"><div><span className="home-branch-eyebrow">WITHIN INTEGRAL MEMBRANE</span><h3>Choose a membrane-attachment type</h3><p>Transmembrane proteins have one or more canonical UniProt TM features. The non-TM lipid-anchored branch remains distinct.</p></div><Button variant="outline" size="sm" onClick={()=>{setExpanded(false);integralTrigger.current?.focus({preventScroll:true});}}>Close <X data-icon="inline-end"/></Button></div>
   <div className="home-class-grid home-class-grid-children">{integralChildren.map(item=><Link to={`/search?membrane_class=${item.key}`} className={`home-class-card home-tone-${item.color}`} key={item.key}><span className="home-branch-type">{item.key==='lipid_anchored'?'Non-TM branch':'Transmembrane branch'}</span>{cardBody(item)}</Link>)}</div>
   <div className="home-branch-links"><Link to="/search?membrane_class=transmembrane">Browse all transmembrane <strong>{count('transmembrane')?.toLocaleString('en-US')??'—'}</strong> <ArrowRight size={15}/></Link><Link to="/search?membrane_class=integral_membrane">Browse all integral membrane <strong>{count('integral_membrane')?.toLocaleString('en-US')??'—'}</strong> <ArrowRight size={15}/></Link></div>
  </div></CollapseRegion>
 </div></section>;
}
function LocationBrowser(){
 const summary=useCatalogSummary();const navigate=useNavigate();const locations=summary.data?.locations??[];
 const top=locations.filter(item=>item.id!=='SL-0162').slice(0,8);const max=top[0]?.count||1;
 return <section className="home-locations home-container" aria-labelledby="location-title"><div className="home-location-heading"><div><span className="home-eyebrow"><MapPin size={14}/> WHERE PROTEINS ARE FOUND</span><h2 id="location-title">Browse by membrane location</h2><p className="home-section-note">Explore UniProt entry-level locations. A protein can occur in more than one place.</p></div><span className="home-source-tag">UniProt · Subcellular location</span></div>{summary.isError?<p role="alert">Locations are temporarily unavailable.</p>:summary.isPending?<p role="status">Loading membrane locations…</p>:<><div className="home-location-grid">{top.map((item,index)=><Link className="home-location-card" key={item.id} to={`/search?membrane_location=${item.id}`}><span className="home-location-number">{String(index+1).padStart(2,'0')}</span><div><h3>{item.label}</h3><div className="home-location-count"><span><strong>{item.count.toLocaleString('en-US')}</strong> proteins</span><ArrowRight size={16}/></div><span className="home-location-bar" aria-hidden="true"><span style={{width:`${100*item.count/max}%`}}/></span></div></Link>)}</div><div className="home-location-more"><label>Find another membrane location<select aria-label="Browse all membrane locations" defaultValue="" onChange={e=>{if(e.target.value)navigate(`/search?membrane_location=${e.target.value}`);}}><option value="">Browse all {locations.length} locations</option>{locations.map(item=><option key={item.id} value={item.id}>{item.label}{item.id==='SL-0162'?' (unspecified)':''} · {item.count.toLocaleString('en-US')}</option>)}</select></label><p>Counts represent protein entries, not expression levels. Isoform-specific locations remain in each protein’s details.</p></div></>}</section>;
}
const examples=[{gene:'EGFR',accession:'P00533',title:'Receptor signaling',description:'Sequence annotations, clinical variants and interaction evidence.',icon:Network,color:'blue'},{gene:'KCNH2',accession:'Q12809',title:'Ion channel',description:'Explore channel domains and variant evidence.',icon:Waves,color:'purple'},{gene:'AQP4',accession:'P55087',title:'Water transport',description:'Compare membrane topology with tissue expression.',icon:Droplets,color:'teal'}];
export default function HomePage(){
 const navigate=useNavigate();const summary=useCatalogSummary();const [backdrop,setBackdrop]=useState('diversity');
 return <main className="home-page"><section className={`home-hero home-hero-${backdrop}`}><span className="home-hero-eyebrow">THE HUMAN MEMBRANE PROTEIN ATLAS</span><h1>Explore human<br/>membrane proteins</h1><p className="home-subtitle">Connect sequence, variants and molecular evidence in one place.</p><ProteinSearchForm onSearch={query=>navigate(`/search${query?`?query=${encodeURIComponent(query)}`:''}`)}/><div className="home-try">Try {examples.map(item=><Link key={item.gene} to={`/protein/${item.accession}`}>{item.gene}</Link>)}</div><p className="home-count" aria-live="polite">{summary.data?`${summary.data.total_proteins.toLocaleString('en-US')} protein entries · Source-linked evidence`:summary.isError?'Protein counts are temporarily unavailable. Search remains available.':'Loading protein entries…'}</p><div className="home-hero-controls"><a className="home-data-jump" href="#data-layers">Explore 7 data layers <ArrowRight size={14}/></a><div className="home-background-switch"><span>Background</span><ModeToggleGroup aria-label="Homepage background" value={backdrop} onValueChange={setBackdrop} options={[{id:'bilayer',name:'Lipid bilayer'},{id:'diversity',name:'Protein landscape'},{id:'ribbon',name:'Green ribbons'}].map(item=>({value:item.id,ariaLabel:`${item.name} background`,label:<><span className={`home-swatch home-swatch-${item.id}`}/><span>{item.name}</span></>}))}/></div></div></section><HomeEvidence/><MembraneClassBrowser summary={summary.data}/><LocationBrowser/><section className="home-examples home-container" aria-labelledby="examples-title"><h2 id="examples-title">Start with an example</h2><div className="home-example-grid">{examples.map(({icon:Icon,...item})=><Link key={item.gene} className={`home-example-card home-tone-${item.color}`} to={`/protein/${item.accession}`}><Icon className="home-example-icon" size={35} strokeWidth={1.6}/><div><h3>{item.gene}<span>{item.title}</span></h3><p>{item.description}</p><span className="home-example-accession"><Database size={14} aria-hidden="true"/>UniProt <strong>{item.accession}</strong></span><span className="home-card-link">Open protein <ArrowRight size={15}/></span></div></Link>)}</div></section></main>;
}
