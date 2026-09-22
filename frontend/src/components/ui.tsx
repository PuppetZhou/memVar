import { useEffect, useRef, useState, type ReactNode } from 'react';
import { AlertCircle, ChevronLeft, ChevronRight, ExternalLink, LoaderCircle, X } from 'lucide-react';
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from '@tanstack/react-table';
import { display, type RecordData } from '../api';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogTitle } from './ui/dialog';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { CollapseRegion, Reveal } from '@/lib/motion';
import { cn } from '@/lib/utils';

export function Badge({children,tone='neutral'}:{children:ReactNode;tone?:string}){return <span className={`badge badge-${tone}`}>{children}</span>;}
export function Status({loading,error,empty,children}:{loading?:boolean;error?:Error|null;empty?:boolean;children?:ReactNode}){
 if(loading)return <div className="state" role="status"><LoaderCircle className="spin" size={19}/> Loading data…</div>;
 if(error)return <div className="state error" role="alert"><AlertCircle size={19}/><span>{error.message}</span></div>;
 if(empty)return <div className="empty-state">No matching records are available in the current data release.</div>;
 return <>{children}</>;
}
export function Panel({id,title,subtitle,color='blue',icon,children,action}:{id:string;title:string;subtitle?:string;color?:string;icon?:ReactNode;children:ReactNode;action?:ReactNode}){return <section id={id} className={`panel accent-${color}`}><div className="section-heading"><div className="heading-icon">{icon}</div><div><h2>{title}</h2>{subtitle&&<p>{subtitle}</p>}</div>{action&&<div className="section-action">{action}</div>}</div>{children}</section>;}
export function Disclosure({title,children,open=false,className,onOpenChange}:{title:ReactNode;children:ReactNode;open?:boolean;className?:string;onOpenChange?:(open:boolean)=>void}){
 const [expanded,setExpanded]=useState(open);
 return <Collapsible className={cn('details',className)} open={expanded} onOpenChange={next=>{setExpanded(next);onOpenChange?.(next);}}>
   <CollapsibleTrigger className="details-trigger">{title}<ChevronRight size={15} aria-hidden="true"/></CollapsibleTrigger>
   <CollapsibleContent forceMount asChild><CollapseRegion open={expanded}><div className="details-content">{children}</div></CollapseRegion></CollapsibleContent>
 </Collapsible>;
}
export function LinkOut({href,children}:{href:unknown;children:ReactNode}){return typeof href==='string'&&/^https?:\/\//.test(href)?<a className="external-link" href={href} target="_blank" rel="noreferrer">{children}<ExternalLink size={12}/></a>:<>{children}</>;}
export function Fields({items}:{items:{label:string;value:unknown}[]}){return <dl className="field-grid">{items.filter(item=>item.value!==null&&item.value!==undefined&&item.value!=='').map((item,index)=><div key={`${item.label}-${index}`}><dt>{item.label}</dt><dd>{display(item.value)}</dd></div>)}</dl>;}
export function DataTable<T>({items,columns,onRowClick}:{items:T[];columns:ColumnDef<T>[];onRowClick?:(row:T)=>void}){const table=useReactTable({data:items,columns,getCoreRowModel:getCoreRowModel()});return <div className="table-wrap"><table className="data-table"><thead>{table.getHeaderGroups().map(group=><tr key={group.id}>{group.headers.map(header=><th key={header.id}>{header.isPlaceholder?null:flexRender(header.column.columnDef.header,header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map(row=><tr key={row.id} onClick={()=>onRowClick?.(row.original)} className={onRowClick?'clickable-row':undefined}>{row.getVisibleCells().map(cell=><td key={cell.id}>{flexRender(cell.column.columnDef.cell,cell.getContext())}</td>)}</tr>)}</tbody></table></div>;}
export function PageJump({page,onJump,totalPages,maxPage,loading=false,label='Go to page'}:{page:number;onJump:(page:number)=>void;totalPages?:number;maxPage?:number;loading?:boolean;label?:string}){
 const [draft,setDraft]=useState('');
 useEffect(()=>setDraft(''),[page]);
 const target=Number(draft),maximum=totalPages==null?undefined:Math.max(1,totalPages),inputMax=maxPage==null?maximum:Math.min(maxPage+1,maximum??Infinity);
 const valid=draft.trim()!==''&&Number.isSafeInteger(target)&&target>=1&&(inputMax==null||target<=inputMax);
 return <form className="page-jump" onSubmit={event=>{event.preventDefault();if(valid&&!loading){onJump(target-1);setDraft('');}}}><label>Go to page<input aria-label={label} type="number" min="1" max={inputMax} step="1" value={draft} disabled={loading} placeholder={String(page+1)} onChange={event=>setDraft(event.target.value)}/></label>{maximum!=null&&<span>of {maximum.toLocaleString()}</span>}<Button variant="outline" size="sm" type="submit" disabled={!valid||loading}>Go</Button></form>;
}
export function Pager({page,count,next,onPrevious,onNext,onJump,totalPages,maxPage,loading}:{page:number;count:number;next?:string|null;onPrevious:()=>void;onNext:()=>void;onJump?:(page:number)=>void;totalPages?:number;maxPage?:number;loading?:boolean}){if(!loading&&page===0&&!next)return <div className="pagination pagination-summary"><span aria-live="polite">{count} records</span></div>;return <div className="pagination"><span aria-live="polite">Page {page+1} · {count} records</span><div><Button variant="outline" size="sm" disabled={page===0||loading} onClick={onPrevious}><ChevronLeft data-icon="inline-start"/>Previous</Button><Button variant="outline" size="sm" disabled={!next||loading} onClick={onNext}>Next<ChevronRight data-icon="inline-end"/></Button></div>{onJump&&<PageJump page={page} onJump={onJump} totalPages={totalPages} maxPage={maxPage} loading={loading}/>}</div>;}
export function Modal({title,onClose,children,closeRequested=false}:{title:string;onClose:()=>void;children:ReactNode;closeRequested?:boolean}){
 const activeElement=document.activeElement;
 const opener=useRef<HTMLElement|SVGElement|null>(activeElement instanceof HTMLElement||activeElement instanceof SVGElement?activeElement:null);
 const [open,setOpen]=useState(true);
 const closing=useRef(false);
 const latestOnClose=useRef(onClose);
 latestOnClose.current=onClose;
 const requestClose=()=>{if(!closing.current){closing.current=true;setOpen(false);}};
 useEffect(()=>{if(closeRequested){closing.current=true;setOpen(false);}},[closeRequested]);
 return <Dialog open={open} onOpenChange={next=>{if(!next)requestClose();}}><DialogContent
   aria-describedby={undefined} showCloseButton={false}
   className="w-[96vw] max-w-[1180px] sm:max-w-[1180px] max-h-[90vh] grid-rows-[auto_minmax(0,1fr)] gap-0 p-0"
   onCloseAutoFocus={event=>{
     event.preventDefault();
     // Radix calls this after the exit animation and focus-scope teardown. Keep
     // conditional parent callers mounted until then; do not steal another dialog's focus.
     if(opener.current?.isConnected&&!document.activeElement?.closest('[role="dialog"]'))opener.current.focus({preventScroll:true});
     if(closing.current){closing.current=false;latestOnClose.current();}
   }}>
   <div className="dialog-heading"><DialogTitle>{title}</DialogTitle><Button variant="ghost" size="icon" onClick={requestClose} aria-label="Close details"><X/></Button></div>
   <div className="dialog-body overflow-auto"><Reveal>{children}</Reveal></div>
 </DialogContent></Dialog>;
}
export function DetailFields({items}:{items:unknown}){if(!Array.isArray(items))return null;return <Fields items={items.map((item:RecordData)=>({label:display(item.label),value:item.value}))}/>;}
export function SelectFilter({label:labelText,value,onChange,options,all='All',allowAll=true}:{label:string;value:string;onChange:(value:string)=>void;options?:unknown[];all?:string;allowAll?:boolean}){
 const choices=(options??[]).map(option=>{const item=typeof option==='object'&&option?option as RecordData:{value:option,label:option};return {value:String(item.value??item.name??''),label:String(item.label??item.value??item.name??'').replaceAll('_',' ')};});
 if(value&&!choices.some(option=>option.value===value))choices.unshift({value,label:value.replaceAll('_',' ')});
 return <label className="filter"><span>{labelText}</span><select value={value} onChange={e=>onChange(e.target.value)}>{allowAll&&<option value="">{all}</option>}{choices.map(option=><option key={option.value} value={option.value}>{option.label}</option>)}</select></label>;
}
