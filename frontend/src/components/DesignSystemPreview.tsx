import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AnimatePresence, motion } from 'motion/react';
import { useReducedMotion } from '@/lib/use-reduced-motion';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Field, FieldGroup, FieldSet, FieldLegend, FieldLabel, FieldDescription } from '@/components/ui/field';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { CopyIcon, ResetIcon, PredictionIcon, PathwayIcon, StatisticsIcon, CollectionIcon, FrequencyIcon, ClinicalIcon, StructureIcon, SequenceIcon, FilterIcon, AnnotationIcon } from '@/lib/icons';
import { Reveal, uiTransition } from '@/lib/motion';
import { Modal } from './ui';

const modules = [
 {label:'Overview',tone:'blue',scale:'indigo',section:'overview',icon:AnnotationIcon},
 {label:'Sequence',tone:'purple',scale:'violet',section:'sequence',icon:SequenceIcon},
 {label:'Structure',tone:'teal',scale:'cyan',section:'structure',icon:StructureIcon},
 {label:'Expression',tone:'green',scale:'green',section:'expression',icon:StatisticsIcon},
 {label:'QTL',tone:'amber',scale:'orange',section:'qtl',icon:FilterIcon},
 {label:'Diseases',tone:'rose',scale:'pink',section:'diseases',icon:ClinicalIcon},
];
const icons = [
 {label:'Copy',icon:CopyIcon,tone:'blue'}, {label:'Reset',icon:ResetIcon,tone:'blue'}, {label:'Prediction',icon:PredictionIcon,tone:'purple'},
 {label:'Pathway',icon:PathwayIcon,tone:'teal'}, {label:'Statistics',icon:StatisticsIcon,tone:'green'}, {label:'Collection',icon:CollectionIcon,tone:'blue'},
 {label:'Frequency',icon:FrequencyIcon,tone:'amber'}, {label:'Clinical',icon:ClinicalIcon,tone:'rose'}, {label:'Structure',icon:StructureIcon,tone:'teal'},
 {label:'Sequence',icon:SequenceIcon,tone:'purple'}, {label:'Filter',icon:FilterIcon,tone:'blue'}, {label:'Annotation',icon:AnnotationIcon,tone:'blue'},
];

export default function DesignSystemPreview() {
 const [selection,setSelection]=useState(false);
 const [activeTone,setActiveTone]=useState('blue');
 const [details,setDetails]=useState(false);
 const [copyState,setCopyState]=useState('');
 const [sources,setSources]=useState(['UniProt']);
 const reduce=useReducedMotion();
 async function copy() {
  try { await navigator.clipboard.writeText('P00533'); setCopyState('Copied P00533'); }
  catch { setCopyState('Copy unavailable. Select and copy P00533 manually.'); }
 }
 return <main className="kit-page">
  <header className="kit-intro"><div className="kit-spectrum" aria-hidden="true">{modules.map(({tone})=><span key={tone} data-ui-tone={tone}/>)}</div><p className="kit-eyebrow">memVar · interface preview</p><h1>A clearer view of the evidence.</h1><p>Neutral reading surfaces, blue actions and distinct scientific colours. Explore the component states and category palettes. This is an interface sample; source selections below do not query or change scientific data.</p><Button asChild variant="outline"><Link to="/protein/P00533">Open EGFR · P00533</Link></Button></header>
  <div className="kit-modules" role="group" aria-label="Preview module colours">{modules.map(({label,tone,scale,icon:Icon})=><button key={tone} type="button" className="kit-module" data-ui-tone={tone} aria-pressed={activeTone===tone} onClick={()=>setActiveTone(tone)}><Icon aria-hidden="true"/><strong>{label}</strong><span>Radix {scale}</span></button>)}</div><p className="kit-note" role="status">Selected colour: {modules.find(module=>module.tone===activeTone)?.label}. Choose another module to compare its selected state.</p>
  <div className="kit-grid">
   <Card className="kit-card" data-ui-tone="blue"><CardHeader><CardTitle><AnnotationIcon aria-hidden="true"/>Evidence controls</CardTitle><CardDescription>Explicit actions, readable labels and reversible selection.</CardDescription></CardHeader>
    <CardContent className="flex flex-col gap-5"><div className="kit-actions"><Button onClick={()=>setDetails(true)}><AnnotationIcon data-icon="inline-start"/>Open evidence</Button><Tooltip><TooltipTrigger asChild><Button variant="outline" onClick={copy}><CopyIcon data-icon="inline-start"/>Copy ID</Button></TooltipTrigger><TooltipContent>Copy the UniProt accession</TooltipContent></Tooltip><Button variant="ghost" disabled={!selection} onClick={()=>setSelection(false)}><ResetIcon data-icon="inline-start"/>Clear selection</Button></div>
     <span role="status" className="kit-note">{copyState||'UniProt accession: P00533'}</span>
     <FieldSet><FieldLegend>Visible source layers · sample</FieldLegend><FieldDescription>Multiple sources remain independently selectable.</FieldDescription><FieldGroup>{['UniProt','OPM'].map(source=><Field key={source} orientation="horizontal"><Checkbox id={`preview-${source}`} checked={sources.includes(source)} onCheckedChange={checked=>setSources(previous=>checked?[...previous.filter(s=>s!==source),source]:previous.filter(s=>s!==source))}/><FieldLabel htmlFor={`preview-${source}`}>{source}</FieldLabel></Field>)}</FieldGroup></FieldSet>
     <p className="kit-note" role="status">Visible: {sources.join(' · ')||'No layers selected'}</p>
    </CardContent><CardFooter><Button variant="secondary" onClick={()=>setSelection(true)} disabled={selection}><SequenceIcon data-icon="inline-start"/>Select example region</Button></CardFooter></Card>
   <Card className="kit-card" data-ui-tone="purple"><CardHeader><CardTitle><SequenceIcon aria-hidden="true"/>Selection feedback</CardTitle><CardDescription>The panel enters and leaves with one short transition.</CardDescription></CardHeader><CardContent className="flex flex-col gap-4"><AnimatePresence initial={false} mode="wait">{selection?<motion.div key="selected" className="kit-selection" initial={reduce?false:{opacity:0,y:6}} animate={{opacity:1,y:0}} exit={{opacity:0,y:reduce?0:4}} transition={reduce?{duration:0}:uiTransition}><SequenceIcon aria-hidden="true"/><div><strong>Example region selected</strong><div>Use “Clear selection” to return.</div></div></motion.div>:<motion.p key="empty" className="kit-note" initial={false} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:reduce?0:0.1}}>Select an example region to preview the feedback.</motion.p>}</AnimatePresence><p className="kit-note">Reduced-motion preferences are respected. Data remain immediately accessible.</p></CardContent><CardFooter><Button variant="outline" disabled={!selection} onClick={()=>setSelection(false)}><ResetIcon data-icon="inline-start"/>Clear selection</Button></CardFooter></Card>
   <Card className="kit-card" data-ui-tone="teal"><CardHeader><CardTitle><CollectionIcon aria-hidden="true"/>Selected icon vocabulary</CardTitle><CardDescription>Lucide for actions; your Tabler choices for sequence, filters and annotation.</CardDescription></CardHeader><CardContent><div className="kit-icons">{icons.map(({label,icon:Icon,tone})=><div className="kit-icon" data-ui-tone={tone} key={label}><Icon aria-hidden="true"/><span>{label}</span></div>)}</div></CardContent><CardFooter><span className="kit-note">Colour and shape support the text label; they do not replace it.</span></CardFooter></Card>
   <Card className="kit-card" data-ui-tone="rose"><CardHeader><CardTitle><StatisticsIcon aria-hidden="true"/>Radix colour roles</CardTitle><CardDescription>Six module identities, one consistent scale. Slate keeps text and surfaces calm.</CardDescription></CardHeader><CardContent><div className="kit-palette">{modules.map(({label,tone,scale})=><div className="kit-palette-row" data-ui-tone={tone} key={tone}><strong>{label} · {scale}</strong><div className="kit-swatches" role="img" aria-label={`${scale}: 12 steps from light surfaces to deep text`}>{Array.from({length:12},(_,i)=><span aria-hidden="true" className="kit-swatch" key={i} style={{background:`var(--${scale}-${i+1})`}}/>)}</div><div className="kit-palette-caption"><span>01 · Surface</span><span>09 · Accent</span><span>12 · Text</span></div></div>)}</div></CardContent><CardFooter><span className="kit-note">1–2 surfaces · 3–5 states · 6–8 borders · 9–10 actions · 11–12 text. Scientific heatmaps keep their own scales.</span></CardFooter></Card>
  </div>
  {details&&<Modal title="Evidence preview · P00533" onClose={()=>setDetails(false)}><Reveal><p>This sample demonstrates the shared evidence dialog. Press Escape, use Close, or click outside to return.</p><p>Focus returns to the action that opened this panel.</p><Button variant="outline" onClick={()=>setDetails(false)}>Return to preview</Button></Reveal></Modal>}
 </main>;
}
