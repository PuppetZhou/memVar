import { useState, type CSSProperties, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ExternalLink, Search } from 'lucide-react';
import './data-overview-charts.css';

export interface OverviewBreakdown {key:string;title:string;unit:string;rows:{label:string;value:number;version?:string;url?:string;href?:string}[];note?:string}
type Row=OverviewBreakdown['rows'][number];
type Section={id:string;metrics:{key:string;value:number|null}[];breakdowns:OverviewBreakdown[]};
const palette=['#2563eb','#8b5cf6','#0d9488','#f59e0b','#e54c80','#0891b2'];
const n=(value:number)=>value.toLocaleString('en-US');
const percent=(value:number,total:number)=>!total?'0%':value>0&&value/total<.001?'<0.1%':`${(value/total*100).toFixed(1)}%`;
const colorStyle=(color:string)=>({'--ov-color':color} as CSSProperties);
function RowName({row}:{row:Row}){return row.href?<Link to={row.href}>{row.label}<ArrowRight size={12}/></Link>:row.url?<a href={row.url} target="_blank" rel="noreferrer">{row.label}<ExternalLink size={12}/></a>:<span>{row.label}</span>;}
function Chart({data,children,subtitle,wide=false}:{data:OverviewBreakdown;children:ReactNode;subtitle?:string;wide?:boolean}){return <article className={`db-chart ov-chart${wide?' ov-wide':''}`}><header><div><h3>{data.title}</h3>{subtitle&&<p>{subtitle}</p>}</div><span>{data.unit}</span></header>{children}{data.note&&<details className="ov-counting"><summary>Counting notes</summary><p>{data.note}</p></details>}</article>;}

// Only use this component for disjoint field sets or separately stored source records.
function Composition({data,subtitle}:{data:OverviewBreakdown;subtitle:string}){
 const [hover,setHover]=useState<number|null>(null),[pinned,setPinned]=useState<number|null>(null);const active=hover??pinned;
 const total=data.rows.reduce((sum,row)=>sum+row.value,0);let offset=0;
 return <Chart data={data} subtitle={subtitle} wide={data.key==='qtl'}><div className="ov-composition"><svg viewBox="0 0 200 200" role="img" aria-label={`${data.title}: ${n(total)} ${data.unit}`}><circle cx="100" cy="100" r="78" fill="none" stroke="#edf1f7" strokeWidth="23"/>{data.rows.map((row,i)=>{const share=total?row.value/total*100:0,start=offset;offset+=share;return <circle key={row.label} cx="100" cy="100" r="78" fill="none" stroke={palette[i%palette.length]} strokeWidth={active===i?28:23} pathLength="100" strokeDasharray={`${share} ${100-share}`} strokeDashoffset={-start} transform="rotate(-90 100 100)" opacity={active==null||active===i?1:.3} onMouseEnter={()=>setHover(i)} onMouseLeave={()=>setHover(null)} onClick={()=>setPinned(pinned===i?null:i)} style={{cursor:'pointer'}}><title>{`${row.label}: ${n(row.value)} (${percent(row.value,total)})`}</title></circle>;})}<text x="100" y="98" textAnchor="middle" className="ov-ring-number">{n(active==null?total:data.rows[active].value)}</text><text x="100" y="119" textAnchor="middle" className="ov-ring-caption">{active==null?(data.unit==='score fields'?'score fields':'source records'):percent(data.rows[active].value,total)}</text></svg><div className="ov-ring-legend">{data.rows.map((row,i)=><button key={row.label} type="button" aria-pressed={pinned===i} className={active===i?'active':''} style={colorStyle(palette[i%palette.length])} onMouseEnter={()=>setHover(i)} onMouseLeave={()=>setHover(null)} onFocus={()=>setHover(i)} onBlur={()=>setHover(null)} onClick={()=>setPinned(pinned===i?null:i)}><i/><span>{row.label}</span><strong>{n(row.value)}<small>{percent(row.value,total)}</small></strong></button>)}</div></div></Chart>;
}

function ProteinClasses({data,total}:{data:OverviewBreakdown;total:number}){return <Chart data={data} subtitle="Independent coverage · labels may overlap" wide><div className="ov-coverage-grid">{data.rows.map((row,i)=><div className="ov-coverage-card" key={row.label} style={colorStyle(palette[i%palette.length])}><div className="ov-gauge"><svg viewBox="0 0 100 100" role="img" aria-label={`${row.label}: ${percent(row.value,total)} of ${n(total)} proteins`}><circle cx="50" cy="50" r="39" fill="none" stroke="#edf1f7" strokeWidth="10"/><circle cx="50" cy="50" r="39" fill="none" stroke="var(--ov-color)" strokeWidth="10" pathLength="100" strokeDasharray={`${total?row.value/total*100:0} 100`} transform="rotate(-90 50 50)" strokeLinecap="round"/><text x="50" y="55" textAnchor="middle">{percent(row.value,total)}</text></svg></div><div><RowName row={row}/><strong>{n(row.value)}</strong><small>of {n(total)} proteins</small></div></div>)}</div></Chart>;}

function SourceFamilies({data}:{data:OverviewBreakdown}){
 const families=[{name:'Reference annotation',labels:['UniProt']},{name:'Predicted topology',labels:['DeepTMHMM2','TmAlphaFold/cctop','TmAlphaFold/tmdet']},{name:'HTP resources',labels:['HTP','HTP/experimental','HTP/3D']},{name:'Topology & structure',labels:['TOPDB','PDBTM/pdbtm','PDBTM/pdbtm_all']},{name:'Membrane associations',labels:['BioDolphin','MPLID']}];
 const known=new Set(families.flatMap(g=>g.labels));if(data.rows.some(r=>!known.has(r.label)))families.push({name:'Other resources',labels:data.rows.filter(r=>!known.has(r.label)).map(r=>r.label)});
 return <Chart data={data} subtitle="Source families · coverage is not additive" wide><div className="ov-family-grid">{families.map((family,i)=><section key={family.name} style={colorStyle(palette[i%palette.length])}><h4><i/>{family.name}</h4>{data.rows.filter(r=>family.labels.includes(r.label)).map(row=><div className="ov-family-row" key={row.label}><RowName row={row}/><strong>{n(row.value)}</strong></div>)}</section>)}</div></Chart>;
}

function Membership({data}:{data:OverviewBreakdown}){const max=Math.max(1,...data.rows.map(r=>r.value));return <Chart data={data} subtitle="Source coverage · overlapping membership"><div className="ov-columns">{data.rows.map((row,i)=><div key={row.label} style={colorStyle(palette[i%palette.length])}><strong>{n(row.value)}</strong><div className="ov-column-track"><i style={{height:`${row.value/max*100}%`}} title={`${row.label}: ${n(row.value)}`}/></div><RowName row={row}/></div>)}</div><p className="ov-axis-caption">Bar height · variant count, starting at zero</p></Chart>;}

function Consequences({data}:{data:OverviewBreakdown}){
 const groups=[{name:'Amino-acid substitution',rows:data.rows.filter(r=>/^(missense|synonymous)/.test(r.label))},{name:'Start / stop codons',rows:data.rows.filter(r=>/^(start|stop|incomplete terminal)/.test(r.label))},{name:'Splicing',rows:data.rows.filter(r=>r.label.startsWith('splice'))},{name:'Other coding annotations',rows:data.rows.filter(r=>!/^(missense|synonymous|start|stop|incomplete terminal|splice)/.test(r.label))}];
 return <Chart data={data} subtitle="Term families · a row may carry several terms"><div className="ov-term-groups">{groups.filter(g=>g.rows.length).map((group,i)=><details open={i===0} key={group.name} style={colorStyle(palette[i%palette.length])}><summary><i/>{group.name}<span>{group.rows.length} terms</span></summary><div>{group.rows.map(row=><div className="ov-term" key={row.label}><span>{row.label}</span><strong>{n(row.value)}</strong></div>)}</div></details>)}</div></Chart>;
}

function ToolkitInventory({data}:{data:OverviewBreakdown}){
 const [search,setSearch]=useState('');const groups=[{name:'Single-field outputs',rows:data.rows.filter(r=>r.value===1)},{name:'Multiple-field outputs',rows:data.rows.filter(r=>r.value!==1)}];
 return <Chart data={data} subtitle="Browse model labels · badges count score fields" wide><label className="ov-tool-search"><Search size={15}/><input aria-label="Find a prediction tool in data overview" placeholder="Find a tool…" value={search} onChange={e=>setSearch(e.target.value)}/></label><div className="ov-tool-groups">{groups.map((group,i)=><section key={group.name} style={colorStyle(palette[i])}><h4>{group.name}<span>{group.rows.length} model labels</span></h4><div>{group.rows.filter(r=>r.label.toLowerCase().includes(search.toLowerCase())).map(row=><span className="ov-tool-chip" key={row.label}>{row.label}<b title={`${row.value} score fields`}>{row.value}</b></span>)}</div></section>)}</div>{!data.rows.some(r=>r.label.toLowerCase().includes(search.toLowerCase()))&&<p>No tools match.</p>}</Chart>;
}

// Presentation groups for the already-published datasets, not new biological assignments.
const expressionGroups=[
 {name:'Tissues',datasets:['rna tissue hpa','normal ihc data','rna tissue fantom','ms tissue sample data']},
 {name:'Cancer samples',datasets:['cancer data','cancer cptac','rna cancer sample']},
 {name:'Cell lines',datasets:['rna celline','rna cell line cancer']},
 {name:'Cell types & clusters',datasets:['rna single cell type','rna single cell cluster','dvp cell type','dvp cell type group data']},
];
const expressionLabels:Record<string,[string,string]>={
 'rna tissue hpa':['HPA tissue RNA','RNA-seq'],'normal ihc data':['Normal tissue staining','IHC'],'rna tissue fantom':['FANTOM tissue RNA','CAGE'],'ms tissue sample data':['Tissue proteomics','MS'],
 'cancer data':['Cancer staining','IHC'],'cancer cptac':['CPTAC cancer proteomics','MS'],'rna cancer sample':['Cancer sample RNA','RNA-seq'],'rna celline':['Cell-line RNA','RNA-seq'],'rna cell line cancer':['Cancer cell-line RNA','RNA-seq'],
 'rna single cell type':['Single-cell types','scRNA-seq'],'rna single cell cluster':['Single-cell clusters','scRNA-seq'],'dvp cell type':['DVP cell types','MS'],'dvp cell type group data':['DVP cell-type groups','MS'],
};
function ExpressionInventory({data}:{data:OverviewBreakdown}){
 const [selected,setSelected]=useState(0);const known=new Set(expressionGroups.flatMap(g=>g.datasets));const unknown=data.rows.filter(r=>!known.has(r.label));const groups=unknown.length?[...expressionGroups,{name:'Other datasets',datasets:unknown.map(r=>r.label)}]:expressionGroups;
 const rows=data.rows.filter(r=>groups[selected].datasets.includes(r.label));
 return <Chart data={data} subtitle="Choose a context to inspect datasets and measurement types" wide><div className="ov-context-tabs" role="group" aria-label="Expression context classes">{groups.map((group,i)=><button key={group.name} type="button" aria-pressed={selected===i} onClick={()=>setSelected(i)} style={colorStyle(palette[i%palette.length])}><span>{group.name}</span><strong>{data.rows.filter(r=>group.datasets.includes(r.label)).length}</strong><small>datasets</small></button>)}</div><div className="ov-expression-cards" aria-live="polite">{rows.map(row=><article key={row.label} style={colorStyle(palette[selected%palette.length])}><span>{expressionLabels[row.label]?.[1]??'Source measurement'}</span><h4>{expressionLabels[row.label]?.[0]??row.label}</h4><strong>{n(row.value)}</strong><small>source observations</small><details><summary>Dataset identity</summary><code>{row.label}</code></details></article>)}</div><p className="ov-axis-caption">Counts describe records, not expression intensity. GTEx median vectors are excluded here.</p></Chart>;
}

export function DataOverviewCharts({section}:{section:Section}){return <div className="db-chart-grid ov-chart-grid">{[...section.breakdowns].sort((a,b)=>section.id==='predictors'?Number(a.key==='tools')-Number(b.key==='tools'):0).map(data=>{
 const key=`${section.id}/${data.key}`;
 if(key==='proteins/classes')return <ProteinClasses key={key} data={data} total={section.metrics.find(m=>m.key==='proteins')?.value??0}/>;
 if(key==='proteins/sources')return <SourceFamilies key={key} data={data}/>;
 if(key==='variants/sources')return <Membership key={key} data={data}/>;
 if(key==='variants/consequences')return <Consequences key={key} data={data}/>;
 if(key==='predictors/tools')return <ToolkitInventory key={key} data={data}/>;
 if(key==='context/expression')return <ExpressionInventory key={key} data={data}/>;
 if(['predictors/groups','predictors/scope','diseases/sources','context/qtl'].includes(key))return <Composition key={key} data={data} subtitle={section.id==='predictors'?'Composition of published score fields':'Composition of stored source records'}/>;
 return <Chart key={key} data={data}><div className="ov-family-row">{data.rows.map(row=><div key={row.label}><RowName row={row}/><strong>{n(row.value)}</strong></div>)}</div></Chart>;
 })}</div>;}
