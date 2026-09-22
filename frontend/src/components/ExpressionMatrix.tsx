import { useId, useRef, useState, type CSSProperties } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, ChevronDown, ChevronUp } from 'lucide-react';
import { api, display, number, params, type RecordData } from '../api';
import { Status } from './ui';
import { Button } from './ui/button';
import { expressionCollectionFor } from './ContextDisplay';
import { CollapseRegion } from '../lib/motion';
import './expression-matrix.css';

interface MatrixItem extends RecordData {
  record_id:string;context:string;group:string;sample:string;measurement:string;
  value:unknown;numeric_value:number|null;unit:string;details:RecordData[];
}
interface MatrixGroup {key:string;label:string;records:number;available_values:number;missing_values:number;median:number|null;summary_kind:string;items:MatrixItem[];}
interface MatrixData {
  dataset:string;source:string;category:string;measurement:string;unit:string;groups:MatrixGroup[];
  totals:{records:number;groups:number;available_values:number;missing_values:number};
  scale:{kind:'categorical'|'linear'|'log1p'|'diverging';minimum:number|null;maximum:number|null;maximum_absolute:number|null;categories:string[]};
  project_summary:string|null;notes:string[];
}

const CATEGORY_COLOURS:Record<string,string>={high:'#1f9d70',medium:'#e3a42f',low:'#5b8bd9','not detected':'#d9dee7','n/a':'#eef1f5',ascending:'#7357c7',descending:'#c15d8d','not representative':'#9ba5b5'};
function categoryColour(raw:unknown){
  const key=String(raw??'').trim().toLowerCase();
  if(!key)return '#cbd5e1';
  if(CATEGORY_COLOURS[key])return CATEGORY_COLOURS[key];
  let hash=0;for(const char of key)hash=(hash*31+char.charCodeAt(0))>>>0;
  return `hsl(${hash%360} 42% 61%)`;
}
function sourceValue(item:MatrixItem){return item.value===null||item.value===undefined||item.value===''?'Missing source value':`${display(item.value)} ${item.unit}`;}
function plottedValue(group:MatrixGroup){return group.summary_kind==='project_median'?group.median:group.items.length===1?group.items[0].numeric_value:null;}
function barPosition(value:number,max:number,kind:MatrixData['scale']['kind']):CSSProperties{
  if(kind==='diverging'){
    const width=max?Math.min(50,Math.abs(value)/max*50):0;
    return {left:`${value<0?50-width:50}%`,width:`${width}%`,background:value<0?'#4f81cf':'#d66a83'};
  }
  const ratio=max?(kind==='log1p'?Math.log1p(Math.max(0,value))/Math.log1p(max):Math.max(0,value)/max):0;
  return {width:`${Math.min(100,ratio*100)}%`};
}
function ValueBar({value,max,kind}:{value:number|null;max:number;kind:MatrixData['scale']['kind']}){
  return <span className={`ex-bar-track${kind==='diverging'?' is-diverging':''}${value===0?' is-zero':''}${value===null?' is-missing':''}`} aria-hidden="true">{value!==null&&<span className="ex-bar-fill" style={barPosition(value,max,kind)}/>}</span>;
}
function CategoryBar({items}:{items:MatrixItem[]}){
  const counts=new Map<string,number>();
  for(const item of items){const value=String(item.value??'').trim()||'Missing';counts.set(value,(counts.get(value)??0)+1);}
  return <span className="ex-category-track" aria-label={[...counts].map(([value,count])=>`${value}: ${count}`).join(', ')}>{[...counts].map(([value,count])=><span key={value} title={`${value}: ${count} / ${items.length}`} style={{width:`${items.length?count/items.length*100:0}%`,background:value==='Missing'?'#cbd5e1':categoryColour(value)}}/>)}</span>;
}

// Keep large sample collections lazy: this component mounts only after the group opens.
function SourceValues({group,data,onSelect}:{group:MatrixGroup;data:MatrixData;onSelect:(row:RecordData)=>void}){
  const detailMax=group.items.reduce((max,item)=>Math.max(max,Math.abs(item.numeric_value??0)),0);
  return <div className="ex-source-values"><p>Original {data.source} values in {contextLabel(group.label)} · {data.unit}. Sample bars are relative within this group.</p><div>{group.items.map(item=><button type="button" key={item.record_id} onClick={()=>onSelect(item)} title={`${item.sample} · ${sourceValue(item)}`}><span>{contextLabel(item.sample)}</span>{item.numeric_value!==null?<ValueBar value={item.numeric_value} max={detailMax} kind={data.scale.kind}/>:<i style={{background:item.value===null||item.value===undefined||item.value===''?'#cbd5e1':categoryColour(item.value)}}/>}<strong>{sourceValue(item)}</strong></button>)}</div></div>;
}

const INITIAL_GROUPS=10;
// Display formatting only; source labels and lookup keys remain unchanged.
const contextLabel=(value:string)=>value.replaceAll('_',' ');

export function ExpressionMatrix({accession,dataset,onSelect}:{accession:string;dataset:string;onSelect:(row:RecordData)=>void}){
  const result=useQuery({queryKey:['expression-matrix',accession,dataset],queryFn:({signal})=>api<MatrixData>(`/proteins/${accession}/expression/matrix?${params({dataset})}`,signal)});
  const [expandedGroup,setExpandedGroup]=useState<string|null>(null);
  const [closingGroups,setClosingGroups]=useState<Set<string>>(()=>new Set());
  const [collectionOpen,setCollectionOpen]=useState(false);
  const gridId=useId();
  const gridRef=useRef<HTMLDivElement>(null);
  const collectionButtonRef=useRef<HTMLButtonElement>(null);
  const data=result.data;
  // Compute scale over every group, independently of the display window.
  const plotted=data?.groups.map(plottedValue).filter((value):value is number=>value!==null)??[];
  const maxPlotted=plotted.length?Math.max(...plotted.map(Math.abs)):0;
  const scaleDescription=data?.scale.kind==='log1p'?'Bar length: log1p, relative to the collection maximum. Values keep original units.':data?.scale.kind==='diverging'?'Bars: centered on zero, relative to the largest absolute value in the collection. Blue negative, rose positive.':data?.scale.kind==='categorical'?'Segments: proportion of original source categories.':'Bar length: linear, relative to the collection maximum. Values keep original units.';
  const visibleGroups=(collectionOpen?data?.groups:data?.groups.slice(0,INITIAL_GROUPS))??[];

  return <section className="ex-matrix" aria-label="Expression values by source context">
    <Status loading={result.isPending} error={result.error}>{data&&<>
      <header className="ex-matrix-heading"><div><span>{data.source} · source collection</span><h3><Activity size={17}/>{expressionCollectionFor(dataset).context}</h3><p>{number(data.totals.records,0)} original values across {number(data.totals.groups,0)} source-defined groups · {data.unit}</p></div><div className="ex-scale"><i className={data.scale.kind}/><span>{scaleDescription}</span></div></header>
      {data.scale.kind==='categorical'&&<div className="ex-category-legend">{data.scale.categories.map(category=><span key={category}><i style={{background:categoryColour(category)}}/>{category}</span>)}{data.totals.missing_values>0&&<span><i style={{background:'#cbd5e1'}}/>Missing</span>}</div>}
      <div className="ex-value-note">{data.project_summary?'Project group medians · n = measured values. Expand a group for original source values.':'Source-provided values · select a row for its record.'} Compare within this collection and unit.{data.totals.missing_values>0?` ${number(data.totals.missing_values,0)} missing values are marked separately, never as zero.`:''}</div>
      <div className={`ex-value-grid${collectionOpen?' is-scrollable':''}`} id={gridId} ref={gridRef} tabIndex={collectionOpen?0:undefined} role="region" aria-label={`${data.source} ${data.measurement} relative values`}>
        {visibleGroups.map(group=>{
          const value=plottedValue(group),isSingle=group.items.length===1,expanded=expandedGroup===group.key;
          const summary=group.summary_kind==='project_median'?'project median':isSingle?'source value':`${number(group.records,0)} source values`;
          return <section className={`ex-value-group${expanded||closingGroups.has(group.key)?' is-expanded':''}`} key={group.key}>
            <button type="button" className="ex-value-row" title={group.label} aria-expanded={isSingle?undefined:expanded} aria-label={`${contextLabel(group.label)}: ${value===null?summary:`${summary} ${number(value,3)} ${data.unit}`}. ${isSingle?'Open source value details':'Toggle original source values'}.`} onClick={()=>{if(isSingle){onSelect(group.items[0]);return;}if(expandedGroup)setClosingGroups(groups=>new Set(groups).add(expandedGroup));setExpandedGroup(expanded?null:group.key);}}>
              <span className="ex-row-label"><strong>{contextLabel(group.label)}</strong>{(!isSingle||group.missing_values>0)&&<small>{!isSingle?`${summary} · n=${number(group.available_values,0)}`:''}{group.missing_values?`${isSingle?'':' · '}${number(group.missing_values,0)} missing`:''}</small>}</span>
              {data.scale.kind==='categorical'?<CategoryBar items={group.items}/>:<ValueBar value={value} max={maxPlotted} kind={data.scale.kind}/>}
              <span className={`ex-row-value${value===null?' is-category':''}`}>{value===null?(isSingle?String(group.items[0]?.value??'Missing'):`${number(group.records,0)} values`):<>{group.summary_kind==='project_median'?number(value,3):display(group.items[0].value)} <small>{data.unit}</small></>}</span>
              {!isSingle&&<ChevronDown className="ex-row-chevron" size={14}/>}
            </button>
            {!isSingle&&<CollapseRegion open={expanded} onAnimationComplete={()=>{if(!expanded)setClosingGroups(groups=>{if(!groups.has(group.key))return groups;const next=new Set(groups);next.delete(group.key);return next;});}}><SourceValues group={group} data={data} onSelect={onSelect}/></CollapseRegion>}
          </section>;
        })}
      </div>
      <div className="ex-matrix-pagination"><p role="status">{collectionOpen?<><strong>{number(data.groups.length,0)}</strong> groups · scroll to browse</>:<>Previewing <strong>{number(visibleGroups.length,0)}</strong> of <strong>{number(data.groups.length,0)}</strong> groups</>}<span> · scale uses the full collection</span></p>
       {data.groups.length>INITIAL_GROUPS&&<Button ref={collectionButtonRef} type="button" variant="outline" size="sm" aria-controls={gridId} aria-expanded={collectionOpen} onClick={()=>{
         if(collectionOpen){
           if(gridRef.current)gridRef.current.scrollTop=0;
           setCollectionOpen(false);setExpandedGroup(null);setClosingGroups(new Set());
           requestAnimationFrame(()=>{collectionButtonRef.current?.focus({preventScroll:true});collectionButtonRef.current?.scrollIntoView({block:'nearest',behavior:'instant'});});
         }else{setCollectionOpen(true);requestAnimationFrame(()=>gridRef.current?.focus({preventScroll:true}));}
       }}>{collectionOpen?<><ChevronUp size={14}/>Collapse collection</>:<><ChevronDown size={14}/>Expand collection · {number(data.groups.length,0)} groups</>}</Button>}
      </div>
    </>}</Status>
  </section>;
}
