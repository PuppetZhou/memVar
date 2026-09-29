import { useQuery } from '@tanstack/react-query';
import { api, number } from '../api';
import { Disclosure, LinkOut, Status } from './ui';
import './disease-classification.css';

const SCHEMES = [
  {id:'mondo_body_system', label:'MONDO · Body system'},
  {id:'mondo_etiology', label:'MONDO · Etiology'},
  {id:'kegg', label:'KEGG · Disease categories'},
];
// English presentation labels only; original labels and membership remain in the API/database.
const KEGG_LABELS:Record<string,string>={
  'Q7KEGG:infection':'Infectious diseases', 'Q7KEGG:neoplasm':'Neoplasms',
  'Q7KEGG:cardiovascular':'Cardiovascular diseases', 'Q7KEGG:chromosomal':'Chromosomal abnormalities',
  'Q7KEGG:congenital':'Congenital malformations', 'Q7KEGG:digestive':'Digestive system diseases',
  'Q7KEGG:endocrine_metabolic':'Endocrine / metabolic diseases', 'Q7KEGG:hematologic':'Hematologic diseases',
  'Q7KEGG:immune':'Immune system diseases', 'Q7KEGG:mental':'Mental / behavioral disorders',
  'Q7KEGG:musculoskeletal':'Musculoskeletal diseases', 'Q7KEGG:nervous':'Nervous system diseases',
  'Q7KEGG:reproductive':'Reproductive system diseases', 'Q7KEGG:respiratory':'Respiratory diseases',
  'Q7KEGG:ribosomopathy':'Ribosomopathies', 'Q7KEGG:skin':'Skin diseases', 'Q7KEGG:urinary':'Urinary system diseases',
};
function categoryLabel(id:string|null,label:string|null){return (id&&KEGG_LABELS[id])||label;}
interface Classification {scheme:string;category_id:string|null;category_label:string|null;mapping_status:string;}
interface Disease {mondo_id:string;classifications:Classification[];}
interface RecordClassification {available:boolean;diseases:Disease[];}
interface Category {category_id:string;category_label:string;variant_count:number;anatomical_category:boolean|null;}
interface Scheme {scheme:string;label:string;mapped_variants:number;unmapped_variants:number;with_mondo_unmapped:number;items:Category[];}
interface Distribution {total_variants:number;variants_with_mondo:number;without_mondo:number;disease_ids:number;schemes:Scheme[];versions:{mondo:string;kegg:string;rules:string};}

export function DiseaseTypeLabels({value}:{value:unknown}){
  const data=value as RecordClassification|undefined;
  return <section className="dc-types" aria-label="Disease type classifications"><h3>Disease types</h3>
    {!data?.available?<p>Classification data is currently unavailable.</p>:!data.diseases.length?<p>No direct MONDO identifier in this ClinVar summary record.</p>:<>
      {data.diseases.map(disease=><div className="dc-disease" key={disease.mondo_id}>
        <LinkOut href={`https://monarchinitiative.org/${disease.mondo_id}`}>{disease.mondo_id}</LinkOut>
        <dl>{SCHEMES.map(scheme=>{const rows=disease.classifications.filter(row=>row.scheme===scheme.id),mapped=rows.filter(row=>row.category_id);return <div key={scheme.id}><dt>{scheme.label}</dt><dd>{mapped.length?mapped.map(row=><span className={`dc-type dc-${scheme.id}`} key={row.category_id} title={row.category_id??''}>{categoryLabel(row.category_id,row.category_label)}</span>):<span className="dc-missing" title={rows.map(row=>row.mapping_status).join(' · ')}>No mapped category</span>}</dd></div>;})}</dl>
      </div>)}
      <p className="dc-note">Disease context, not variant pathogenicity. Categories can overlap. KEGG uses reference-supported links, not disease identity equivalence; no condition name-to-ID pairing is inferred.</p>
    </>}
  </section>;
}

export function ClinvarClassificationDistribution({accession}:{accession:string}){
  const result=useQuery({queryKey:['clinvar-classification',accession],queryFn:({signal})=>api<Distribution>(`/proteins/${accession}/diseases/clinvar-classification`,signal)});
  const data=result.data;
  return <section className="dc-distribution" aria-label="ClinVar disease classification distribution"><header><h3>Disease classification</h3><p>Two MONDO views and the project’s 17 KEGG categories</p></header>
    <Status loading={result.isPending} error={result.error}>{data&&<>
      <div className="dc-summary"><span><strong>{number(data.total_variants,0)}</strong> ClinVar SNVs</span><span><strong>{number(data.variants_with_mondo,0)}</strong> with MONDO</span><span><strong>{number(data.without_mondo,0)}</strong> without MONDO</span></div>
      <p className="dc-note">All ClinVar SNVs linked to this protein’s genes, independent of the condition search below. Each bar counts unique SNVs; categories overlap, so percentages may sum to more than 100%.</p>
      <div className="dc-charts">{data.schemes.map(scheme=><section className={`dc-chart dc-${scheme.scheme}`} key={scheme.scheme} aria-label={scheme.label}>
        <h4>{scheme.label}</h4><p><strong>{number(scheme.mapped_variants,0)}</strong> mapped · {number(scheme.unmapped_variants,0)} unmapped</p>
        <ol>{scheme.items.filter(item=>item.variant_count>0).map(item=>{const percent=data.total_variants?100*item.variant_count/data.total_variants:0;return <li key={item.category_id} title={`${item.category_id} · ${item.variant_count} of ${data.total_variants} SNVs`}><div className="dc-bar-label"><span>{categoryLabel(item.category_id,item.category_label)}{item.anatomical_category===false&&scheme.scheme==='mondo_body_system'&&<small>Non-anatomical category</small>}</span><b>{number(item.variant_count,0)} <small>{percent<0.1?'<0.1':percent.toFixed(1)}%</small></b></div><div className="dc-bar-track" aria-hidden="true"><span style={{width:`${percent}%`}}/></div></li>;})}</ol>
        {!scheme.mapped_variants&&<p className="dc-missing">No mapped categories in this view.</p>}
        <p className="dc-note">{number(scheme.with_mondo_unmapped,0)} with MONDO but no category in this view; {number(data.without_mondo,0)} without MONDO. Zero-count categories are omitted.</p>
      </section>)}</div>
      <Disclosure title="Classification scope & sources"><p>MONDO body-system and etiology classes follow the confirmed ontology hierarchy. The body-system view includes syndromic disease as a non-anatomical category. Etiology does not describe a variant’s molecular effect or inheritance.</p><p>KEGG categories use the project’s 17-group mapping via MONDO exact references and KEGG DBLINKS. These links support classification, not disease identity equivalence. No clinical-significance filter or name/RCV-based inference is applied.</p><p>MONDO {data.versions.mondo} · KEGG {data.versions.kegg} · Mapping {data.versions.rules}</p></Disclosure>
    </>}</Status>
  </section>;
}
