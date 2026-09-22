import { useEffect, useMemo, useState, type PointerEvent } from 'react';
import type { Score } from './sequence-model';
import './conservation-plot.css';

export default function ConservationPlot({scores,sequence,range,onSelect,compact=false}:{scores:Score[];sequence:string;range:[number,number];onSelect:(position:number)=>void;compact?:boolean}) {
 const [position,setPosition]=useState<number|null>(null);
 const byPosition=useMemo(()=>new Map(scores.map(score=>[score.position,score])),[scores]);
 const span=Math.max(1,range[1]-range[0]+1);
 const points=useMemo(()=>scores.filter(score=>score.position>=range[0]&&score.position<=range[1]&&score.value!=null&&Number.isFinite(score.value)),[scores,range[0],range[1]]);
 const x=(p:number)=>(p-range[0]+.5)/span*1000;
 const y=(v:number)=>94-Math.max(0,Math.min(1,v))*80;
 const path=points.map((score,i)=>`${i===0||points[i-1].position!==score.position-1?'M':'L'}${x(score.position)},${y(score.value!)}`).join(' ');
 const score=position==null?undefined:byPosition.get(position);
 const value=score?.value!=null&&Number.isFinite(score.value)?score.value:null;
 const readout=position==null?'Hover to read a residue score':`${sequence[position-1]??''}${position} · ${value==null?'JSD unavailable':`JSD ${value.toFixed(6)}`}`;
 const previous=position==null?null:byPosition.get(position-1)?.value;
 const difference=value!=null&&previous!=null&&Number.isFinite(previous)?value-previous:null;
 useEffect(()=>setPosition(null),[range[0],range[1],sequence]);
 const positionAt=(event:PointerEvent<SVGSVGElement>)=>{const bounds=event.currentTarget.getBoundingClientRect();return Math.max(range[0],Math.min(range[1],range[0]+Math.floor((event.clientX-bounds.left)/bounds.width*span)));};
 return <div className={`jsd-panel ${compact?'jsd-compact':''}`}>
  {!compact&&<div className="jsd-heading"><strong>Sequence conservation</strong><span>JSD · original 0–1 scale</span><span className="jsd-direction">0 lower <i/> higher 1</span></div>}
  <div className="jsd-plot-wrap" tabIndex={0} role="slider" aria-label="Explore JSD conservation by residue" aria-valuemin={range[0]} aria-valuemax={range[1]} aria-valuenow={position??range[0]} aria-valuetext={readout} onFocus={()=>setPosition(p=>p??range[0])} onKeyDown={event=>{const current=position??range[0];const next=event.key==='ArrowRight'?Math.min(range[1],current+1):event.key==='ArrowLeft'?Math.max(range[0],current-1):event.key==='Home'?range[0]:event.key==='End'?range[1]:null;if(next!=null){event.preventDefault();setPosition(next);}else if(event.key==='Enter'||event.key===' '){event.preventDefault();onSelect(current);}}}>
   <svg className="conservation-plot" viewBox="0 0 1000 108" preserveAspectRatio="none" aria-label="JSD profile with a 0.5 reference line" onPointerMove={event=>setPosition(positionAt(event))} onPointerDown={event=>{const p=positionAt(event);setPosition(p);onSelect(p);}}>
    {[1,.5,0].map(tick=><g key={tick}><line x1="0" x2="1000" y1={y(tick)} y2={y(tick)} stroke={tick===.5?'#a78bfa':'#dce3ef'} strokeDasharray={tick===.5?'5 4':undefined} vectorEffect="non-scaling-stroke"/></g>)}
    {points.length>0&&<path d={path} fill="none" stroke="#7135dd" strokeWidth="1.7" vectorEffect="non-scaling-stroke"/>}
    {points.filter((point,i)=>(i===0||points[i-1].position!==point.position-1)&&(i===points.length-1||points[i+1].position!==point.position+1)).map(point=><ellipse key={point.position} cx={x(point.position)} cy={y(point.value!)} rx="3.8" ry="3" fill="#7135dd"/>)}
    {position!=null&&<g className="jsd-crosshair"><line x1={x(position)} x2={x(position)} y1="7" y2="99" stroke="#312e81" strokeDasharray="3 3" vectorEffect="non-scaling-stroke"/>{value!=null&&<><line x1="0" x2="1000" y1={y(value)} y2={y(value)} stroke="#7c3aed" strokeOpacity=".35" vectorEffect="non-scaling-stroke"/><ellipse cx={x(position)} cy={y(value)} rx="3.8" ry="4" fill="#6d28d9" stroke="white" strokeWidth="1.7" vectorEffect="non-scaling-stroke"/></>}</g>}

   </svg>
   <div className="jsd-axis-labels" aria-hidden="true">{[1,.5,0].map(tick=><span key={tick} style={{top:`${y(tick)/108*100}%`}}>{tick}</span>)}</div>
   {position!=null&&<div className="jsd-tooltip" style={{left:`clamp(140px, ${x(position)/10}%, calc(100% - 140px))`}}><strong>{readout}</strong>{difference!=null&&<span>{difference>0?'↑':difference<0?'↓':'→'} {Math.abs(difference).toFixed(4)} vs previous residue</span>}{score?.status&&<span>Source support: {score.status.replaceAll('_',' ')}</span>}{value==null&&!score?.status&&<span>No score at this position</span>}</div>}
  </div>
  <div className="jsd-readout" aria-live="polite"><span>{readout}</span>{position!=null&&<button className="text-button" onClick={()=>onSelect(position)}>Select residue {position}</button>}{!compact&&<small>0.5 = reference, not a threshold · ← / → inspect</small>}</div>
 </div>;
}
