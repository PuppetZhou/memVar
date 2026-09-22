import { useId, useState, type CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, Database, Dna, Fingerprint, HeartPulse, Layers, Network, SlidersHorizontal, MapPin, Globe2, ShieldCheck, FlaskConical, ScanLine, GitBranch, Microscope, ListFilter, BookOpen } from 'lucide-react';
import { api } from '../api';
import { Status } from './ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ContentTransition } from '@/lib/motion';
import { motion } from 'motion/react';
import { useReducedMotion } from '@/lib/use-reduced-motion';
import { HelpButton } from './HelpGuide';
import './home-evidence.css';

interface Metric {key:string;label:string;value:number|null;unit:string;basis:string}
interface Breakdown {key:string;title:string;unit:string;rows:{label:string;value:number}[];note?:string}
interface Section {id:string;metrics:Metric[];breakdowns:Breakdown[];notes:string[]}
interface Statistics {sections:Section[]}
type Feature={title:string;detail:string;icon:typeof Dna};
interface Layer {id:string;title:string;short:string;icon:typeof Dna;color:string;section:string;metric?:string;unit:string;description:string;anchor:string;features:Feature[];secondary?:{metric:string;label:string};note?:string}
const layers:Layer[]=[
 {id:'proteins',title:'Know your protein',short:'Proteins',icon:Fingerprint,color:'#2563eb',section:'proteins',metric:'proteins',unit:'protein entries',description:'Explore sequence, membrane location and structural context.',anchor:'sequence',secondary:{metric:'sequences',label:'available sequences'},features:[{title:'Sequence',detail:'Residues & annotations',icon:Dna},{title:'Membrane',detail:'Location & topology',icon:MapPin},{title:'Structure',detail:'Interactive 3D views',icon:ScanLine}]},
 {id:'variants',title:'Understand genetic variation',short:'Variants',icon:Dna,color:'#8054d9',section:'variants',metric:'variants',unit:'GRCh38 variants',description:'Move from a genomic change to its molecular and clinical evidence.',anchor:'variants',features:[{title:'Consequence',detail:'Transcript & protein changes',icon:GitBranch},{title:'Frequency',detail:'Population context',icon:Globe2},{title:'Clinical evidence',detail:'Source classifications',icon:ShieldCheck}]},
 {id:'predictors',title:'Compare prediction scores',short:'Predictions',icon:Activity,color:'#ce4d8d',section:'predictors',metric:'tools',unit:'tools / configurations',description:'Choose relevant scores and inspect each method’s interpretation.',anchor:'variants',secondary:{metric:'fields',label:'selectable score fields'},features:[{title:'Sequence models',detail:'Learned sequence features',icon:Dna},{title:'Variant effects',detail:'Method-specific scores',icon:Activity},{title:'Conservation',detail:'Evolutionary context',icon:GitBranch}]},
 {id:'expression',title:'Find the biological context',short:'Expression',icon:Layers,color:'#099b8b',section:'context',unit:'listed datasets',description:'Browse RNA and protein measurements across tissues and cells.',anchor:'expression',note:'Counts the 13 expression datasets listed in Data overview. GTEx median-expression vectors are available separately and are excluded from this dataset count.',features:[{title:'Tissues',detail:'Normal & cancer samples',icon:MapPin},{title:'Cells',detail:'Cell lines, types & clusters',icon:Microscope},{title:'Measurements',detail:'RNA, proteomics & staining',icon:FlaskConical}]},
 {id:'regulation',title:'Explore genetic regulation',short:'Regulation',icon:SlidersHorizontal,color:'#cf8828',section:'context',metric:'qtl',unit:'QTL association rows',description:'Inspect variant–gene associations in their study and tissue context.',anchor:'qtl',features:[{title:'Associations',detail:'Variant–gene links',icon:GitBranch},{title:'Tissues',detail:'Context-specific records',icon:MapPin},{title:'Statistics',detail:'Original effects & significance',icon:Activity}]},
 {id:'interactions',title:'Discover molecular partners',short:'Interactions',icon:Network,color:'#168fb4',section:'context',metric:'ppi',unit:'stored PPI records',description:'Explore protein partners and reported mutation effects on interactions.',anchor:'interactions',note:'Counts stored interaction and mutation-feature record IDs, not unique protein pairs. Predicted interfaces are separate and excluded from this count.',features:[{title:'Partners',detail:'Protein interaction evidence',icon:Network},{title:'Contexts',detail:'Disease & study collections',icon:ListFilter},{title:'Mutation effects',detail:'Reported interaction changes',icon:Dna}]},
 {id:'diseases',title:'Connect disease evidence',short:'Diseases',icon:HeartPulse,color:'#e15468',section:'diseases',metric:'evidence',unit:'disease evidence records',description:'Review disease relationships and phenotype annotations with source evidence.',anchor:'diseases',secondary:{metric:'phenotypes',label:'phenotype annotations'},features:[{title:'Relationships',detail:'Gene–disease evidence',icon:HeartPulse},{title:'Phenotypes',detail:'Reported clinical features',icon:Fingerprint},{title:'Provenance',detail:'Assertions & source records',icon:BookOpen}]},
];
const compact=(value:number|null)=>value===null?'—':new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1}).format(value);
const exact=(value:number|null)=>value===null?'Not available':value.toLocaleString('en-US');
function primary(layer:Layer,section?:Section):number|null{
 if(layer.id==='expression')return section?.breakdowns.find(b=>b.key==='expression')?.rows.length??null;
 return section?.metrics.find(m=>m.key===layer.metric)?.value??null;
}
function LayerPreview({layer,section}:{layer:Layer;section:Section}){
 const value=primary(layer,section);const secondary=section.metrics.find(m=>m.key===layer.secondary?.metric);const primaryMetric=section.metrics.find(m=>m.key===layer.metric);
 return <div className="home-layer-preview" style={{'--layer':layer.color} as CSSProperties}>
  <div className="home-layer-intro"><h3>{layer.title}</h3><p>{layer.description}</p>{secondary&&<span className="home-layer-secondary"><strong>{compact(secondary.value)}</strong> {layer.secondary?.label}</span>}<div className="home-layer-actions"><Link className="home-layer-example" to={`/protein/P00533#${layer.anchor}`}>Explore EGFR <ArrowRight size={15}/></Link><HelpButton title={`${layer.short} · counting scope`} label="About this count"><p><strong>{exact(value)}</strong> {layer.unit}.</p>{primaryMetric&&<p>{primaryMetric.basis}</p>}{layer.note&&<p>{layer.note}</p>}<p>Counts use different units across layers and are not additive. Available evidence varies by protein.</p><Link to={`/results#${layer.section}`}>Full statistics and counting notes</Link></HelpButton></div></div>
  <div className="home-layer-features" aria-label={`${layer.short}: what you can explore`}>{layer.features.map(({title,detail,icon:Icon},i)=><div className={`home-layer-feature home-feature-${i}`} key={title}><span><Icon size={26} strokeWidth={1.7}/></span><h4>{title}</h4><p>{detail}</p></div>)}</div>
 </div>;
}
export default function HomeEvidence(){
 const indicatorId=useId();const reduce=useReducedMotion();
 const query=useQuery({queryKey:['catalog-statistics'],queryFn:({signal})=>api<Statistics>('/catalog/statistics',signal),staleTime:300000});const [active,setActive]=useState('variants');const layer=layers.find(item=>item.id===active)!;const section=query.data?.sections.find(item=>item.id===layer.section);
 return <section id="data-layers" className="home-evidence-section"><div className="home-container"><header className="home-evidence-heading"><div><span className="home-eyebrow"><Database size={14}/> SEVEN LAYERS OF EVIDENCE</span><h2>Discover what’s in memVar</h2><p>Choose a layer to see what you can explore.</p></div><Link to="/results">Complete data overview <ArrowRight size={16}/></Link></header><Status loading={query.isPending} error={query.error}>{query.data&&<Tabs value={active} onValueChange={setActive} className="home-evidence-explorer"><TabsList className="home-layer-list" aria-label="Explore data layers">{layers.map(item=>{const Icon=item.icon;const value=primary(item,query.data.sections.find(s=>s.id===item.section));return <TabsTrigger key={item.id} value={item.id} aria-label={`${item.short}: ${exact(value)} ${item.unit}`} style={{'--layer':item.color} as CSSProperties}>{item.id===active&&<motion.span className="home-layer-indicator" layoutId={indicatorId} transition={{duration:reduce?0:.18,ease:[.22,1,.36,1]}}/>}<span className="home-layer-tab-title"><Icon size={19}/><span>{item.short}</span></span><strong title={`${exact(value)} ${item.unit}`}>{compact(value)}</strong><small>{item.unit}</small></TabsTrigger>;})}</TabsList><TabsContent value={active} className="home-layer-content"><ContentTransition transitionKey={active}>{section?<LayerPreview layer={layer} section={section}/>:<p className="home-layer-unavailable">Coverage for this layer is unavailable.</p>}</ContentTransition></TabsContent></Tabs>}</Status></div></section>;
}
