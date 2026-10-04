import { Link } from 'react-router-dom';
import { number } from '../api';
import { interpolateColor } from '../lib/palette';
import { ModeToggleGroup } from './ui/mode-toggle-group';
import './structure-predictor.css';

export type PredictorFamily = 'AlphaMissense'|'ESM1b'|'ThermoMPNN'|'AlphaGenome';
export type PredictorRecord = {variant_id:string;annotation_id:string;gene_id:string;transcript_id:string;prediction_id:number;sequence_id:string;position:number;ref_aa:string;alt_aa:string;score:number};
export type PredictorSite = {position:number;score:number|null;status:'scored'|'no_finite_score'|'opposite_sign_tie';extreme_values:number[];records:PredictorRecord[];scored_variant_count:number;scored_substitution_count:number;scored_annotation_count:number};
export type PredictorExtrema = {field:string;label:string;unit:string;rule:string;rule_label:string;sites:PredictorSite[];scored_positions:number;mapped_positions:number;scale:{min:number;max:number;note:string};note:string;tie_note:string};
export const alphaGenomeFields = [
  {value:'alphagenome_avi_raw',label:'AVI raw'},
  {value:'alphagenome_avi_phred',label:'AVI PHRED'},
  {value:'alphagenome_splicing',label:'Merged splicing'},
];
export function structurePredictorField(family:PredictorFamily, alphaField:string){
  return family==='AlphaGenome'?alphaField:family==='ThermoMPNN'?'ThermoMPNN_ddg':family==='ESM1b'?'ESM1b_score':'AlphaMissense_score';
}
export const predictorTieColor='#8064ad';
const LOW='#2774ac',MID='#f2eee8',HIGH='#c73748';
export function structurePredictorColor(score:number, data:PredictorExtrema){
  const {min,max}=data.scale;
  let t=Math.max(0,Math.min(1,(score-min)/(max-min||1)));
  if(data.rule==='minimum')t=1-t;
  return t<=.5?interpolateColor(LOW,MID,t*2):interpolateColor(MID,HIGH,(t-.5)*2);
}
export function StructurePredictorControls({family,onFamily,alphaField,onAlphaField,data,loading,error,onRetry}:{family:PredictorFamily;onFamily:(value:PredictorFamily)=>void;alphaField:string;onAlphaField:(value:string)=>void;data?:PredictorExtrema;loading:boolean;error:Error|null;onRetry:()=>void}){
  return <div className="structure-predictor-controls">
    <div className="structure-predictor-choice"><strong>Predictor</strong><ModeToggleGroup aria-label="Structure predictor model" value={family} onValueChange={value=>onFamily(value as PredictorFamily)} options={(['AlphaMissense','ESM1b','ThermoMPNN','AlphaGenome'] as const).map(value=>({value,label:value==='ESM1b'?'ESM1b (ESM)':value}))}/>
    {family==='AlphaGenome'&&<label>Score<select aria-label="AlphaGenome structure score" value={alphaField} onChange={event=>onAlphaField(event.target.value)}>{alphaGenomeFields.map(option=><option key={option.value} value={option.value}>{option.label}</option>)}</select></label>}</div>
    {loading?<p role="status">Loading predictor extrema…</p>:error?<p role="alert">Predictor scores unavailable. <button className="text-button" onClick={onRetry}>Retry scores</button></p>:data&&<>
      <p><strong>{data.rule_label}</strong><span>{data.scored_positions.toLocaleString()} canonical positions with scores · shown where this structure has mapped residues.</span></p>
      {!data.scored_positions&&<p className="empty-state">No mapped scores for this model on the current canonical sequence. Unscored residues remain gray.</p>}
      <details><summary>Scope &amp; interpretation</summary><p>{data.note}</p><p>{data.tie_note}</p><p>AlphaGenome values refer to DNA-variant effects on predicted genomic function; they are not protein stability scores. No clinical classification is inferred from these colors.</p></details>
    </>}
  </div>;
}
export function StructurePredictorLegend({data}:{data:PredictorExtrema}){
  if(!data.scored_positions)return <div className="structure-predictor-legend"><strong>{data.label}</strong><p>No finite mapped scores to define a color scale.</p></div>;
  const stability=data.rule==='signed_absolute_maximum';
  const left=data.rule==='minimum'?HIGH:LOW,right=data.rule==='minimum'?LOW:HIGH;
  return <div className="structure-predictor-legend">
    <strong>{data.label} · {data.unit}</strong>
    <div className="structure-predictor-scale" role="img" aria-label={`${data.label} color scale: ${data.scale.min} to ${data.scale.max} ${data.unit}`}>
      <span>{number(data.scale.min,3)}<small>{stability?'Stabilizing':data.rule==='minimum'?'Stronger effect':'Lower effect'}</small></span>
      <i style={{background:`linear-gradient(90deg,${left},${MID},${right})`}}/>
      <span>{number(data.scale.max,3)}<small>{stability?'Destabilizing':data.rule==='minimum'?'Lower effect':'Stronger effect'}</small></span>
      {stability&&<span className="structure-predictor-zero">0 · no predicted change</span>}
    </div>
    <p>{data.scale.note}</p>
    {data.sites.some(site=>site.status==='opposite_sign_tie')&&<span><b style={{background:predictorTieColor}}/>Opposite-sign extrema tied · inspect residue</span>}
  </div>;
}
export function StructurePredictorSite({data,site,accession,loading}:{data?:PredictorExtrema;site?:PredictorSite;accession:string;loading:boolean}){
  return <section className="structure-predictor-site" aria-label="Residue predictor extremum">
    {loading?<p>Loading predictor score…</p>:!data?<p>Predictor data unavailable.</p>:<>
      <header><strong>{data.label}</strong><span>{data.rule==='minimum'?'Minimum':data.rule==='signed_absolute_maximum'?'Largest |ΔΔG|':'Maximum'}</span></header>
      {!site?.extreme_values.length?<p>No mapped finite score at this residue.</p>:<>
        <p className="structure-predictor-value">{site.extreme_values.map(value=>number(value,4)).join(' / ')} <small>{data.unit}</small></p>
        {site.status==='opposite_sign_tie'&&<p>Equal magnitude, opposite signs. No single direction selected.</p>}
        <p>{site.scored_variant_count} scored DNA variants · {site.scored_substitution_count} substitutions</p>
        <details open><summary>Substitutions producing this extremum ({site.records.length})</summary><div className="structure-predictor-records">{site.records.map((record,i)=><article key={`${record.annotation_id}:${record.gene_id}:${record.prediction_id}:${i}`}>
          <Link to={`/protein/${accession}?variants_search=${encodeURIComponent(record.variant_id)}&variants_predictors=${encodeURIComponent(data.field)}#variants`}>{record.ref_aa}{record.position}{record.alt_aa} · {number(record.score,4)}</Link>
          <small>{record.variant_id} · {record.transcript_id}</small>
        </article>)}</div></details>
      </>}
    </>}
  </section>;
}
