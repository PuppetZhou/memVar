import { lazy, memo, Suspense, useEffect, useState, type FormEvent } from 'react';
import { Link, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, Atom, BookOpen, Dna, Fingerprint, HeartPulse, Network, Search, SlidersHorizontal } from 'lucide-react';
import { api } from './api';
import brandLogo from './assets/memvar-logo.png';
import OverviewContent, { type OverviewData } from './components/Overview';
import { Diseases, Expression, Interactions, Qtl } from './components/ContextPanels';
import { AlphaGenomeExpression } from './components/AlphaGenomeExpression';
import Variants from './components/VariantCatalog';
import { Status } from './components/ui';
import { ResultsPage, DocumentationPage } from './components/DatabasePages';
import HomePage from './components/HomePage';
import SearchPage from './components/ProteinSearch';
// Residue selection should only rerender the three linked scientific views.
// These sections depend on the accession (and expression context), not selection.
const Overview=memo(OverviewContent);
const ExpressionPanel=memo(Expression),QtlPanel=memo(Qtl),InteractionPanel=memo(Interactions),DiseasePanel=memo(Diseases),AlphaGenomePanel=memo(AlphaGenomeExpression);
const DesignSystemPreview=lazy(()=>import('./components/DesignSystemPreview'));
const SequenceViewer=lazy(()=>import('./components/SequenceViewer'));
const StructureViewer=lazy(()=>import('./components/StructureViewer'));
const sections=[{id:'overview',label:'Overview',icon:Fingerprint,color:'blue'},{id:'sequence',label:'Sequence',icon:Dna,color:'purple'},{id:'structure',label:'Structure',icon:Atom,color:'teal'},{id:'variants',label:'Variants',icon:Dna,color:'purple'},{id:'expression',label:'Expression',icon:Activity,color:'green'},{id:'qtl',label:'QTL',icon:SlidersHorizontal,color:'amber'},{id:'alphagenome',label:'AlphaGenome',icon:Dna,color:'blue'},{id:'interactions',label:'Interactions',icon:Network,color:'teal'},{id:'diseases',label:'Diseases',icon:HeartPulse,color:'rose'}];
function Header(){const isHome=useLocation().pathname==='/';const navigate=useNavigate();const [text,setText]=useState('');function submit(event:FormEvent){event.preventDefault();if(text.trim())navigate(`/search?query=${encodeURIComponent(text.trim())}`);}return <header className={`site-header ${isHome?'home-header':''}`}><Link to="/" className="brand" aria-label="memVar home"><span className="brand-logo"><img src={brandLogo} alt="memVar" width="2172" height="724"/></span></Link>{isHome?<nav className="home-header-nav" aria-label="Main navigation"><Link to="/search">Explore proteins</Link><Link to="/results">Data overview</Link><Link to="/documentation">Documentation</Link></nav>:<><span className="header-description">Human membrane protein variants</span><form className="header-search" onSubmit={submit}><Search size={17}/><input aria-label="Find a protein" placeholder="Gene, protein or UniProt ID" value={text} onChange={e=>setText(e.target.value)}/><button type="submit" aria-label="Search proteins"><ArrowRight size={16}/></button></form><nav className="database-nav" aria-label="Main navigation"><Link to="/results">Data overview</Link><Link to="/documentation"><BookOpen size={16}/>Documentation</Link></nav></>}</header>;}
function SectionNav(){
 const [active,setActive]=useState('overview');
 useEffect(()=>{
  let frame=0;
  const update=()=>{
   frame=0;
   // Read below the sticky navigation and the existing anchor scroll offset.
   const readingLine=Math.max((document.querySelector('.section-nav')?.getBoundingClientRect().bottom??0)+24,window.innerHeight*.2);
   let current='overview';
   for(const section of sections){const element=document.getElementById(section.id);if(element&&element.getBoundingClientRect().top<=readingLine)current=section.id;}
   setActive(current);
  };
  const schedule=()=>{if(!frame)frame=requestAnimationFrame(update);};
  // Measure the nine section boundaries, not only changed intersection entries.
  // Also follows lazy content and restored scroll positions after dialogs.
  const sizes=new ResizeObserver(schedule),observed=new Set<Element>();
  const attach=()=>{for(const section of sections){const element=document.getElementById(section.id);if(element&&!observed.has(element)){sizes.observe(element);observed.add(element);}}schedule();};
  const report=document.querySelector('.report');
  const changes=new MutationObserver(attach);if(report)changes.observe(report,{childList:true});
  window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);attach();
  return()=>{window.removeEventListener('scroll',schedule);window.removeEventListener('resize',schedule);sizes.disconnect();changes.disconnect();cancelAnimationFrame(frame);};
 },[]);
 return <nav className="section-nav" aria-label="Protein sections">{sections.map(({id,label,icon:Icon,color})=><a key={id} href={`#${id}`} onClick={()=>setActive(id)} className={`${active===id?'active':''} nav-${color}`} aria-current={active===id?'location':undefined}><Icon size={15}/>{label}</a>)}</nav>;
}
function ProteinContent({accession}:{accession:string}){const [expressionContext,setExpressionContext]=useState('');const [selectedPosition,setSelectedPosition]=useState<number|null>(null);const query=useQuery({queryKey:['overview',accession],queryFn:({signal})=>api<OverviewData>(`/proteins/${encodeURIComponent(accession)}/overview`,signal)});useEffect(()=>{window.scrollTo(0,0);},[accession]);return <><main className="report"><Status loading={query.isPending} error={query.error}>{query.data&&<><SectionNav/><Overview data={query.data}/><Suspense fallback={<Status loading/>}><SequenceViewer accession={accession} selectedPosition={selectedPosition} onSelectPosition={setSelectedPosition}/></Suspense><Suspense fallback={<Status loading/>}><StructureViewer accession={accession} selectedPosition={selectedPosition} onSelectPosition={setSelectedPosition}/></Suspense><Variants accession={accession} selectedPosition={selectedPosition} onClearSelectedPosition={()=>setSelectedPosition(null)}/><ExpressionPanel accession={accession} onContextChange={setExpressionContext}/><QtlPanel accession={accession}/><AlphaGenomePanel accession={accession} expressionContext={expressionContext}/><InteractionPanel accession={accession}/><DiseasePanel accession={accession}/></>}</Status></main></>;}
function ProteinPage(){const accession=(useParams().accession??'').toUpperCase();return <ProteinContent accession={accession} key={accession}/>;}
export default function App(){return <><Header/><Routes><Route path="/" element={<HomePage/>}/><Route path="/protein/:accession" element={<ProteinPage/>}/><Route path="/design-system" element={<Suspense fallback={<Status loading/>}><DesignSystemPreview/></Suspense>}/><Route path="/search" element={<SearchPage/>}/><Route path="/results" element={<ResultsPage/>}/><Route path="/documentation" element={<DocumentationPage/>}/><Route path="/about" element={<DocumentationPage/>}/><Route path="*" element={<main className="search-page"><h1>Page not found</h1><Link to="/">Return to memVar</Link></main>}/></Routes><footer className="site-footer"><span className="footer-brand">mem<strong>Var</strong></span><span>Human membrane proteins · source-linked molecular evidence</span><Link to="/results">Data overview</Link><Link to="/documentation">Documentation</Link></footer></>;}
