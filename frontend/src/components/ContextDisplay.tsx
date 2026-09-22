import type { CSSProperties } from 'react';
import { ArrowDown, ArrowUp, ArrowRight, CircleHelp, Minus, Ban, Plus, Database, Dna, Orbit, Layers, CircleDot, FlaskConical, Microscope, Check, ShieldCheck, ShieldQuestion, CircleDashed, Ban as RefutedIcon } from 'lucide-react';
import { display, label, number, type RecordData } from '../api';
import { Disclosure, LinkOut, PageJump } from './ui';
import { ModeToggleGroup } from './ui/mode-toggle-group';
import { ContentTransition } from '../lib/motion';
import './context-detail.css';
import './expression-assay.css';

export function ContextPages({offset,limit,total,disabled,onChange}:{offset:number;limit:number;total:number;disabled:boolean;onChange:(offset:number)=>void}){
 const count=Math.ceil(total/limit),current=Math.floor(offset/limit)+1;
 const start=Math.max(1,Math.min(current-2,count-4));const pages=count<=7?Array.from({length:count},(_,i)=>i+1):[...new Set([1,count,...Array.from({length:5},(_,i)=>start+i)])].sort((a,b)=>a-b);
 return <nav className="cx-numbered-pages" aria-label="Expression context pages"><span>{total?`${offset+1}–${Math.min(offset+limit,total)} of ${number(total,0)} contexts`:'0 contexts'}</span><div><button disabled={disabled||current<=1} aria-label="Previous context page" onClick={()=>onChange(offset-limit)}>‹</button>{pages.map((page,i)=><span key={page}>{i>0&&page-pages[i-1]>1&&<i>…</i>}<button disabled={disabled} aria-label={`Context page ${page}`} aria-current={current===page?'page':undefined} onClick={()=>onChange((page-1)*limit)}>{page}</button></span>)}<button disabled={disabled||current>=count} aria-label="Next context page" onClick={()=>onChange(offset+limit)}>›</button></div><PageJump page={current-1} onJump={page=>onChange(page*limit)} totalPages={count} loading={disabled} label="Go to context page"/></nav>;
}

type Assay={name:string;target:string;description:string;color:string};
export const ASSAYS:Record<string,Assay>={
 rna:{name:'Bulk RNA-seq',target:'RNA',description:'RNA abundance in tissues, cancer samples and cell lines.',color:'#2775cd'},
 single:{name:'Single-cell RNA-seq',target:'RNA',description:'Single-cell / single-nucleus RNA grouped by cell type or cluster.',color:'#7e58c9'},
 cage:{name:'CAGE',target:'RNA',description:'FANTOM transcription-start tags; tags per million.',color:'#c18323'},
 ms:{name:'Mass spectrometry',target:'Protein',description:'Protein intensity or source-specific protein fold change; includes DVP.',color:'#0a958c'},
 ihc:{name:'Immunohistochemistry',target:'Protein',description:'Antibody staining levels or counts by staining category.',color:'#cd5985'},
};
const DATASET_ASSAYS:Record<string,string>={gtex_gene_median_tpm:'rna',rna_tissue_hpa:'rna',rna_cancer_sample:'rna',rna_celline:'rna',rna_cell_line_cancer:'rna',rna_single_cell_type:'single',rna_single_cell_cluster:'single',rna_tissue_fantom:'cage',ms_tissue_sample_data:'ms',cancer_cptac:'ms',dvp_cell_type:'ms',dvp_cell_type_group_data:'ms',normal_ihc_data:'ihc',cancer_data:'ihc'};
export function assayFor(dataset:string){return ASSAYS[DATASET_ASSAYS[dataset]];}
export function AssayBadge({dataset}:{dataset:string}){const assay=assayFor(dataset);return assay?<span className="cx-assay-badge" style={{color:assay.color,borderColor:assay.color+'40',background:assay.color+'0c'}}>{assay.target} · {assay.name}</span>:null;}
// Source collection labels organize navigation; they do not harmonize contexts or units.
const EXPRESSION_COLLECTIONS:Record<string,{context:string;detail:string;icon:typeof Layers}>={
 gtex_gene_median_tpm:{context:'Tissue & cell groups',detail:'Source median RNA expression across tissue, cultured-cell and microdissection groups.',icon:Layers},
 rna_tissue_hpa:{context:'Normal tissues',detail:'HPA gene RNA expression across normal tissues.',icon:Layers},
 rna_tissue_fantom:{context:'Normal tissues · CAGE',detail:'FANTOM transcription-start tag expression across normal tissues.',icon:Layers},
 rna_cancer_sample:{context:'Cancer samples',detail:'Individual cancer sample RNA values, grouped by cancer type.',icon:Microscope},
 rna_celline:{context:'Individual cell lines',detail:'RNA expression in individual cultured cell lines.',icon:FlaskConical},
 rna_cell_line_cancer:{context:'Cell lines by cancer type',detail:'Source RNA summaries of cell lines grouped by cancer type.',icon:FlaskConical},
 rna_single_cell_type:{context:'Single cell types',detail:'Source RNA profiles integrated by annotated cell type.',icon:CircleDot},
 rna_single_cell_cluster:{context:'Single cell clusters',detail:'RNA profiles of annotated cell clusters, grouped by tissue.',icon:CircleDot},
 normal_ihc_data:{context:'Normal tissue staining',detail:'Antibody staining categories in normal tissue cell types.',icon:Microscope},
 cancer_data:{context:'Cancer tissue staining',detail:'Source staining-category counts by cancer type.',icon:Microscope},
 ms_tissue_sample_data:{context:'Normal tissue proteomics',detail:'Mass-spectrometry protein intensities in tissue samples.',icon:Layers},
 cancer_cptac:{context:'Cancer proteomics',detail:'CPTAC source protein log fold changes by cancer type.',icon:Microscope},
 dvp_cell_type:{context:'Cell type proteomics · DVP',detail:'Deep Visual Proteomics protein intensities by cell type.',icon:CircleDot},
 dvp_cell_type_group_data:{context:'Cell type groups · DVP',detail:'Deep Visual Proteomics source protein summaries by cell type group.',icon:CircleDot},
};
export function expressionCollectionFor(dataset:string){return EXPRESSION_COLLECTIONS[dataset]??{context:label(dataset),detail:'Original source collection.',icon:Database};}
const EXPRESSION_SOURCE_TONES:Record<string,string>={GTEx:'teal',HPA:'violet',FANTOM:'amber',CPTAC:'pink'};
const SOURCE_NAMES:Record<string,string>={GTEx:'Genotype-Tissue Expression',HPA:'Human Protein Atlas',FANTOM:'FANTOM5 · via HPA',CPTAC:'Cancer proteomics · via HPA'};
interface AssayCollection {dataset?:string;key:string;count:number|null;source?:string;measurement?:string;measurement_unit?:string;filter?:Record<string,string>;}
export function AssayOverview({datasets,selectedDataset,onChooseDataset}:{datasets:AssayCollection[];selectedDataset:string;onChooseDataset:(dataset:AssayCollection)=>void}){
 const selectedTarget=assayFor(selectedDataset)?.target??'RNA';
 const selectedCollections=datasets.filter(collection=>assayFor(collection.dataset??collection.key)?.target===selectedTarget);
 const sources=[...new Set(selectedCollections.map(collection=>collection.source??collection.filter?.source??'Source'))];
 return <section className="cx-assay-overview">
  <header><h3>Explore expression data</h3><p>Choose <strong>RNA</strong> or <strong>protein</strong>, then a database and the tissue, cell or cancer context measured.</p></header>
  <ModeToggleGroup className="cx-expression-types" aria-label="Expression data type" value={selectedTarget} onValueChange={target=>{const next=datasets.find(collection=>assayFor(collection.dataset??collection.key)?.target===target);if(next)onChooseDataset(next);}} options={[
   {value:'RNA',label:<><span className="cx-expression-type-icon" data-kind="rna"><Dna size={16}/></span>RNA measurements</>,disabled:!datasets.some(collection=>assayFor(collection.dataset??collection.key)?.target==='RNA')},
   {value:'Protein',label:<><span className="cx-expression-type-icon" data-kind="protein"><Orbit size={16}/></span>Protein measurements</>,disabled:!datasets.some(collection=>assayFor(collection.dataset??collection.key)?.target==='Protein')},
  ]}/>
  <ContentTransition transitionKey={selectedTarget} className="cx-expression-sources">
   {sources.map(source=><div className="cx-expression-source" key={source} style={{'--expression-source':`var(--${EXPRESSION_SOURCE_TONES[source]??'slate'}-11)`,'--expression-source-soft':`var(--${EXPRESSION_SOURCE_TONES[source]??'slate'}-3)`} as CSSProperties}>
    <div className="cx-expression-database"><Database size={16}/><div><strong>{source}</strong><small>{SOURCE_NAMES[source]??'Source database'}</small></div></div>
    <div className="cx-expression-collections" role="group" aria-label={`${source} ${selectedTarget} contexts`}>
     {selectedCollections.filter(collection=>(collection.source??collection.filter?.source??'Source')===source).map(collection=>{
      const key=collection.dataset??collection.key,descriptor=expressionCollectionFor(key),Icon=descriptor.icon,selected=key===selectedDataset,assay=assayFor(key);
      return <button type="button" key={key} className={selected?'is-selected':''} aria-pressed={selected} aria-label={`${source}: ${descriptor.context}`} onClick={()=>onChooseDataset(collection)} title={descriptor.detail} style={{'--expression-assay':assay?.color??'var(--slate-11)'} as CSSProperties}>
       <span className="cx-expression-collection-icon"><Icon size={17}/></span><span><strong>{descriptor.context}</strong><small><span className="cx-expression-method">{assay?.name}</span> · {number(collection.count,0)} records</small></span>{selected?<Check size={14} aria-hidden="true"/>:<ArrowRight size={14} aria-hidden="true"/>}
      </button>;
     })}
    </div>
   </div>)}
  </ContentTransition>
  <Disclosure title="How to read measurements & units" className="cx-expression-unit-guide">
   <div className="cx-expression-unit-notes"><p><strong>RNA:</strong> GTEx values here are source-provided group medians in TPM. HPA <strong>pTPM</strong> rescales protein-coding transcript abundance to one million per sample; <strong>nTPM</strong> adds TMM normalization for comparisons between samples. Both measure RNA, with different normalization.</p><p>HPA single-cell <strong>nCPM</strong> uses TMM-normalized protein-coding counts per million; FANTOM CAGE uses transcription-start tags per million. These retain separate scales.</p><p><strong>Protein:</strong> mass spectrometry reports source intensity or log fold change; antibody staining reports qualitative levels or category counts. These are separate measurements, not interchangeable protein quantities.</p><p>Each chart compares one collection and unit. Record counts describe coverage. Original values, missing states and source details remain available.</p><div><LinkOut href="https://www.proteinatlas.org/humanproteome/tissue/method/transcriptomics">HPA RNA methods</LinkOut><LinkOut href="https://www.proteinatlas.org/humanproteome/single%2Bcell/single%2Bcell%2Btype/method">HPA single-cell methods</LinkOut><LinkOut href="https://gtexportal.org/home/downloads/adult-gtex/overview">GTEx source data</LinkOut></div></div>
  </Disclosure>
 </section>;
}

// Display categories only: no score, inferred classification, or ordering is introduced.
const VALIDITY:Record<string,{color:string;description:string;icon:typeof ShieldCheck}>={
 definitive:{color:'#0f766e',description:'A gene–disease relationship upheld over time with strong supporting evidence.',icon:ShieldCheck},
 strong:{color:'#087f9b',description:'Strong supporting evidence for this gene–disease relationship.',icon:ShieldCheck},
 moderate:{color:'#3e60a4',description:'Moderate supporting evidence for this gene–disease relationship.',icon:ShieldCheck},
 limited:{color:'#697586',description:'Limited supporting evidence; the relationship has not met the Moderate category.',icon:CircleDashed},
 supportive:{color:'#77549a',description:'A broad support category used when a source does not curate to the finer GenCC grades; not a ranked intermediate grade.',icon:ShieldQuestion},
 disputed:{color:'#976600',description:'The reported relationship is disputed by the source evidence assessment.',icon:ShieldQuestion},
 'disputed evidence':{color:'#976600',description:'The reported relationship is disputed by the source evidence assessment.',icon:ShieldQuestion},
 refuted:{color:'#97506b',description:'Evidence against the reported relationship substantially outweighs the supporting evidence.',icon:RefutedIcon},
 'refuted evidence':{color:'#97506b',description:'Evidence against the reported relationship substantially outweighs the supporting evidence.',icon:RefutedIcon},
 'animal model only':{color:'#886d38',description:'Animal-model evidence without an asserted human gene–disease relationship.',icon:CircleDashed},
 'no known disease relationship':{color:'#697586',description:'No causal relationship in the specified human disease has been established by the source.',icon:CircleDashed},
};
export function DiseaseClassification({source,value}:{source:unknown;value:unknown}){
 if(value===null||value===undefined||value==='')return <span className="muted">—</span>;
 const category=['GenCC','ClinGen'].includes(String(source))?VALIDITY[String(value).trim().toLowerCase()]:undefined;
 const Icon=category?.icon??CircleDashed;
 return <span className="cx-validity" style={{'--validity-color':category?.color??'#475569'} as CSSProperties} title={category?.description}><Icon size={15} aria-hidden="true"/><span>{display(value)}</span></span>;
}

// Literal source terms only; no inference from generic mutation labels or sequence.
const EFFECTS:Record<string,{text:string;tone:string;icon:typeof ArrowUp}>={
 'mutation increasing':{text:'Increased interaction',tone:'increase',icon:ArrowUp},
 'mutation increasing strength':{text:'Increased interaction strength',tone:'increase',icon:ArrowUp},
 'mutation increasing rate':{text:'Increased interaction rate',tone:'increase',icon:ArrowUp},
 'mutation decreasing':{text:'Decreased interaction',tone:'decrease',icon:ArrowDown},
 'mutation decreasing strength':{text:'Decreased interaction strength',tone:'decrease',icon:ArrowDown},
 'mutation decreasing rate':{text:'Decreased interaction rate',tone:'decrease',icon:ArrowDown},
 'mutation disrupting':{text:'Interaction disrupted',tone:'disrupt',icon:Ban},
 'mutation disrupting strength':{text:'Interaction strength disrupted',tone:'disrupt',icon:Ban},
 'mutation with no effect':{text:'No observed effect',tone:'unchanged',icon:Minus},
 'mutation causing':{text:'Interaction induced',tone:'induced',icon:Plus},
};
export function MutationEffect({value}:{value:unknown}){
 const term=label(value).trim().toLowerCase(),effect=EFFECTS[term]??{text:term==='mutation'||term==='not available'?'Effect not specified':'See source effect',tone:'unknown',icon:CircleHelp};const Icon=effect.icon;
 return <div className={`ppi-effect ppi-effect-${effect.tone}`}><strong><Icon size={17}/>{effect.text}</strong><small>{label(value)}</small></div>;
}
export function mutationName(mutation:RecordData){return label(mutation.label??mutation.feature_id).replace(/^(?:uniprotkb:)?[A-Z0-9]+(?:-\d+)?:(?=p\.)/,'');}
export function MutationPartners({mutation}:{mutation:RecordData}){
 const own=String(mutation.affected_protein??'').replace(/^uniprotkb:/,'');const all=[...new Set([...String(mutation.participants_raw??'').matchAll(/(?:^|\|)uniprotkb:([^\s(|]+)/g)].map(match=>match[1]))];const others=all.filter(id=>id!==own);
 return <div className="ppi-mutation-partners">{others.length?others.map(id=><LinkOut key={id} href={`https://www.uniprot.org/uniprotkb/${encodeURIComponent(id)}`}>{id}</LinkOut>):all.includes(own)?<span>Source participant: {display(mutation.affected_symbol)}</span>:<span>See source participants</span>}</div>;
}
export function SequenceChange({mutation}:{mutation:RecordData}){return <div className="ppi-mutation-change"><code title={display(mutation.original)}>{display(mutation.original)}</code><ArrowRight size={14}/><code title={display(mutation.resulting)}>{display(mutation.resulting)}</code></div>;}
