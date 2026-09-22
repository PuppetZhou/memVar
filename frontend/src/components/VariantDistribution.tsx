import { useMemo, useRef, useState } from 'react';
import { RotateCcw } from 'lucide-react';
import { Button } from './ui/button';
import { SelectionFeedback } from '@/lib/motion';
import './distribution-v2.css';

export type ClinicalCounts = Partial<Record<'pathogenic'|'uncertain'|'benign'|'conflicting'|'other'|'unclassified',number>>;
export type DistributionSite = {position:number;variant_count?:number;count?:number;clinical_counts?:ClinicalCounts};
const categories = [
 {key:'pathogenic',label:'Pathogenic / likely pathogenic',color:'#ef4444'},
 {key:'uncertain',label:'VUS',color:'#f59e0b'},
 {key:'benign',label:'Benign / likely benign',color:'#10b981'},
 {key:'conflicting',label:'Conflicting labels',color:'#a855f7'},
 {key:'other',label:'Other labels',color:'#38bdf8'},
 {key:'unclassified',label:'Unclassified',color:'#cbd5e1'},
] as const;
export function VariantDistribution({sites,length,onRange,onClear,selected}:{sites:DistributionSite[];length:number;onRange:(range:[number,number])=>void;onClear?:()=>void;selected?:[number,number]|null}) {
 const [size,setSize]=useState(0);const [hover,setHover]=useState<number|null>(null);
 const plotRef=useRef<HTMLDivElement>(null);
 function clearRange(){if(!onClear)return;onClear();setHover(null);requestAnimationFrame(()=>plotRef.current?.focus({preventScroll:true}));}
 const width=size||Math.max(1,Math.ceil(length/50));
 const bins=useMemo(()=>{const result=Array.from({length:Math.ceil(length/width)},(_,i)=>({start:i*width+1,end:Math.min(length,(i+1)*width),count:0,counts:{} as ClinicalCounts}));for(const site of sites){if(site.position<1||site.position>length)continue;const bin=result[Math.floor((site.position-1)/width)];bin.count+=site.variant_count??site.count??0;for(const c of categories)bin.counts[c.key]=(bin.counts[c.key]??0)+(site.clinical_counts?.[c.key]??(c.key==='unclassified'&&!site.clinical_counts?(site.variant_count??site.count??0):0));}return result;},[sites,length,width]);
 const max=Math.max(1,...bins.map(b=>b.count));const preview=hover==null?null:bins[hover];
 return <div className="variant-distribution"><div className="distribution-toolbar"><span>ClinVar labels · verified canonical positions</span><label>Bin size <select aria-label="Variant distribution bin size" value={size} onChange={e=>{setSize(Number(e.target.value));setHover(null);}}><option value={0}>Auto · {Math.max(1,Math.ceil(length/50))} aa</option>{[10,20,50,100].map(n=><option value={n} key={n}>{n} aa</option>)}</select></label></div>
  <SelectionFeedback visible={!!selected} className="distribution-selection" aria-label="Selected variant distribution range"><div><strong>Catalog filter: residues {selected?.[0]}–{selected?.[1]}</strong><span>{selected?selected[1]-selected[0]+1:0} aa · Other filters retained on clear.</span></div>{onClear&&<Button variant="outline" size="sm" onClick={clearRange}><RotateCcw size={15}/>Clear range filter</Button>}</SelectionFeedback>
  <div className="distribution-legend" aria-label="ClinVar classification color legend">{categories.map(c=><span key={c.key}><i style={{background:c.color}}/>{c.label}</span>)}</div>
  <div className="distribution-bars" ref={plotRef} tabIndex={-1} role="group" aria-label="Binned variant distribution by original ClinVar labels">{bins.map((b,i)=><button key={b.start} type="button" className={selected&&b.start<=selected[1]&&b.end>=selected[0]?'selected':''} aria-pressed={!!selected&&b.start<=selected[1]&&b.end>=selected[0]} aria-label={`Residues ${b.start}–${b.end}: ${b.count} variant-position links; ${categories.map(c=>`${c.label} ${b.counts[c.key]??0}`).join(', ')}`} onMouseEnter={()=>setHover(i)} onMouseLeave={()=>setHover(null)} onFocus={()=>setHover(i)} onBlur={()=>setHover(null)} onKeyDown={event=>{if(event.key==='Escape'&&selected&&onClear){event.preventDefault();clearRange();}}} onClick={()=>onRange([b.start,b.end])}><span className="distribution-stack" style={{height:`${b.count?Math.max(2,b.count/max*100):1}%`}}>{categories.map(c=>!!b.counts[c.key]&&<i key={c.key} style={{background:c.color,flex:b.counts[c.key]}}/>)}</span></button>)}</div>
  <div className="distribution-axis"><span>1</span><span>{Math.round(length/4)}</span><span>{Math.round(length/2)}</span><span>{Math.round(length*3/4)}</span><span>{length.toLocaleString()} aa</span></div>
  <div className="distribution-preview" aria-live="polite">{preview?<><strong>Residues {preview.start}–{preview.end}</strong>{categories.filter(c=>preview.counts[c.key]).map(c=><span key={c.key}><i style={{background:c.color}}/>{c.label}: <b>{preview.counts[c.key]}</b></span>)}</>:<span>Hover a bin for its composition; click to select the residue range.</span>}</div>
  <p className="distribution-note">Counts are variant–position links. Original ClinVar labels are grouped for display; disagreeing label groups are shown separately. Prediction scores do not determine these colours.</p>
 </div>;
}
