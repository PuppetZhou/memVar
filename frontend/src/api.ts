export class ApiError extends Error { constructor(public status:number,message:string){super(message);} }
export async function api<T>(path:string,signal?:AbortSignal):Promise<T>{
  const response=await fetch(`/api${path}`,{signal,headers:{Accept:'application/json'}});
  if(!response.ok){let message=`The request could not be completed (${response.status}).`;try{const body=await response.json();if(typeof body.detail==='string')message=body.detail;}catch{/* Non-JSON proxy errors keep the status. */}throw new ApiError(response.status,message);}
  return response.json() as Promise<T>;
}
export function params(values:Record<string,string|number|undefined|null>){const search=new URLSearchParams();for(const [key,value]of Object.entries(values))if(value!==undefined&&value!==null&&value!=='')search.set(key,String(value));return search.toString();}
export type RecordData=Record<string,unknown>;
export type FilterOption=string|{value:string;label?:string;count?:number};
export interface Page<T=RecordData>{items:T[];next_cursor:string|null;filters?:Record<string,FilterOption[]>;status?:string;note?:string;gene_dosage?:RecordData[];}
export function display(value:unknown):string{
  if(value===null||value===undefined||value==='')return 'Not available';
  if(typeof value==='boolean')return value?'Yes':'No';
  if(Array.isArray(value))return value.length?value.map(display).join(' · '):'Not available';
  if(typeof value==='object'){const obj=value as RecordData;return display(obj.name??obj.label??obj.text??obj.term??obj.value??obj.id??obj.accession??null);}
  const string=String(value);
  if(['{}','[]','.'].includes(string.trim()))return 'Not available';
  if(/%3D/i.test(string)){try{return decodeURIComponent(string);}catch{return string;}}
  return string;
}
export function number(value:unknown,digits=3){if(value===null||value===undefined||value==='')return '—';const n=Number(value);if(!Number.isFinite(n))return display(value);if(n!==0&&Math.abs(n)<0.001)return n.toExponential(2);return n.toLocaleString('en-US',{maximumFractionDigits:digits});}
export function label(value:unknown){return display(value).replaceAll('_',' ');}
