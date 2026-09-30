import { useCallback, useEffect, useId, useMemo, useRef, useState, type CSSProperties, type PointerEvent as ReactPointerEvent } from 'react';
import { useQueries, useQuery } from '@tanstack/react-query';
import { Activity, Check, ChevronDown, ChevronUp, Dna, Plus, RotateCcw, Trash2, X, ZoomIn, ZoomOut } from 'lucide-react';
import { api, number, params } from '../api';
import { HelpButton } from './HelpGuide';
import { AviTrack } from './AlphaGenomeAvi';
import './alphagenome-expression.css';
import { palette, predictionTextColor } from '../lib/palette';
import { QtlPicker, QtlTrack, type QtlDataset } from './AlphaGenomeQtl';
import { GenomeInspector } from './AlphaGenomeInspect';

type Track = {track_id:string;modality:string;name:string;assay_title:string;biosample_name:string|null;biosample_type:string|null;biosample_key?:string;ontology_curie:string|null;gtex_tissue?:string|null;strand:string|null;histone_mark:string|null;transcription_factor?:string|null;data_source:string|null;display_unit:string};
type Tile = {tile_id:string;window_start_0based:number;window_end_0based:number;chromosome:string};
type Gene = {ensembl_gene_id:string;gene_symbol:string;gene_start_1based:number;gene_end_1based_inclusive:number;gene_strand:string;status?:string;prediction_status?:string;tiles:Tile[]};
type Catalog = {available:boolean;genes:Gene[];tracks:Track[];snapshot:string;levels:number[];missing_modalities:string[];shared_modalities?:string[]};
type View = [number,number];
type TranscriptFeature = {feature:'CDS'|'stop_codon'|'exon'|'UTR';start_0based:number;end_0based:number;exon_number:number;strand:string};
type ManeModel = {status:string;transcript_id:string|null;segments:TranscriptFeature[];exons?:TranscriptFeature[];utrs?:TranscriptFeature[];transcript_start_0based?:number|null;transcript_end_0based?:number|null;cds_bases:number;cds_segments:number;chromosome:string;strand:string};
type Region = {start:number;end:number;chromosome:string};
type Signal = Region&{kind:'signal';mean:(number|null)[];maximum:(number|null)[];bin_width:number;bin_edges?:number[];source_resolution_bp?:number};
type Contacts = Region&{kind:'contacts';size:number;values:(number|null)[];bin_width:number;bin_edges?:number[];source_resolution_bp?:number};
type Junction = {rank:number;source_event_index?:number;start_0based:number;end_0based:number;strand:string;value:number|null};
type Junctions = Region&{kind:'junctions';items:Junction[];total:number;has_more:boolean;offset:number};
type TrackData = Signal|Contacts|Junctions;
const modes:Record<string,{label:string;color:string;group:string;help:string}> = {
 rna_seq:{label:'RNA-seq',color:palette.blue,group:'Transcription / RNA',help:'Reference-sequence RNA abundance prediction.'},
 cage:{label:'CAGE',color:palette.cyan,group:'Transcription / RNA',help:'Transcription start-site activity.'},
 procap:{label:'PRO-cap',color:palette.ice,group:'Transcription / RNA',help:'Nascent transcription initiation.'},
 atac:{label:'ATAC',color:palette.sage,group:'Accessibility',help:'Chromatin accessibility.'},
 dnase:{label:'DNase',color:palette.leaf,group:'Accessibility',help:'DNase-sensitive chromatin accessibility.'},
 chip_histone:{label:'Histone ChIP',color:palette.coral,group:'ChIP',help:'Histone-mark signal.'},
 chip_tf:{label:'TF ChIP',color:palette.rose,group:'ChIP',help:'Transcription-factor binding signal.'},
 splice_sites:{label:'Splice sites',color:palette.peach,group:'Splicing',help:'Shared donor and acceptor site probabilities; not biosample-specific.'},
 splice_site_usage:{label:'Splice usage',color:palette.apricot,group:'Splicing',help:'Reference-sequence splice-site usage prediction.'},
 splice_junctions:{label:'Splice junctions',color:palette.butter,group:'Splicing',help:'Predicted spliced-read connections.'},
 contact_maps:{label:'Contact map',color:palette.mist,group:'3D genome',help:'Signed contact enrichment relative to genomic-distance expectation.'},
};
const normalized=(s:string)=>s.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const contextName=(t:Track)=>t.biosample_name||'Shared prediction';
const sceneKey=(t:Track)=>t.biosample_key||t.ontology_curie||'';
const details=(t:Track)=>[t.assay_title,t.histone_mark,t.transcription_factor,t.strand&&t.strand!=='.'?`${t.strand} strand`:null].filter(Boolean).join(' · ');
const colorStyle=(color:string)=>({'--ag-color':color} as CSSProperties);
const location=(start:number,end:number)=>`${Math.floor(start+1).toLocaleString()}–${Math.ceil(end).toLocaleString()}`;
const finite=(values:(number|null)[])=>values.filter((v):v is number=>v!==null&&Number.isFinite(v));
const num=(value:number|null|undefined)=>value===null||value===undefined?'Not available':number(value,5);
const tick=(value:number)=>value!==0&&(Math.abs(value)<.01||Math.abs(value)>=10000)?value.toExponential(1):number(value,3);
const counted=(count:number,singular:string,plural=singular+'s')=>`${count.toLocaleString()} ${count===1?singular:plural}`;
const projectX=(position0:number,view:View)=>52+(position0-view[0])/(view[1]-view[0])*920;
const modeInfo=(id:string)=>modes[id]??{label:id,color:'#55606c',group:'Prediction',help:''};
function AlphaGenomeGuide({snapshot}:{snapshot?:string}){
 return <><div className="help-sections"><section><h3>Compare a biosample across modalities</h3><p>Choose a biosample first, then a modality and a specific assay track. Add more tracks without losing that biosample. Splice-site predictions are shared and have a separate entry.</p></section><section><h3>Two kinds of prediction</h3><p>AVI shows variant impact scores for current gene-associated project SNVs. It is independent of the selected biosample, and PHRED is not a pathogenicity probability. The other tracks predict the reference sequence; they are not measurements or alternate-allele effects.</p></section><section><h3>Coordinates and resolution</h3><p>All tracks use GRCh38 and the same visible interval. Coordinates shown here are 1-based. Wheel over the coordinate axis or drag the Pan slider to browse while keeping the current zoom. Click a transcript block to focus its source interval, or choose a CDS exon to focus its coding interval. Zoom requests finer data down to the source resolution. Means and maxima describe display bins; axes and units remain independent between assays. Missing values are not zero.</p></section><section><h3>MANE Select transcript structure</h3><p>Blue blocks mark coding sequence (CDS), gray blocks mark source-annotated UTR, and rose marks the separately annotated stop codon. Exon outlines share one line; arrows in the connecting introns show transcription direction. All features come from the same versioned MANE Select representative in MANE 1.5. Source UTR and stop-codon annotations can overlap; the stop codon is drawn on top. The versioned transcript is shown beside the axis. Missing MANE models are labelled explicitly. A gene-linked CDS does not establish an exact match to this UniProt protein or isoform.</p></section><section><h3>Overlay signals</h3><p>Selected one-dimensional tracks from the same biosample and modality share a panel and an original-value axis. Each assay or strand keeps its own curve, color and inspected values. Use the legend to hide or show a curve, or turn off Overlay same modality for separate panels. Signals are not summed, normalized or strand-flipped; differences between assays can affect their scales.</p></section><section><h3>GTEx QTL tracks</h3><p>GTEx v11 tissues are selected independently of AlphaGenome biosamples; samples are not matched. Tracks show variant–phenotype associations in the current model window. QTLs may occur outside this window. The vertical axis is −log₁₀(P), not effect size; original P, slope and phenotype remain in each track’s details. Coordinates are 1-based on screen; track scales are independent.</p></section><section><h3>Coverage and interpretation</h3><p>Blank AVI positions are not evidence of low impact. Same-position alternate alleles remain separate records. Feature contributions are displayed with their original sign and are not summed to reconstruct AVI. Overlapping model windows are inspected separately. Contact colors are centered on zero; splice junctions use explicit pages rather than a highest-score subset.</p></section></div><h3>Modalities</h3><div className="help-modality-grid">{Object.entries(modes).map(([id,m])=><section key={id} style={colorStyle(m.color)}><h3>{m.label}</h3><p>{m.help}</p></section>)}</div><div className="help-sources"><a href="https://www.alphagenomedocs.com/exploring_model_metadata.html" target="_blank" rel="noreferrer">Official modality definitions ↗</a></div>{snapshot&&<p>Reference snapshot: {snapshot}</p>}</>;
}
function PositionLine({position,view,height=120}:{position:number|null;view:View;height?:number}){
 if(position===null||position-1<view[0]||position-1>=view[1])return null;
 const x=projectX(position-1,view);return <line x1={x} x2={x} y1="0" y2={height} stroke="#2656c9" strokeWidth="1.2"/>;
}
type CoordinateProps = {
 view:View; position:number|null; hoverPosition:number|null;
 onHover:(position:number|null)=>void; brush:View|null;
};
function plotBounds(element:Element) {
 const rect=element.getBoundingClientRect(),style=getComputedStyle(element);
 const paddingLeft=parseFloat(style.paddingLeft)||0,paddingRight=parseFloat(style.paddingRight)||0;
 return {left:rect.left+paddingLeft,width:rect.width-paddingLeft-paddingRight};
}
function pointerPosition(element:Element,clientX:number,view:View) {
 const bounds=plotBounds(element),fraction=(1000*(clientX-bounds.left)/bounds.width-52)/920;
 return fraction<0||fraction>1?null:Math.min(view[1],Math.floor(view[0]+fraction*(view[1]-view[0]))+1);
}
function CoordinateOverlay({view,position,hoverPosition,brush,height=125}:{view:View;position:number|null;hoverPosition:number|null;brush:View|null;height?:number}) {
 const visible=hoverPosition!==null&&hoverPosition-1>=view[0]&&hoverPosition-1<view[1];
 return <g pointerEvents="none">
  {brush&&<rect className="agx-brush-selection" x={projectX(brush[0],view)} y={0} width={Math.max(0,projectX(brush[1],view)-projectX(brush[0],view))} height={height}/>}
  <PositionLine position={position} view={view} height={height}/>
  {visible&&<line className="agx-crosshair" x1={projectX(hoverPosition!-1,view)} x2={projectX(hoverPosition!-1,view)} y1={0} y2={height}/>}
 </g>;
}
function GenomicAxis({view,gene,chromosome,position,hoverPosition,onHover,brush,cds,canPan,onPan,onFocusFeature}:CoordinateProps&{gene:Gene;chromosome:string;cds?:ManeModel;canPan:boolean;onPan:(fraction:number)=>void;onFocusFeature:(block:TranscriptFeature)=>void}) {
 const axisRef=useRef<SVGSVGElement>(null);
 useEffect(()=>{
  const axis=axisRef.current;if(!axis)return;
  let pending=0,frame=0;
  const wheel=(event:WheelEvent)=>{
   if(!canPan||brush||event.ctrlKey||event.metaKey||event.buttons)return;
   const delta=Math.abs(event.deltaX)>Math.abs(event.deltaY)?event.deltaX:event.deltaY;
   if(!delta)return;
   event.preventDefault();
   const width=plotBounds(axis).width;
   pending+=delta*(event.deltaMode===1?16:event.deltaMode===2?width:1)/width;
   if(!frame)frame=requestAnimationFrame(()=>{const fraction=pending;pending=0;frame=0;onPan(fraction);});
  };
  axis.addEventListener('wheel',wheel,{passive:false});
  return()=>{axis.removeEventListener('wheel',wheel);cancelAnimationFrame(frame);};
 },[canPan,brush,onPan]);
 const hasStructure=Boolean(cds?.exons?.length);
 const modelStart=hasStructure?(cds!.transcript_start_0based??Math.min(...cds!.exons!.map(b=>b.start_0based))):gene.gene_start_1based-1;
 const modelEnd=hasStructure?(cds!.transcript_end_0based??Math.max(...cds!.exons!.map(b=>b.end_0based))):gene.gene_end_1based_inclusive;
 const left=Math.max(view[0],modelStart),right=Math.min(view[1],modelEnd);
 const visible=(b:TranscriptFeature)=>b.start_0based<view[1]&&b.end_0based>view[0];
 const exons=[...(cds?.exons??[])].sort((a,b)=>a.start_0based-b.start_0based);
 const gaps=hasStructure?exons.slice(1).map((b,i)=>[exons[i].end_0based,b.start_0based] as View):[[left,right] as View];
 const arrows=gaps.flatMap(([start,end])=>{
  const a=projectX(Math.max(view[0],start),view),b=projectX(Math.min(view[1],end),view),count=Math.floor((b-a)/45);
  return Array.from({length:Math.max(0,count)},(_,i)=>a+(i+1)*(b-a)/(count+1));
 });
 const strand=cds?.strand??gene.gene_strand;
 const features=[...exons.filter(visible),...(cds?.utrs?.filter(visible)??[]),...(cds?.segments.filter(visible)??[])];
 const current=hoverPosition??position,within=current!==null&&current-1>=view[0]&&current-1<view[1];
 const currentFeature=current===null?null:features.find(b=>b.feature==='stop_codon'&&current-1>=b.start_0based&&current-1<b.end_0based)??features.find(b=>b.feature==='CDS'&&current-1>=b.start_0based&&current-1<b.end_0based)??features.find(b=>b.feature==='UTR'&&current-1>=b.start_0based&&current-1<b.end_0based)??features.find(b=>current-1>=b.start_0based&&current-1<b.end_0based);
 const featureLabel=(b:TranscriptFeature)=>b.feature==='stop_codon'?'Stop codon':b.feature==='exon'?'Exon':b.feature;
 const hoverLabel=currentFeature?` · ${featureLabel(currentFeature)} · exon ${currentFeature.exon_number}`:hasStructure&&current!==null&&current-1>=modelStart&&current-1<modelEnd?' · Intron':'';
 return <div className="agx-axis-row"><div className="agx-axis-label"><strong className="agx-gene-name">{gene.gene_symbol}</strong>{(cds?.status==='available'||hasStructure)&&cds?<><span>MANE Select · {strand} strand</span><span className="agx-transcript" title={`${cds.transcript_id} · ${cds.cds_segments} coding segments`}>{cds.transcript_id}</span><div className="agx-cds-guide">{cds.cds_segments>0&&<b className="agx-cds-key"><i/>CDS</b>}{Boolean(cds.utrs?.length)&&<b className="agx-cds-key"><i className="agx-utr-key"/>UTR</b>}</div>{cds.status!=='available'&&<span>CDS not available</span>}</>:<span>{cds?`MANE CDS: ${cds.status.replaceAll('_',' ')}`:'Loading MANE model…'}</span>}</div>
  <svg ref={axisRef} className="agx-axis" viewBox="0 0 1000 112" preserveAspectRatio="none" role="img" tabIndex={0} aria-label="Shared genomic coordinates and MANE transcript structure. Wheel to pan; drag to zoom; arrow keys inspect positions."
   onPointerMove={e=>onHover(pointerPosition(e.currentTarget,e.clientX,view))} onPointerLeave={()=>onHover(null)} onBlur={()=>onHover(null)}
   onFocus={e=>{if(e.currentTarget.matches(':focus-visible'))onHover(Math.floor((view[0]+view[1])/2)+1);}} onKeyDown={e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();onHover(Math.max(view[0]+1,Math.min(view[1],(current??view[0]+1)+(e.key==='ArrowRight'?1:-1))));}}}>
   {[0,.25,.5,.75,1].map(r=><g key={r}><line x1={52+r*920} x2={52+r*920} y1="20" y2="37" stroke="#a0a5aa"/><text x={52+r*920} y="14" textAnchor={r===0?'start':r===1?'end':'middle'}>{Math.round(view[0]+r*(view[1]-view[0])+(r===1?0:1)).toLocaleString()}</text></g>)}
   {left<right&&<g className="agx-transcript-line" stroke="#303438" fill="none" strokeWidth="1.5"><line x1={projectX(left,view)} x2={projectX(right,view)} y1="66" y2="66"/>{arrows.map((x,i)=><path key={i} d={strand==='-'?`M${x+3} 62 L${x-2} 66 L${x+3} 70`:`M${x-3} 62 L${x+2} 66 L${x-3} 70`}/>)}</g>}
   {features.map((b,i)=>{
    const x=projectX(Math.max(view[0],b.start_0based),view),width=Math.max(.8,projectX(Math.min(view[1],b.end_0based),view)-x);
    const coding=b.feature==='CDS'||b.feature==='stop_codon',height=coding?24:14;
    const color=b.feature==='CDS'?'#3784b5':b.feature==='stop_codon'?palette.rose:'#797e84';
    const name=`MANE ${featureLabel(b)} · exon ${b.exon_number} · ${chromosome}:${location(b.start_0based,b.end_0based)} · ${b.strand} strand`;
    return <g key={`${b.feature}:${b.start_0based}:${i}`}><rect className="agx-cds-block" data-feature={b.feature} data-exon={b.exon_number} data-start={b.start_0based+1} data-end={b.end_0based} x={x} y={66-height/2} width={width} height={height} fill={b.feature==='exon'?'#fff':color} stroke={color} strokeWidth={b.feature==='exon'?1:.5} role="button" tabIndex={0} aria-label={`Zoom to ${name}`} onClick={()=>onFocusFeature(b)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();onFocusFeature(b);}}}><title>{name} · click to zoom</title></rect>{width>28&&b.feature==='CDS'&&<text className="agx-cds-exon-number" x={x+width/2} y={70} textAnchor="middle" pointerEvents="none">{b.exon_number}</text>}</g>;
   })}
   <CoordinateOverlay view={view} position={position} hoverPosition={hoverPosition} brush={brush} height={112}/>
   {within&&current!==null&&<text className="agx-hover-coordinate" x={Math.max(55,Math.min(965,projectX(current-1,view)))} y="106" textAnchor={projectX(current-1,view)>720?'end':'start'}>{chromosome}:{current.toLocaleString()}{hoverLabel}</text>}
   {brush&&<text className="agx-hover-coordinate" x="510" y="73" textAnchor="middle">{location(brush[0],brush[1])} · release to zoom</text>}
  </svg></div>;
}
type SignalSeries = {track:Track;data:Signal;color:string};
function SignalPlot({data,view,color,stat,position,hoverPosition,onHover,brush,series}:CoordinateProps&{data:Signal;color:string;stat:'mean'|'maximum';series?:SignalSeries[]}) {
 const [localHover,setLocalHover]=useState(false),clipId=useId();
 const lines=series?.map(s=>({...s,label:details(s.track)||s.track.name,id:s.track.track_id}))??[{data,color,label:'Signal',id:'signal'}];
 const good=lines.flatMap(l=>finite(l.data[stat])),low=good.reduce((n,v)=>Math.min(n,v),0),high=good.reduce((n,v)=>Math.max(n,v),0),span=high-low||1;
 const edge=(d:Signal,i:number)=>d.bin_edges?.[i]??d.start+i*(d.end-d.start)/d.mean.length;
 const current=hoverPosition??position,cx=current===null?52:projectX(current-1,view),y=(v:number)=>105-(v-low)/span*83;
 const inspected=lines.map(l=>({...l,index:current===null?-1:l.data.mean.findIndex((_,i)=>current-1>=edge(l.data,i)&&current-1<edge(l.data,i+1))}));
 const pathFor=(d:Signal)=>{let path='',previous=false;for(let i=0;i<d[stat].length;i++){const v=d[stat][i];if(v===null){previous=false;continue;}path+=`${previous?'L':'M'}${projectX(edge(d,i),view).toFixed(2)},${y(v).toFixed(2)} H${projectX(edge(d,i+1),view).toFixed(2)} `;previous=true;}return path;};
 const active=inspected.find(l=>l.index>=0);
 return <><div className="agx-plot-frame"><svg className="agx-signal" viewBox="0 0 1000 118" preserveAspectRatio="none" role="img" tabIndex={0} aria-label={`Predicted ${stat} signal. ${lines.length} separate series. Drag to zoom; arrow keys inspect bins.`}
  onPointerMove={e=>{setLocalHover(true);onHover(pointerPosition(e.currentTarget,e.clientX,view));}} onPointerLeave={()=>{setLocalHover(false);onHover(null);}}
  onFocus={e=>{if(e.currentTarget.matches(':focus-visible')){setLocalHover(true);onHover(Math.max(view[0]+1,Math.floor(edge(data,0))+1));}}} onBlur={()=>{setLocalHover(false);onHover(null);}}
  onKeyDown={e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const next=Math.max(0,Math.min(data.mean.length-1,(active?.index??0)+(e.key==='ArrowRight'?1:-1)));onHover(Math.max(view[0]+1,Math.min(view[1],Math.floor((edge(data,next)+edge(data,next+1))/2)+1)));}}}>
  {[0,.5,1].map(r=><g key={r}><line x1="52" x2="972" y1={22+r*83} y2={22+r*83} stroke="#d9dcdf"/><text x="44" y={26+r*83} textAnchor="end">{tick(high-r*(high-low))}</text></g>)}
  <defs><clipPath id={clipId}><rect x="52" y="0" width="920" height="118"/></clipPath></defs>
  {lines.map((l,i)=><path key={l.id} data-series={l.id} d={pathFor(l.data)} clipPath={`url(#${clipId})`} fill="none" stroke={l.color} strokeWidth="1.6" vectorEffect="non-scaling-stroke" strokeDasharray={i>=11?'5 3':undefined}/>)}
  <CoordinateOverlay view={view} position={position} hoverPosition={hoverPosition} brush={brush} height={118}/>
  {inspected.filter(l=>l.index>=0&&l.data[stat][l.index]!==null).map(l=><g key={l.id} pointerEvents="none"><line className="agx-crosshair agx-crosshair-horizontal" x1="52" x2="972" y1={y(l.data[stat][l.index]!)} y2={y(l.data[stat][l.index]!)}/><circle cx={cx} cy={y(l.data[stat][l.index]!)} r="3.5" fill={l.color} stroke="white" strokeWidth="1.5"/></g>)}
  </svg>{localHover&&active&&current!==null&&!brush&&<GenomeInspector title={series?.length?modeInfo(series[0].track.modality).label:'Reference signal'} coordinate={`${data.chromosome}:${current.toLocaleString()}`} left={Math.max(6,Math.min(60,cx/10+1))}>
   {inspected.map(l=><section key={l.id}><div className="agx-inspector-series"><i style={{background:l.color}}/>{l.label}</div>{l.index<0?<p>No data at this coordinate</p>:<><span className="agx-inspector-bin">Bin {location(edge(l.data,l.index),edge(l.data,l.index+1))}</span><dl><div><dt>Mean</dt><dd>{num(l.data.mean[l.index])}</dd></div><div><dt>Maximum</dt><dd>{num(l.data.maximum[l.index])}</dd></div></dl></>}</section>)}
  </GenomeInspector>}</div>
  <div className="agx-inspect">{!active?<><Activity size={12}/><span title={`Source resolution: ${number(data.source_resolution_bp??data.bin_width,2)} bp`}>{number(data.bin_width,2)} bp/bin</span><span>Hover for values</span></>:<><strong>{data.chromosome}:{current!.toLocaleString()}</strong>{inspected.filter(l=>l.index>=0).map(l=><span key={l.id}><i className="agx-inline-swatch" style={{background:l.color}}/>{lines.length>1?l.label+' · ':''}{stat==='mean'?'Mean':'Maximum'} <b>{num(l.data[stat][l.index])}</b></span>)}</>}</div>
  {!good.length&&<p>No finite signal is available in this range.</p>}</>;
}
function ContactPlot({data,position,hoverPosition,onHover}:{data:Contacts;position:number|null;hoverPosition:number|null;onHover:(position:number|null)=>void}) {
 const canvas=useRef<HTMLCanvasElement>(null),[hover,setHover]=useState<[number,number]|null>(null);
 const peak=useMemo(()=>finite(data.values).reduce((n,v)=>Math.max(n,Math.abs(v)),0),[data.values]);
 useEffect(()=>{const ctx=canvas.current?.getContext('2d');if(!ctx)return;const pixels=ctx.createImageData(data.size,data.size);for(let y=0;y<data.size;y++)for(let x=0;x<data.size;x++){const v=data.values[y*data.size+x],strength=v===null?0:Math.min(1,Math.abs(v)/(peak||1)),target=v!==null&&v<0?[123,149,198]:[200,94,98],i=(y*data.size+x)*4;for(let c=0;c<3;c++)pixels.data[i+c]=v===null?[218,225,235][c]:Math.round(250+(target[c]-250)*strength);pixels.data[i+3]=255;}ctx.putImageData(pixels,0,0);},[data,peak]);
 const edge=(i:number)=>data.bin_edges?.[i]??data.start+i*data.bin_width;
 const coord=(i:number)=>location(edge(i),edge(i+1));
 const inspect=(x:number,y:number)=>{setHover([x,y]);onHover(Math.floor((edge(x)+edge(x+1))/2)+1);};
 const current=hoverPosition??position,sharedIndex=current===null?-1:Array.from({length:data.size},(_,i)=>i).findIndex(i=>current-1>=edge(i)&&current-1<edge(i+1));
 return <div className="agx-contact"><div><div className="agx-contact-plot"><canvas ref={canvas} width={data.size} height={data.size} role="img" tabIndex={0} aria-label="Contact matrix. Arrow keys inspect both genomic axes."
  onFocus={e=>{if(e.currentTarget.matches(':focus-visible'))inspect(0,0);}} onBlur={()=>{setHover(null);onHover(null);}} onKeyDown={e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();const [x,y]=hover??[0,0];inspect(Math.max(0,Math.min(data.size-1,x+(e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0))),Math.max(0,Math.min(data.size-1,y+(e.key==='ArrowDown'?1:e.key==='ArrowUp'?-1:0))));}}
  onPointerMove={e=>{const r=e.currentTarget.getBoundingClientRect();inspect(Math.max(0,Math.min(data.size-1,Math.floor((e.clientX-r.left)/r.width*data.size))),Math.max(0,Math.min(data.size-1,Math.floor((e.clientY-r.top)/r.height*data.size))));}} onPointerLeave={()=>{setHover(null);onHover(null);}}/>
  <svg viewBox="0 0 100 100" className="agx-contact-crosshair" aria-hidden="true">{sharedIndex>=0&&<line className="agx-crosshair" x1={(sharedIndex+.5)/data.size*100} x2={(sharedIndex+.5)/data.size*100} y1={0} y2={100}/>} {hover&&<line className="agx-crosshair agx-crosshair-horizontal" x1={0} x2={100} y1={(hover[1]+.5)/data.size*100} y2={(hover[1]+.5)/data.size*100}/>}</svg></div><p>Both axes · {data.chromosome}:{location(data.start,data.end)}</p></div>
  <div><strong>Relative contact signal</strong><div className="agx-contact-legend"/><p>−{num(peak)} · 0 · +{num(peak)}</p><p>Log-fold over expectation · gray = missing</p><p>{data.size} × {data.size} · {number(data.bin_width,0)} bp per cell axis</p>{hover&&<div className="agx-inspect">X {data.chromosome}:{coord(hover[0])}<br/>Y {data.chromosome}:{coord(hover[1])}<br/><b>{num(data.values[hover[1]*data.size+hover[0]])}</b></div>}</div></div>;
}
function JunctionPlot({data,view,color,position,hoverPosition,onHover,brush}:CoordinateProps&{data:Junctions;color:string}) {
 const [active,setActive]=useState<Junction|null>(null);
 const peak=data.items.reduce((n,j)=>j.value===null?n:Math.max(n,Math.abs(j.value)),1),x=(p:number)=>projectX(Math.max(view[0],Math.min(view[1],p)),view);
 return <><div className="agx-plot-frame"><svg className="agx-junctions" preserveAspectRatio="none" viewBox="0 0 1000 150" aria-label="Predicted splice junction connections. Drag to zoom."
  onPointerMove={e=>onHover(pointerPosition(e.currentTarget,e.clientX,view))} onPointerLeave={()=>{setActive(null);onHover(null);}}>
  <line x1="52" x2="972" y1="130" y2="130" stroke="#d3d8de"/>
  {data.items.filter((j):j is Junction&{value:number}=>j.value!==null).map(j=><path key={`${j.source_event_index??j.rank}:${j.strand}`} d={`M${x(j.start_0based)},130 Q${(x(j.start_0based)+x(j.end_0based))/2},${120-Math.sqrt(Math.abs(j.value)/peak)*110} ${x(j.end_0based)},130`} tabIndex={0} aria-label={`Junction ${location(j.start_0based,j.end_0based)}, ${j.strand} strand, value ${num(j.value)}`} onFocus={()=>setActive(j)} onBlur={()=>setActive(null)} onPointerEnter={()=>setActive(j)} onPointerLeave={()=>setActive(null)} stroke={color} strokeOpacity={active===j?1:.2+.8*Math.abs(j.value)/peak} strokeWidth={active===j?3:1.4} fill="none"></path>)}
  <CoordinateOverlay view={view} position={position} hoverPosition={hoverPosition} brush={brush} height={145}/>
  </svg>{active&&!brush&&<GenomeInspector title="Splice junctions" coordinate={`${data.chromosome}:${location(active.start_0based,active.end_0based)}`} left={7}><dl><div><dt>Strand</dt><dd>{active.strand==='+'?'+ · forward':'− · reverse'}</dd></div><div><dt>Junction signal</dt><dd>{num(active.value)}</dd></div></dl><p className="agx-inspector-note">Coordinates show the complete source interval. Arc height is a visual guide.</p></GenomeInspector>}</div><details><summary>Junction coordinates and values · {data.items.length.toLocaleString()} shown</summary><div className="agx-junction-table"><table><thead><tr><th>Interval (1-based)</th><th>Strand</th><th>Value</th></tr></thead><tbody>{data.items.map(j=><tr key={`${j.source_event_index??j.rank}:${j.strand}`}><td>{location(j.start_0based,j.end_0based)}</td><td>{j.strand}</td><td>{num(j.value)}</td></tr>)}</tbody></table></div></details></>;
}
function TrackCard({accession,gene,tile,track,view,position,hoverPosition,onHover,brush,onRemove,onMove,index,total}:CoordinateProps&{accession:string;gene:Gene;tile:Tile;track:Track;onRemove:()=>void;onMove:(delta:number)=>void;index:number;total:number}){
 const ref=useRef<HTMLElement>(null),[visible,setVisible]=useState(false),[collapsed,setCollapsed]=useState(false),[stat,setStat]=useState<'mean'|'maximum'>('mean'),[offset,setOffset]=useState(0);
 useEffect(()=>{const observer=new IntersectionObserver(entries=>setVisible(entries.some(e=>e.isIntersecting)),{rootMargin:'500px'});if(ref.current)observer.observe(ref.current);return()=>observer.disconnect();},[]);
 useEffect(()=>setOffset(0),[view[0],view[1],tile.tile_id]);
 const query=useQuery({queryKey:['expression-alphagenome-track',accession,gene.ensembl_gene_id,tile.tile_id,track.track_id,view[0],view[1],offset],queryFn:({signal})=>api<TrackData>(`/proteins/${accession}/expression/alphagenome/track?${params({gene:gene.ensembl_gene_id,tile:tile.tile_id,track_id:track.track_id,start:view[0],end:view[1],bins:1024,offset,limit:500})}`,signal),enabled:visible&&!collapsed,staleTime:300000,gcTime:120000,retry:1});
 const meta=modeInfo(track.modality),d=query.data;
 return <article ref={ref} className={`agx-track${collapsed?' is-collapsed':''}`} style={colorStyle(meta.color)}><header><div className="agx-track-title"><span className="agx-track-kind">{meta.label}</span><strong>{contextName(track)}</strong><span>{details(track)}</span>{track.modality==='splice_sites'&&<small>Shared · not biosample-specific</small>}</div><div className="agx-track-actions"><button title="Move track up" aria-label={`Move ${track.track_id} up`} disabled={index===0} onClick={()=>onMove(-1)}><ChevronUp size={15}/></button><button title="Move track down" aria-label={`Move ${track.track_id} down`} disabled={index===total-1} onClick={()=>onMove(1)}><ChevronDown size={15}/></button><button aria-label={`${collapsed?'Expand':'Collapse'} ${track.track_id}`} aria-expanded={!collapsed} onClick={()=>setCollapsed(!collapsed)}>{collapsed?<Plus size={15}/>:<ChevronUp size={15}/>}</button><button aria-label={`Remove ${track.track_id}`} onClick={onRemove}><X size={15}/></button></div></header><div className="agx-track-body">{collapsed?<span className="agx-collapsed-label">Track collapsed</span>:<><div className="agx-track-meta"><span>Reference prediction · {track.display_unit||'Source scale'}</span>{d?.kind==='signal'&&<div className="agx-segment" aria-label={`Statistic for ${track.track_id}`}><button aria-pressed={stat==='mean'} onClick={()=>setStat('mean')}>Mean</button><button aria-pressed={stat==='maximum'} onClick={()=>setStat('maximum')}>Maximum</button></div>}</div>{query.error?<div className="agx-error" role="alert">{query.error.message}<button onClick={()=>query.refetch()}>Retry track</button></div>:d?.kind==='signal'?<SignalPlot data={d} view={view} color={predictionTextColor(meta.color)} stat={stat} position={position} hoverPosition={hoverPosition} onHover={onHover} brush={brush}/>:d?.kind==='contacts'?<ContactPlot data={d} position={position} hoverPosition={hoverPosition} onHover={onHover}/>:d?.kind==='junctions'?<><JunctionPlot data={d} view={view} color={meta.color} position={position} hoverPosition={hoverPosition} onHover={onHover} brush={brush}/><div className="agx-pagination"><span>{d.items.length?offset+1:0}–{offset+d.items.length} of {number(d.total,0)} events · source order</span><button disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-500))}>Previous</button><button disabled={!d.has_more} onClick={()=>setOffset(offset+500)}>Next</button></div></>:<div className="agx-loading">{visible?'Loading reference prediction…':'Track loads when scrolled into view.'}</div>}</>}</div></article>;
}
const seriesColors=[palette.blue,palette.coral,palette.sage,palette.cyan,palette.rose,palette.apricot,palette.leaf,palette.ice,palette.peach,palette.butter,palette.mist];
const signalModality=(t:Track)=>!['contact_maps','splice_junctions'].includes(t.modality);
function SignalGroupCard({accession,gene,tile,tracks,catalogTracks,view,position,hoverPosition,onHover,brush,onRemove,onRemoveSeries,onMove,index,total}:CoordinateProps&{accession:string;gene:Gene;tile:Tile;tracks:Track[];catalogTracks:Track[];onRemove:()=>void;onRemoveSeries:(id:string)=>void;onMove:(delta:number)=>void;index:number;total:number}) {
 const ref=useRef<HTMLElement>(null),[visible,setVisible]=useState(false),[collapsed,setCollapsed]=useState(false),[stat,setStat]=useState<'mean'|'maximum'>('mean'),[hidden,setHidden]=useState<string[]>([]);
 useEffect(()=>{const observer=new IntersectionObserver(entries=>setVisible(entries.some(e=>e.isIntersecting)),{rootMargin:'500px'});if(ref.current)observer.observe(ref.current);return()=>observer.disconnect();},[]);
 const queries=useQueries({queries:tracks.map(track=>({queryKey:['expression-alphagenome-track',accession,gene.ensembl_gene_id,tile.tile_id,track.track_id,view[0],view[1],0],queryFn:({signal}:{signal:AbortSignal})=>api<Signal>(`/proteins/${accession}/expression/alphagenome/track?${params({gene:gene.ensembl_gene_id,tile:tile.tile_id,track_id:track.track_id,start:view[0],end:view[1],bins:1024,offset:0,limit:500})}`,signal),enabled:visible&&!collapsed,staleTime:300000,gcTime:120000,retry:1}))});
 const catalogColors=catalogTracks.filter(t=>sceneKey(t)===sceneKey(tracks[0])&&t.modality===tracks[0].modality&&t.display_unit===tracks[0].display_unit).sort((a,b)=>a.track_id.localeCompare(b.track_id));
 const color=(t:Track)=>predictionTextColor(catalogColors.length===1?modeInfo(t.modality).color:seriesColors[catalogColors.findIndex(x=>x.track_id===t.track_id)%seriesColors.length]);
 const lines=tracks.flatMap((track,i)=>queries[i].data&&!hidden.includes(track.track_id)?[{track,data:queries[i].data!,color:color(track)}]:[]),meta=modeInfo(tracks[0].modality),groupId=tracks.map(t=>t.track_id).join(',');
 return <article ref={ref} className={`agx-track agx-signal-track${collapsed?' is-collapsed':''}`} style={colorStyle(meta.color)}><header><div className="agx-track-title"><span className="agx-track-kind">{meta.label}</span><strong>{contextName(tracks[0])}</strong><span>{tracks.length>1?`${tracks.length} separate signals`:details(tracks[0])}</span></div><div className="agx-track-actions"><button aria-label={`Move ${groupId} up`} disabled={index===0} onClick={()=>onMove(-1)}><ChevronUp size={14}/></button><button aria-label={`Move ${groupId} down`} disabled={index===total-1} onClick={()=>onMove(1)}><ChevronDown size={14}/></button><button aria-label={`${collapsed?'Expand':'Collapse'} ${groupId}`} aria-expanded={!collapsed} onClick={()=>setCollapsed(!collapsed)}>{collapsed?<Plus size={14}/>:<ChevronUp size={14}/>}</button><button aria-label={`Remove track panel ${groupId}`} onClick={onRemove}><X size={14}/></button></div></header>
  <div className="agx-track-body">{collapsed?<span className="agx-collapsed-label">Track collapsed</span>:<><div className="agx-track-meta"><span>{tracks.length>1?'Overlay · original shared scale':tracks[0].display_unit}</span><div className="agx-segment"><button aria-pressed={stat==='mean'} onClick={()=>setStat('mean')}>Mean</button><button aria-pressed={stat==='maximum'} onClick={()=>setStat('maximum')}>Maximum</button></div></div>
   {tracks.length>1&&<div className="agx-series-legend" aria-label={`${meta.label} signals`}>{tracks.map(t=><span key={t.track_id}><button aria-pressed={!hidden.includes(t.track_id)} onClick={()=>setHidden(h=>h.includes(t.track_id)?h.filter(id=>id!==t.track_id):[...h,t.track_id])}><i style={{background:color(t)}}/>{details(t)||t.name}</button><button aria-label={`Remove ${t.track_id} from overlay`} onClick={()=>onRemoveSeries(t.track_id)}><X size={11}/></button></span>)}</div>}
   {lines.length>0&&queries.some(q=>q.isPending)&&<span className="agx-track-notice">Loading {queries.filter(q=>q.isPending).length} signal(s)…</span>}
   {queries.map((q,i)=>q.error&&<div key={tracks[i].track_id} className="agx-error">{details(tracks[i])}: {q.error.message}<button onClick={()=>q.refetch()}>Retry</button></div>)}
   {lines.length?<SignalPlot data={lines[0].data} color={lines[0].color} series={lines} view={view} stat={stat} position={position} hoverPosition={hoverPosition} onHover={onHover} brush={brush}/>:queries.some(q=>q.isPending)?<div className="agx-loading">Loading reference signals…</div>:<div className="agx-loading">{tracks.every(t=>hidden.includes(t.track_id))?'All signals hidden. Select a legend item to show it.':'No signal is available. Retry the failed request above.'}</div>}
  </>}</div></article>;
}
function initialView(gene:Gene,tile:Tile):View{const pad=Math.max(1000,(gene.gene_end_1based_inclusive-gene.gene_start_1based)*.08);const start=Math.max(tile.window_start_0based,Math.floor(gene.gene_start_1based-1-pad)),end=Math.min(tile.window_end_0based,Math.ceil(gene.gene_end_1based_inclusive+pad));return start<end?[start,end]:[tile.window_start_0based,tile.window_end_0based];}
function Workspace({catalog,accession,expressionContext}:{catalog:Catalog;accession:string;expressionContext:string}){
 const initial=catalog.genes.find(g=>g.tiles.length>0)!;
 const [geneId,setGeneId]=useState(initial.ensembl_gene_id),[tileId,setTileId]=useState(initial.tiles[0].tile_id),[selected,setSelected]=useState<string[]>([]),[scene,setScene]=useState(''),[mode,setMode]=useState(''),[search,setSearch]=useState(''),[library,setLibrary]=useState(true),[view,setView]=useState<View>(initialView(initial,initial.tiles[0])),[position,setPosition]=useState<number|null>(null);
 const gene=catalog.genes.find(g=>g.ensembl_gene_id===geneId)??initial,tile=gene.tiles.find(t=>t.tile_id===tileId)??gene.tiles[0];
 const [overlay,setOverlay]=useState(true);
 const [qtlLibrary,setQtlLibrary]=useState(false),[qtlSelected,setQtlSelected]=useState<QtlDataset[]>([]);
 useEffect(()=>{setQtlSelected([]);},[geneId]);
 const cdsQuery=useQuery({queryKey:['alphagenome-mane-cds',accession,geneId],queryFn:({signal})=>api<ManeModel>(`/proteins/${accession}/expression/alphagenome/cds?${params({gene:geneId})}`,signal),staleTime:300000,retry:1});
 const [hoverPosition,setHoverPosition]=useState<number|null>(null),[brush,setBrush]=useState<View|null>(null);
 const drag=useRef<{pointer:number;startX:number;left:number;width:number;origin:View;anchor:number;active:boolean;element:Element}|null>(null),suppressClick=useRef(false);
 useEffect(()=>{setHoverPosition(null);setBrush(null);const current=drag.current;drag.current=null;if(current?.element.hasPointerCapture(current.pointer))current.element.releasePointerCapture(current.pointer);},[geneId,tileId,view[0],view[1]]);
 const cancelBrush=()=>{const current=drag.current;drag.current=null;if(current?.element.hasPointerCapture(current.pointer))current.element.releasePointerCapture(current.pointer);setBrush(null);setHoverPosition(null);};
 const beginBrush=(event:ReactPointerEvent<HTMLDivElement>)=>{
  if(event.button!==0||!event.isPrimary)return;
  const plot=(event.target as Element).closest('svg.agx-axis, svg.agx-signal, canvas.agx-avi-canvas, svg.agx-junctions');
  if(!plot)return;
  const anchor=pointerPosition(plot,event.clientX,view);if(anchor===null)return;
  const bounds=plotBounds(plot);suppressClick.current=false;
  drag.current={pointer:event.pointerId,startX:event.clientX,left:bounds.left,width:bounds.width,origin:[...view],anchor:anchor-1,active:false,element:plot};
 };
 const moveBrush=(event:ReactPointerEvent<HTMLDivElement>)=>{
  const current=drag.current;if(!current||current.pointer!==event.pointerId)return;
  if(!(event.buttons&1)){cancelBrush();return;}
  if(!current.active&&Math.abs(event.clientX-current.startX)<6)return;
  if(!current.active){current.active=true;current.element.setPointerCapture(event.pointerId);}
  const fraction=Math.max(0,Math.min(1,(1000*(event.clientX-current.left)/current.width-52)/920));
  const point=Math.min(current.origin[1]-1,Math.floor(current.origin[0]+fraction*(current.origin[1]-current.origin[0])));
  setBrush([Math.min(current.anchor,point),Math.max(current.anchor,point)+1]);setHoverPosition(point+1);event.preventDefault();
 };
 const endBrush=(event:ReactPointerEvent<HTMLDivElement>)=>{
  const current=drag.current;if(!current||current.pointer!==event.pointerId)return;
  drag.current=null;
  if(current.active){
   const fraction=Math.max(0,Math.min(1,(1000*(event.clientX-current.left)/current.width-52)/920));
   const point=Math.min(current.origin[1]-1,Math.floor(current.origin[0]+fraction*(current.origin[1]-current.origin[0])));
   const low=Math.min(current.anchor,point),high=Math.max(current.anchor,point)+1;
   const span=Math.min(tile.window_end_0based-tile.window_start_0based,Math.max(32,high-low));
   const start=Math.max(tile.window_start_0based,Math.min(tile.window_end_0based-span,Math.floor((low+high-span)/2)));
   suppressClick.current=true;setView([start,start+span]);setHoverPosition(null);event.preventDefault();
  }
  setBrush(null);if(current.element.hasPointerCapture(event.pointerId))current.element.releasePointerCapture(event.pointerId);
 };
 const resetTracks=()=>{setSelected([]);setScene('');setMode('');setSearch('');setLibrary(true);};

 const shared=(t:Track)=>(catalog.shared_modalities??['splice_sites']).includes(t.modality);
 const biosamples=[...new Map(catalog.tracks.filter(t=>!shared(t)&&sceneKey(t)).map(t=>[sceneKey(t),{id:sceneKey(t),name:contextName(t),type:t.biosample_type}])).values()].sort((a,b)=>a.name.localeCompare(b.name));
 const contextTracks=catalog.tracks.filter(t=>scene==='shared'?shared(t):!shared(t)&&sceneKey(t)===scene),availableModes=[...new Set(contextTracks.map(t=>t.modality))],activeMode=availableModes.includes(mode)?mode:availableModes[0]??'';
 const available=contextTracks.filter(t=>t.modality===activeMode&&normalized([contextName(t),details(t),t.name,t.ontology_curie].join(' ')).includes(normalized(search)));
 const panels=useMemo(()=>{const groups:{key:string;tracks:Track[]}[]=[];for(const id of selected){const t=catalog.tracks.find(t=>t.track_id===id);if(!t)continue;const key=overlay&&signalModality(t)?`${sceneKey(t)}:${t.modality}:${t.display_unit}`:t.track_id;const existing=groups.find(g=>g.key===key);if(existing)existing.tracks.push(t);else groups.push({key,tracks:[t]});}return groups;},[selected,catalog.tracks,overlay]);
 const removeIds=(ids:string[])=>setSelected(current=>current.filter(id=>!ids.includes(id)));
 const movePanel=(index:number,delta:number)=>{const next=[...panels];[next[index],next[index+delta]]=[next[index+delta],next[index]];setSelected(next.flatMap(p=>p.tracks.map(t=>t.track_id)));};
 const matches=catalog.tracks.filter(t=>!shared(t)&&expressionContext&&[t.gtex_tissue,t.biosample_name].some(name=>name&&normalized(name)===normalized(expressionContext)));
 const add=(id:string)=>setSelected(current=>current.includes(id)?current.filter(v=>v!==id):[...current,id]);
 const changeScene=(id:string)=>{setScene(id);setMode('');setSearch('');};
 const changeGene=(id:string)=>{const g=catalog.genes.find(g=>g.ensembl_gene_id===id)!;setGeneId(id);setTileId(g.tiles[0].tile_id);setView(initialView(g,g.tiles[0]));setPosition(null);};
 const panFraction=useCallback((fraction:number)=>{
  setHoverPosition(null);
  setView(current=>{const span=current[1]-current[0],left=Math.round(Math.max(tile.window_start_0based,Math.min(tile.window_end_0based-span,current[0]+fraction*span)));return left===current[0]?current:[left,left+span];});
 },[tile.window_start_0based,tile.window_end_0based]);
 const focusFeature=(block:TranscriptFeature)=>{
  const span=Math.min(tile.window_end_0based-tile.window_start_0based,Math.max(200,Math.ceil((block.end_0based-block.start_0based)*1.6)));
  const left=Math.max(tile.window_start_0based,Math.min(tile.window_end_0based-span,Math.floor((block.start_0based+block.end_0based-span)/2)));
  setHoverPosition(null);setView([left,left+span]);
 };
 const windowSpan=tile.window_end_0based-tile.window_start_0based,viewSpan=view[1]-view[0];
 const windowCds=cdsQuery.data?.segments.filter(b=>b.feature==='CDS'&&b.start_0based<tile.window_end_0based&&b.end_0based>tile.window_start_0based).sort((a,b)=>a.exon_number-b.exon_number)??[];
 const zoom=(factor:number)=>{const span=Math.round(Math.min(tile.window_end_0based-tile.window_start_0based,Math.max(32,(view[1]-view[0])*factor))),left=Math.round(Math.max(tile.window_start_0based,Math.min(tile.window_end_0based-span,(view[0]+view[1]-span)/2)));setView([left,left+span]);};
 const focusVariant=(position1:number)=>{const span=Math.min(200,tile.window_end_0based-tile.window_start_0based),start=Math.round(Math.max(tile.window_start_0based,Math.min(tile.window_end_0based-span,position1-1-span/2)));setView([start,start+span]);};
 const pan=(direction:number)=>{const span=view[1]-view[0],left=Math.round(Math.max(tile.window_start_0based,Math.min(tile.window_end_0based-span,view[0]+direction*span*.5)));setView([left,left+span]);};
 return <>{expressionContext&&<div className="agx-context-link"><Activity size={16}/><span>Measured context: <strong>{expressionContext}</strong> · {matches.length?'Matching source label; samples are not matched.':'No matching prediction label.'}</span>{matches.length>0&&<button onClick={()=>{changeScene(sceneKey(matches[0]));setLibrary(true);}}>Use this biosample</button>}</div>}
 <div className="agx-toolbar"><div className="agx-fixed-gene">{catalog.genes.filter(g=>g.tiles.length).length>1?<label>Linked gene<select aria-label="AlphaGenome linked gene" value={geneId} onChange={e=>changeGene(e.target.value)}>{catalog.genes.filter(g=>g.tiles.length).map(g=><option key={g.ensembl_gene_id} value={g.ensembl_gene_id}>{g.gene_symbol} · {g.ensembl_gene_id}</option>)}</select></label>:<><Dna size={18}/><strong>{gene.gene_symbol}</strong><span>{gene.ensembl_gene_id} · GRCh38</span></>}{gene.tiles.length>1&&<label>Model window<select aria-label="AlphaGenome model window" value={tile.tile_id} onChange={e=>{const next=gene.tiles.find(t=>t.tile_id===e.target.value)!;setTileId(next.tile_id);setView(initialView(gene,next));}}>{gene.tiles.map((t,i)=><option key={t.tile_id} value={t.tile_id}>{i+1} / {gene.tiles.length} · {location(t.window_start_0based,t.window_end_0based)}</option>)}</select></label>}</div><div className="agx-toolbar-actions"><button className="agx-icon-reset" title="Reset reference tracks and choose again" aria-label="Reset reference tracks and choose again" onClick={resetTracks}><RotateCcw size={16}/></button><button className="agx-primary" aria-expanded={library} onClick={()=>setLibrary(!library)}><Plus size={16}/>Add tracks</button></div></div>
 {library&&<div className="agx-library"><div className="agx-library-heading"><h4>Add reference tracks</h4><button aria-label="Close track library" onClick={()=>setLibrary(false)}><X size={17}/></button></div>
  <div className="agx-picker-controls">
   <label className="agx-selector"><span>Biosample</span><select aria-label="AlphaGenome biosample" data-selected={Boolean(scene)} value={scene} onChange={e=>changeScene(e.target.value)}><option value="" disabled>Select tissue or cell…</option>{biosamples.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}<option value="shared">Shared predictions · no biosample</option></select></label>
   <label className="agx-selector"><span>Modality</span><select aria-label="AlphaGenome modality" disabled={!scene} data-selected={Boolean(activeMode)} value={activeMode} onChange={e=>{setMode(e.target.value);setSearch('');}}>{!scene&&<option value="">Select biosample first</option>}{availableModes.map(id=><option key={id} value={id}>{modeInfo(id).label} · {counted(contextTracks.filter(t=>t.modality===id).length,'track')}</option>)}</select></label>
   <label className="agx-track-search"><span>Find signal</span><input aria-label="Search AlphaGenome tracks" disabled={!scene} value={search} onChange={e=>setSearch(e.target.value)} placeholder="Assay, mark or strand"/></label>
  </div>
  {scene?<div className="agx-library-results">{available.map(t=><div key={t.track_id} className="agx-candidate"><div><strong>{details(t)||t.name}</strong><span>{t.data_source||'Reference prediction'}</span></div><button className="agx-track-toggle" aria-pressed={selected.includes(t.track_id)} onClick={()=>add(t.track_id)} aria-label={`${selected.includes(t.track_id)?'Remove':'Add'} ${t.track_id}`}>{selected.includes(t.track_id)?<Check size={15}/>:<Plus size={15}/>} {selected.includes(t.track_id)?'Added':'Add'}</button></div>)}{!available.length&&<p>No matching signal.</p>}</div>:<p className="agx-selection-prompt">Select a biosample to browse its prediction tracks.</p>}
 </div>}

 <div className="agx-qtl-entry"><button aria-expanded={qtlLibrary} onClick={()=>setQtlLibrary(!qtlLibrary)}><Plus size={16}/>Add QTL</button><span>GTEx associations</span></div>{qtlLibrary&&<QtlPicker key={geneId} accession={accession} gene={geneId} selected={qtlSelected} onChange={setQtlSelected} onClose={()=>setQtlLibrary(false)}/>}
 <div className="agx-locus"><div><strong>{tile.chromosome}:{location(view[0],view[1])}</strong><span>{number(view[1]-view[0],0)} bp · GRCh38</span></div><div className="agx-viewport"><button className="agx-icon-reset" aria-label="Reset genomic view to gene region" title="Reset view to gene region" onClick={()=>{cancelBrush();setView(initialView(gene,tile));}}><RotateCcw size={15}/></button><button onClick={()=>setView(initialView(gene,tile))}>Gene region</button><button aria-label="Pan genomic window left" disabled={view[0]<=tile.window_start_0based} onClick={()=>pan(-1)}>←</button><button aria-label="Zoom in genomic window" onClick={()=>zoom(.5)} disabled={view[1]-view[0]<=32}><ZoomIn size={15}/></button><button aria-label="Zoom out genomic window" onClick={()=>zoom(2)} disabled={view[1]-view[0]>=tile.window_end_0based-tile.window_start_0based}><ZoomOut size={15}/></button><button aria-label="Pan genomic window right" disabled={view[1]>=tile.window_end_0based} onClick={()=>pan(1)}>→</button><button onClick={()=>setView([tile.window_start_0based,tile.window_end_0based])}>Full window</button></div></div>
 <p className="agx-axis-hint">Drag to zoom · scroll axis to pan · click an exon to focus</p>
 <div className="agx-stack" onPointerDownCapture={beginBrush} onPointerMoveCapture={moveBrush} onPointerUpCapture={endBrush} onPointerCancel={cancelBrush} onLostPointerCapture={()=>{if(drag.current)cancelBrush();}} onClickCapture={e=>{if(suppressClick.current){suppressClick.current=false;e.preventDefault();e.stopPropagation();}}} onKeyDownCapture={e=>{if(e.key==='Escape'){cancelBrush();e.preventDefault();}}}>{cdsQuery.error&&<div className="agx-error">MANE CDS could not be loaded.<button onClick={()=>cdsQuery.refetch()}>Retry CDS</button></div>}<GenomicAxis view={view} gene={gene} chromosome={tile.chromosome} position={position} hoverPosition={hoverPosition} onHover={setHoverPosition} brush={brush} cds={cdsQuery.data} canPan={viewSpan<windowSpan} onPan={panFraction} onFocusFeature={focusFeature}/><div className="agx-region-nav">
  {windowCds.length>0&&<label className="agx-exon-picker"><span className="agx-cds-nav-label">Explore CDS</span><select aria-label="Jump to MANE CDS exon" value="" onChange={e=>{const block=windowCds[Number(e.target.value)];if(block)focusFeature(block);}}><option value="" disabled>Jump to coding region…</option>{windowCds.map((b,i)=><option key={b.start_0based} value={i}>Exon {b.exon_number} · {location(b.start_0based,b.end_0based)}</option>)}</select></label>}
  <label className="agx-pan-picker"><span>Pan</span><input type="range" aria-label="Pan genomic region within model window" aria-valuetext={`${tile.chromosome}:${location(view[0],view[1])}`} title="Drag to browse the model window while keeping this zoom level" min={tile.window_start_0based} max={tile.window_end_0based-viewSpan} step={1} value={view[0]} disabled={viewSpan>=windowSpan} onChange={e=>{const start=Number(e.target.value);setHoverPosition(null);setView([start,start+viewSpan]);}}/><span className="agx-pan-hint">{viewSpan>=windowSpan?'Full window':'Drag to browse'}</span></label>
 </div><AviTrack accession={accession} gene={gene} tile={tile} view={view} position={position} hoverPosition={hoverPosition} onHover={setHoverPosition} brush={brush} onPosition={setPosition} onFocusVariant={focusVariant}/>{qtlSelected.map(d=><QtlTrack key={`${geneId}:${d.dataset_id}:${view.join(':')}`} accession={accession} gene={geneId} dataset={d} chromosome={tile.chromosome} view={view} hoverPosition={hoverPosition??position} onHover={setHoverPosition} onRemove={()=>{setHoverPosition(null);setQtlSelected(items=>items.filter(i=>i.dataset_id!==d.dataset_id));}}/>)}{panels.map((panel,index)=>{const t=panel.tracks[0],common={accession,gene,tile,view,position,hoverPosition,onHover:setHoverPosition,brush,index,total:panels.length,onRemove:()=>removeIds(panel.tracks.map(t=>t.track_id)),onMove:(delta:number)=>movePanel(index,delta)};return signalModality(t)?<SignalGroupCard key={`${geneId}:${tileId}:${panel.key}`} {...common} tracks={panel.tracks} catalogTracks={catalog.tracks} onRemoveSeries={id=>removeIds([id])}/>:<TrackCard key={`${geneId}:${tileId}:${panel.key}`} {...common} track={t}/>;})}</div><div className="agx-stack-heading"><span>{counted(selected.length,'signal')} · {counted(panels.length,'reference panel')} · {counted(qtlSelected.length,'QTL track')}</span><button aria-pressed={overlay} onClick={()=>setOverlay(!overlay)}>Overlay same modality</button>{selected.length>0&&<button onClick={()=>setSelected([])}><Trash2 size={13}/>Clear reference tracks</button>}<button onClick={()=>setLibrary(true)}><Plus size={14}/>Add track</button></div><p className="agx-footnote">GRCh38 · independent track scales</p></>;
}
export function AlphaGenomeExpression({accession,expressionContext=''}:{accession:string;expressionContext?:string}){
 const query=useQuery({queryKey:['expression-alphagenome',accession],queryFn:({signal})=>api<Catalog>(`/proteins/${accession}/expression/alphagenome`,signal),staleTime:300000,retry:1}),data=query.data;
 return <section id="alphagenome" className="agx" aria-label="AlphaGenome and AVI genomic tracks"><span id="expression-predictions" className="agx-legacy-anchor" aria-hidden="true"/><header className="agx-heading"><div><h2>AlphaGenome <span>& AVI</span> <HelpButton title="AlphaGenome & AVI guide" label="Guide"><AlphaGenomeGuide snapshot={data?.snapshot}/></HelpButton></h2><p>Reference predictions, variant scores and GTEx associations.</p></div></header>{data&&<div className="agx-stats"><span><b>{new Set(data.tracks.map(t=>t.ontology_curie).filter(Boolean)).size}</b> biosamples</span><span><b>{new Set(data.tracks.map(t=>t.modality)).size}</b> {new Set(data.tracks.map(t=>t.modality)).size===1?'modality':'modalities'}</span><span><b>{data.tracks.length.toLocaleString()}</b> reference {data.tracks.length===1?'track':'tracks'}</span></div>}{query.error?<div className="agx-error" role="alert">{query.error.message}<button onClick={()=>query.refetch()}>Retry predictions</button></div>:!data?<div className="agx-loading">Loading prediction contexts…</div>:!data.available||!data.genes.some(g=>g.tiles.length)?<div className="agx-empty"><strong>No reference prediction available for this gene.</strong>{data.genes.map(g=><span key={g.ensembl_gene_id}>{g.gene_symbol} · {(g.prediction_status??g.status??'not available').replaceAll('_',' ')}</span>)}</div>:<Workspace key={`${accession}:${data.snapshot}`} accession={accession} catalog={data} expressionContext={expressionContext}/>}</section>;
}
