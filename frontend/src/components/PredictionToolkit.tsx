import { useState } from 'react';
import { Check, Search } from 'lucide-react';
import { number } from '../api';
import { Modal, LinkOut, Disclosure } from './ui';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { ModeToggleGroup } from './ui/mode-toggle-group';
import { ContentTransition } from '@/lib/motion';
import { HelpButton } from './HelpGuide';
import { type Predictor } from './variant-evidence-model';
import { PREDICTOR_GUIDES, predictorProject } from './predictor-guides';
import './prediction-toolkit.css';

export const DEFAULT_PREDICTORS=['AlphaMissense_score','SIFT_score','REVEL_score','CADD_phred'];
export function PredictorPicker({options,selected,onChange,onClose,initialGroup,initialSearch}:{options:Predictor[];selected:string[];onChange:(fields:string[])=>void;onClose:()=>void;initialGroup:string;initialSearch:string}){
 const [search,setSearch]=useState(initialSearch),[group,setGroup]=useState(initialGroup),[draft,setDraft]=useState(selected),[onlySelected,setOnlySelected]=useState(false),[closing,setClosing]=useState(false);
 const groups=[...new Set(options.map(p=>p.group||'Other predictions'))];
 const shown=options.filter(p=>(!group||(p.group||'Other predictions')===group)&&(!onlySelected||draft.includes(p.field))&&`${p.tool} ${p.field} ${PREDICTOR_GUIDES[p.field]?.meaning??''}`.toLowerCase().includes(search.toLowerCase()));
 const toggle=(field:string)=>setDraft(current=>current.includes(field)?current.filter(f=>f!==field):[...current,field]);
 return <Modal title="Prediction Toolkit" onClose={onClose} closeRequested={closing}><div className="pt-picker"><div className="pt-picker-intro"><p>Choose which predictor columns to display.</p><HelpButton title="Prediction criteria" label="How to read"><p>Criteria below describe source conventions and published recommendations. They do not recalculate the categories shown for a variant. Only matched source calls provide category labels; scores without calls remain scores.</p><p>Tools share training data and inputs. This view does not infer agreement, assign weights or produce a combined clinical classification.</p></HelpButton></div>
  <div className="pt-picker-controls"><label className="vc-text-input"><Search size={16}/><input aria-label="Find predictor" placeholder="Find a tool, field or purpose" value={search} onChange={e=>setSearch(e.target.value)}/></label><strong aria-live="polite">{draft.length} selected</strong><Button variant="outline" size="sm" onClick={()=>setDraft(DEFAULT_PREDICTORS.filter(f=>options.some(p=>p.field===f)))}>Default</Button><Button variant="outline" size="sm" onClick={()=>setDraft([])}>Clear all</Button></div>
  <ModeToggleGroup className="vc-picker-group-tabs" aria-label="Prediction method groups" value={group||'all'} onValueChange={value=>setGroup(value==='all'?'':value)} options={[{value:'all',label:'All groups'},...groups.map(name=>({value:name,label:name}))]}/>
  <div className="pt-bulk"><label><Checkbox checked={onlySelected} onCheckedChange={checked=>setOnlySelected(checked===true)}/>Selected only</label><span>{shown.length} fields shown</span><Button variant="ghost" size="sm" disabled={!shown.length} onClick={()=>setDraft(current=>[...new Set([...current,...shown.map(p=>p.field)])])}>Select shown</Button><Button variant="ghost" size="sm" disabled={!shown.length} onClick={()=>setDraft(current=>current.filter(f=>!shown.some(p=>p.field===f)))}>Clear shown</Button></div>
  <ContentTransition transitionKey={`${group}:${onlySelected}`}><div className="pt-tool-grid">{shown.map(p=>{const guide=PREDICTOR_GUIDES[p.field];const project=predictorProject(p.field);return <article key={p.field} className={draft.includes(p.field)?'is-selected':''}><label className="pt-tool-select"><Checkbox checked={draft.includes(p.field)} onCheckedChange={()=>toggle(p.field)}/><strong>{guide?.name??p.tool}</strong>{!group&&<span>{p.group}</span>}</label><p>{guide?.meaning??'See the source field definition.'}</p><dl className="pt-tool-meta"><div><dt>Score range</dt><dd>{guide?.scale??'Original score'}</dd></div><div><dt>Reading the score</dt><dd>{guide?.direction??'Read on the original source scale'}</dd></div><div><dt>Annotation scope</dt><dd>{p.scope==='transcript_consequence'?'Transcript-specific':'Variant-level'}</dd></div></dl>{project&&<div className="pt-project-link"><LinkOut href={project.url}>{project.label}</LinkOut></div>}<Disclosure title="Criteria & source"><code>{p.field}</code>{typeof p.covered_variants==='number'&&<p>{number(p.covered_variants,0)} variants scored in this catalog.</p>}{guide?<><dl><div><dt>Direction</dt><dd>{guide.direction}</dd></div><div><dt>Interpretation</dt><dd>{guide.criterion}</dd></div></dl><span className="pt-guide-source">{guide.source}</span><LinkOut href={guide.url}>Method / definitions</LinkOut></>:<p>Interpretation has not been reviewed for this field. No threshold is assumed.</p>}</Disclosure></article>;})}</div></ContentTransition>
  {!shown.length&&<p className="empty-state">No fields match these choices.</p>}
  <div className="pt-picker-footer"><span>{draft.length} predictor columns</span><Button size="sm" disabled={closing} onClick={()=>{onChange(draft);setClosing(true);}}><Check size={15}/>Apply selection</Button></div>
 </div></Modal>;
}
