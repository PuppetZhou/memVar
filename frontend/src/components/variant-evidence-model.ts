import { label, number, type RecordData } from '../api';
export interface Predictor extends RecordData {
  field: string; tool: string; group?: string; scope?: string; value?: unknown;
  source_pred?: string | null; source_pred_label?: string | null;
  source_pred_effect?: string | null; source_pred_status?: string | null;
}
// Native 0–1 scales checked against the current source dictionary; no rank conversion.
export const DBNSFP_COLUMNS='https://dist.genos.us/release/dbNSFP5.4a_variant.columns.txt';
const HIGHER_EFFECT='Higher original scores indicate a greater predicted damaging effect.';
const HIGHER_PATHOGENICITY='Higher original scores indicate greater predicted pathogenicity.';
const LOWER_EFFECT='Lower original scores indicate a greater predicted damaging effect.';
export const SCORE_SCALES:Record<string,{direction:string;url:string}>={
  SIFT_score:{direction:LOWER_EFFECT,url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC3394338/'},
  SIFT4G_score:{direction:LOWER_EFFECT,url:DBNSFP_COLUMNS},
  Polyphen2_HDIV_score:{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  Polyphen2_HVAR_score:{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  VEST4_score:{direction:'Higher original scores indicate a greater predicted functional change.',url:DBNSFP_COLUMNS},
  MetaLR_score:{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  MetaRNN_score:{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  'M-CAP_score':{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  REVEL_score:{direction:HIGHER_PATHOGENICITY,url:'https://sites.google.com/site/revelgenomics/'},
  MutPred2_score:{direction:HIGHER_EFFECT,url:'https://mutpred.mutdb.org/help.html'},
  MVP_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  gMVP_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  MisFit_D_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  PrimateAI_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  DEOGEN2_score:{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  ClinPred_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  'LIST-S2_score':{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  VARITY_R_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  VARITY_ER_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  VARITY_R_LOO_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  VARITY_ER_LOO_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  AlphaMissense_score:{direction:HIGHER_PATHOGENICITY,url:'https://deepmind.google/blog/a-catalogue-of-genetic-mutations-to-help-pinpoint-the-cause-of-diseases/'},
  PHACTboost_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  MutFormer_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  MutScore_score:{direction:HIGHER_PATHOGENICITY,url:DBNSFP_COLUMNS},
  DANN_score:{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  'fathmm-XF_coding_score':{direction:HIGHER_EFFECT,url:DBNSFP_COLUMNS},
  phastCons100way_vertebrate:{direction:'Higher original scores indicate greater sequence conservation, not a clinical classification.',url:DBNSFP_COLUMNS},
  phastCons470way_mammalian:{direction:'Higher original scores indicate greater sequence conservation, not a clinical classification.',url:DBNSFP_COLUMNS},
  phastCons17way_primate:{direction:'Higher original scores indicate greater sequence conservation, not a clinical classification.',url:DBNSFP_COLUMNS},
  Aloft_prob_Tolerant:{direction:'Original ALoFT probability for its tolerant class.',url:DBNSFP_COLUMNS},
  Aloft_prob_Recessive:{direction:'Original ALoFT probability for its recessive disease-causing class.',url:DBNSFP_COLUMNS},
  Aloft_prob_Dominant:{direction:'Original ALoFT probability for its dominant disease-causing class.',url:DBNSFP_COLUMNS},
  Aloft_Fraction_transcripts_affected:{direction:'Fraction of gene transcripts affected; not a pathogenicity probability.',url:DBNSFP_COLUMNS},
};
type SourceCall={label:string;tone:'damaging'|'tolerated'|'uncertain'};
const DAMAGING:SourceCall={label:'Damaging',tone:'damaging'};
const TOLERATED:SourceCall={label:'Tolerated',tone:'tolerated'};
const NEUTRAL:SourceCall={label:'Neutral',tone:'tolerated'};
const DT_CALLS={D:DAMAGING,T:TOLERATED};
const POLYPHEN_CALLS:Record<string,SourceCall>={D:{label:'Probably damaging',tone:'damaging'},P:{label:'Possibly damaging',tone:'uncertain'},B:{label:'Benign',tone:'tolerated'}};
// Interpret only an existing, matched source call. Never derive calls from score cutoffs.
const SOURCE_CALLS:Record<string,Record<string,SourceCall>>={
  SIFT_score:DT_CALLS,SIFT4G_score:DT_CALLS,MetaSVM_score:DT_CALLS,MetaLR_score:DT_CALLS,MetaRNN_score:DT_CALLS,
  'M-CAP_score':DT_CALLS,PrimateAI_score:DT_CALLS,DEOGEN2_score:DT_CALLS,ClinPred_score:DT_CALLS,'LIST-S2_score':DT_CALLS,
  BayesDel_addAF_score:DT_CALLS,BayesDel_noAF_score:DT_CALLS,
  Polyphen2_HDIV_score:POLYPHEN_CALLS,Polyphen2_HVAR_score:POLYPHEN_CALLS,
  PROVEAN_score:{D:DAMAGING,N:NEUTRAL},'fathmm-XF_coding_score':{D:DAMAGING,N:NEUTRAL},
  AlphaMissense_score:{P:{label:'Likely pathogenic',tone:'damaging'},A:{label:'Ambiguous',tone:'uncertain'},B:{label:'Likely benign',tone:'tolerated'}},
  MutPred2_score:{PS:{label:'Strong pathogenic evidence',tone:'damaging'},PM:{label:'Moderate pathogenic evidence',tone:'damaging'},PP:{label:'Supporting pathogenic evidence',tone:'damaging'},UC:{label:'Uncertain',tone:'uncertain'},BP:{label:'Supporting benign evidence',tone:'tolerated'},BM:{label:'Moderate benign evidence',tone:'tolerated'},BS:{label:'Strong benign evidence',tone:'tolerated'}},
};
export function sourceCall(pred:Predictor){return pred.source_pred&&pred.source_pred_status==='matched_source_category'?SOURCE_CALLS[pred.field]?.[pred.source_pred]:undefined;}

export function record(value:unknown):RecordData{return value&&typeof value==='object'&&!Array.isArray(value)?value as RecordData:{};}
export function records(value:unknown):RecordData[]{return Array.isArray(value)?value.filter(x=>x&&typeof x==='object') as RecordData[]:[];}
export function missing(value:unknown){return value===null||value===undefined||value===''||value==='.';}
export function clinicalTone(value:unknown):string{
  // Keep display grouping in step with variant_support.clinical_display_group.
  const text=String(value??'').replaceAll('_',' ').trim().toLowerCase().replace(/\s+/g,' ');
  if(!text||['-','.','na','not provided','not specified','none'].includes(text))return 'unclassified';
  if(text.includes('conflict'))return 'conflicting';
  const tokens=new Set(text.split(/[/;,]/).map(token=>token.trim()));
  const classes=[
    {name:'pathogenic',terms:['pathogenic','likely pathogenic']},
    {name:'benign',terms:['benign','likely benign']},
    {name:'uncertain',terms:['uncertain significance']},
  ].filter(group=>group.terms.some(term=>tokens.has(term)));
  return classes.length>1?'conflicting':classes[0]?.name??'other';
}
export function predTone(pred:Predictor){
  const original=sourceCall(pred);if(original)return original.tone;
  if(pred.source_pred_status!=='matched_source_category')return 'other';
  const text=String(pred.source_pred_label??pred.source_pred??'').replaceAll('_',' ').trim().toLowerCase().replace(/\s+/g,' ');
  if(['possibly damaging','uncertain significance','uncertain','ambiguous','unknown'].includes(text))return 'uncertain';
  if(['probably damaging','damaging','deleterious','disease causing','pathogenic','likely pathogenic'].includes(text))return 'damaging';
  if(['tolerated','benign','likely benign','neutral','polymorphism','polymorphism automatic'].includes(text))return 'tolerated';
  return 'other'; // Unrecognized text and single-letter codes remain uninterpreted.
}

export function clinicalLabel(value:unknown){return value==='-'?"Not classified (source ‘-’)":label(value);}
export function afPercent(value:unknown){
  if(missing(value))return '—';
  const af=Number(value);if(!Number.isFinite(af)||af<0||af>1)return 'Invalid AF';
  return `${number(af*100,4)}%`;
}
export function consequenceCategory(term:string){
  if(term==='missense_variant')return 'missense';
  if(term==='stop_gained')return 'stop-gained';
  if(term==='start_lost')return 'start-lost';
  if(term==='stop_lost')return 'stop-lost';
  if(term==='synonymous_variant')return 'synonymous';
  if(term.startsWith('splice_'))return 'splice';
  if(term==='frameshift_variant')return 'frameshift';
  if(term.startsWith('inframe_'))return 'inframe';
  return 'other';
}
export const CONSEQUENCE_COLOURS:Record<string,string>={missense:'#ef9a16','stop-gained':'#d94a68','start-lost':'#d97724','stop-lost':'#b55a36',synonymous:'#159b9b',splice:'#7f56d9',frameshift:'#c5488c',inframe:'#3975d8',other:'#667b96'};

// Presentation mappings only: preserve source labels and never derive a clinical call.
export function reviewStars(value:unknown):number|null {
 const normalized=String(value??'').toLowerCase().replaceAll('_',' ').replace(/\s*,\s*/g,', ').replace(/\s+/g,' ').trim();
 const statuses:Record<string,number>={'practice guideline':4,'reviewed by expert panel':3,'criteria provided, multiple submitters, no conflicts':2,'criteria provided, multiple submitters':2,'criteria provided, conflicting classifications':1,'criteria provided, conflicting interpretations':1,'criteria provided, single submitter':1,'no assertion criteria provided':0,'no classification provided':0,'no assertion provided':0,'no classification for the individual variant':0,'no assertion for the individual variant':0};
 return statuses[normalized]??null;
}
export function frequencyStyle(value:unknown){
 if(missing(value))return {color:'#94a3b8',progress:0,valid:false,zero:false};
 const af=Number(value);if(!Number.isFinite(af)||af<0||af>1)return {color:'#94a3b8',progress:0,valid:false,zero:false};
 if(af===0)return {color:'#64748b',progress:0,valid:true,zero:true};
 const t=Math.max(0,Math.min(1,(Math.log10(af)+6)/6));
 return {color:`hsl(${270-105*t} 70% 43%)`,progress:t*100,valid:true,zero:false};
}
export function scoreVisual(item:Predictor){
 const tone=predTone(item),scale=SCORE_SCALES[item.field],v=Number(item.value);
 const categorical:Record<string,string>={damaging:'#e43562',tolerated:'#08996c',uncertain:'#d28b08'};
 if(categorical[tone])return {color:categorical[tone],caption:'Color follows the original source call'};
 const valid=!missing(item.value)&&scale&&Number.isFinite(v)&&v>=0&&v<=1;
 if(!valid)return {color:'#3879bc',caption:'Original score; no matched source call'};
 const directional=/predicted damaging effect|predicted pathogenicity|predicted functional change/.test(scale.direction);
 if(!directional)return {color:`hsl(218 75% ${65-v*30}%)`,caption:'Color intensity follows this native score, not pathogenicity'};
 const effect=scale.direction.startsWith('Lower')?1-v:v;
 return {color:`hsl(${165*(1-effect)} 72% 40%)`,caption:`Continuous score tint. ${scale.direction} No categorical call is inferred.`};
}
export function sourceFieldMap(row:RecordData){return Object.fromEntries(records(row.fields).map(f=>[String(f.label),f.value]));}
export function decodedHGVS(value:unknown){try{return decodeURIComponent(String(value??'')).split(':').at(-1)||'—';}catch{return String(value??'—');}}
