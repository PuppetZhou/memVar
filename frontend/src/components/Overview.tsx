import { useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, BookOpen, Fingerprint, FlaskConical, Database, Dna, Hash, Users, Ruler } from 'lucide-react';
import { api, display, label, number, params, type RecordData } from '../api';
import { Badge, DataTable, Fields, LinkOut, Modal, Pager, SelectFilter, Status } from './ui';
import type { ColumnDef } from '@tanstack/react-table';
import OverviewLocations from './OverviewLocations';
import MembraneOverview from './MembraneOverview';
import { OverviewGo, OverviewReactome, type GoSelection } from './OverviewOntology';
import { GoEvidenceHelp, GoEvidenceLabel, GoReferenceLinks } from './OverviewEvidence';
import './overview-v2.css';
import { FunctionDetails, FunctionSummary } from './FunctionalContext';
export interface Protein{accession:string;protein_name:string|null;gene_names:string[];length:number|null;sequence_id:string|null;entry_name?:string;alternative_protein_names?:string[];reviewed?:boolean;hgnc_ids?:string[];}
interface Collection{items:RecordData[];has_more?:boolean;total?:number;}
interface PharmacologySummaryItem{value:string;count:number;ligand_count:number;}
interface PharmacologySummary{totals:{record_count:number;ligand_count:number;pharmacological_record_count:number;pharmacological_ligand_count:number};record_types:PharmacologySummaryItem[];types:PharmacologySummaryItem[];actions:PharmacologySummaryItem[];}
export interface OverviewData{protein:Protein;function?:RecordData;annotations?:RecordData[];isoforms?:RecordData[];external_references?:RecordData[];membrane_labels?:RecordData[];membrane_classification?:RecordData|null;go?:Collection;go_slim?:RecordData[];pathways?:Collection;locations?:{uniprot:RecordData[];hpa:RecordData[]};rhea?:Collection;pharmacology?:Collection;}
function pharmacologyActionClass(value:unknown){const action=String(value??'').toLowerCase();if(!action||action==='none')return 'unknown';if(action.includes('inhibit')||action.includes('negative'))return 'inhibition';if(action.includes('activ')||action.includes('positive'))return 'activation';if(action.includes('agon'))return 'agonism';if(action.includes('antagon'))return 'antagonism';if(action.includes('bind'))return 'binding';return 'other';}
function PharmacologyAction({value}:{value:unknown}){const empty=value==null||value===''||String(value).toLowerCase()==='none';return <span className={`ov-pharmacology-action ov-action-${pharmacologyActionClass(value)}`} title={empty?'The source did not state an action.':String(value)}>{empty?'Unknown / not stated':display(value)}</span>;}
function BiologicalList({accession,section,initialAspect='',slimId,recordType=''}:{accession:string;section:'go'|'pathways'|'rhea'|'pharmacology';initialAspect?:string;slimId?:string;recordType?:string}){
 const [offset,setOffset]=useState(0);
 const [aspect,setAspect]=useState(initialAspect);
 const [selected,setSelected]=useState<RecordData|null>(null);
 const query=useQuery({queryKey:['overview-list',accession,section,aspect,slimId,recordType,offset],queryFn:({signal})=>api<Collection>(`/proteins/${accession}/overview/${section}?${params({aspect,slim_id:slimId,record_type:recordType,offset,limit:20})}`,signal)});
 let columns:ColumnDef<RecordData>[]=[];
 if(section==='go')columns=[
  {id:'term',header:'GO term',cell:({row})=><>{row.original.is_negative===true&&<Badge tone="amber">NOT</Badge>} <button className="text-button" onClick={()=>setSelected(row.original)}>{display(row.original.name??row.original.go_id)}</button>{row.original.is_obsolete===true&&<Badge tone="amber">Obsolete term</Badge>}<small>{display(row.original.go_id)}</small></>},
  {accessorKey:'aspect',header:'Category',cell:({getValue})=>({F:'Molecular function',P:'Biological process',C:'Cellular component'}[String(getValue())]??display(getValue()))},
  {id:'evidence',header:'Evidence',cell:({row})=><GoEvidenceLabel code={row.original.evidence_code}/>},
  {accessorKey:'relation',header:'Relation',cell:({getValue})=>label(getValue())},
 ];
 if(section==='pathways')columns=[{id:'name',header:'Pathway',cell:({row})=><LinkOut href={row.original.source_url}>{display(row.original.name)}</LinkOut>},{accessorKey:'pathway_id',header:'Reactome ID'},{id:'topics',header:'Topics',cell:({row})=>display(row.original.topics)}];
 if(section==='rhea')columns=[{id:'equation',header:'Reaction',cell:({row})=><button className="text-button" onClick={()=>setSelected(row.original)}>{display(row.original.equation)}</button>},{id:'id',header:'Rhea',cell:({row})=><LinkOut href={row.original.source_url}>{display(row.original.rhea_id)}</LinkOut>},{id:'type',header:'Reaction type',cell:({row})=>row.original.is_transport?'Transport reaction':'Biochemical reaction'}];
 if(section==='pharmacology')columns=[
  {id:'ligand',header:'Ligand',cell:({row})=><button className="text-button" onClick={()=>setSelected(row.original)}>{display(row.original.ligand_name??row.original.target_name)}</button>},
  {accessorKey:'record_type',header:'Record category',cell:({getValue})=>label(getValue())},
  {accessorKey:'type',header:'Type',cell:({getValue})=>getValue()==='None'?<span title="Source did not specify a type">—</span>:display(getValue())},
  {id:'action',header:'Action',cell:({row})=><PharmacologyAction value={row.original.action}/>},
  {id:'affinity',header:'Reported affinity',cell:({row})=><>{number(row.original.affinity_median)} <span className="muted">{row.original.affinity_units?display(row.original.affinity_units):''}</span></>},
 ];
 return <>
  {section==='go'&&!slimId&&<div className="toolbar"><SelectFilter label="GO category" value={aspect} onChange={value=>{setAspect(value);setOffset(0);}} options={[{value:'F',label:'Molecular function'},{value:'P',label:'Biological process'},{value:'C',label:'Cellular component'}]}/></div>}
  {section==='go'&&<GoEvidenceHelp/>}
  {section==='go'&&query.data?.total!==undefined&&<p className="ov-original-total">{number(query.data.total,0)} original annotation records in this selection</p>}
  <Status loading={query.isPending} error={query.error} empty={!query.data?.items.length}><DataTable items={query.data?.items??[]} columns={columns}/></Status>
  <Pager page={offset/20} count={query.data?.items.length??0} next={query.data?.has_more?'next':null} onPrevious={()=>setOffset(Math.max(0,offset-20))} onNext={()=>setOffset(offset+20)} maxPage={5000} onJump={page=>setOffset(page*20)} totalPages={query.data?.total == null ? undefined : Math.ceil(query.data.total/20)} loading={query.isFetching}/>
  {selected&&<Modal title={display(selected.name??selected.ligand_name??selected.equation??selected.target_name)} onClose={()=>setSelected(null)}>{section==='go'?<>
   <div className="ov-go-evidence-detail"><div><span>Evidence</span><GoEvidenceLabel code={selected.evidence_code}/></div><div><span>Literature / source reference</span><GoReferenceLinks value={selected.reference}/></div></div>
   <GoEvidenceHelp/>
   <Fields items={[{label:'GO ID',value:selected.go_id},{label:'Relation',value:selected.relation},{label:'Subject',value:selected.subject_id},{label:'Specified form',value:selected.form_id},{label:'Annotation extension',value:selected.extension},{label:'Association status',value:label(selected.mapping_status)},{label:'Negative annotation',value:selected.is_negative===true?'NOT':null},{label:'With / from',value:selected.with_from},{label:'Assigned by',value:selected.assigned_by},{label:'Term status',value:selected.term_status},{label:'Obsolete term',value:selected.is_obsolete===true?'Obsolete':null}]}/><LinkOut href={selected.url}>GO term definition</LinkOut>
  </>:section==='rhea'?<><p>{display(selected.equation)}</p><Fields items={[{label:'Rhea ID',value:selected.rhea_id},{label:'Direction',value:selected.direction},{label:'Association',value:label(selected.mapping_status)}]}/>{Array.isArray(selected.participants)&&<DataTable items={selected.participants as RecordData[]} columns={[{id:'name',header:'Participant',cell:({row})=><LinkOut href={row.original.chebi_url}>{display(row.original.name)}</LinkOut>},{accessorKey:'coefficient',header:'Coefficient'},{accessorKey:'side_order',header:'Equation side'}]}/>}</>:<>
   <div className="ov-pharmacology-detail-action"><span>Source action</span><PharmacologyAction value={selected.action}/></div>
   <Fields items={[{label:'Record category',value:label(selected.record_type)},{label:'Target',value:selected.target_name},{label:'Ligand',value:selected.ligand_name},{label:'Ligand type',value:selected.ligand_type},{label:'Type',value:selected.type},{label:'Assay',value:selected.assay_description},{label:'Endogenous',value:selected.endogenous},{label:'Affinity measure',value:selected.affinity_units},{label:'Median',value:selected.affinity_median},{label:'Affinity low',value:selected.affinity_low},{label:'Affinity high',value:selected.affinity_high},{label:'Original measure',value:selected.original_affinity_units},{label:'Original relation',value:selected.original_affinity_relation},{label:'Original value (nM)',value:selected.original_affinity_median_nm},{label:'PubMed',value:selected.pubmed_id},{label:'Interaction parameter',value:selected.interaction_parameter},{label:'Interaction value',value:selected.interaction_value}]}/><LinkOut href={selected.ligand_url}>Ligand at Guide to Pharmacology</LinkOut>
  </>}</Modal>}
 </>;
}

function PharmacologyDistribution({title,items,actions=false}:{title:string;items:PharmacologySummaryItem[];actions?:boolean}){
 const maximum=Math.max(1,...items.map(item=>item.count));
 return <section className="ov-pharmacology-distribution"><h4>{title}</h4>{items.length?<div>{items.map(item=><div className="ov-pharmacology-bar" key={item.value}><span>{actions?<PharmacologyAction value={item.value}/>:item.value==='None'?'Not stated':display(item.value)}</span><div><i className={actions?`ov-action-fill-${pharmacologyActionClass(item.value)}`:''} style={{width:`${item.count/maximum*100}%`}}/></div><strong>{number(item.count,0)}</strong></div>)}</div>:<p className="ov-no-data">No values supplied.</p>}</section>;
}

function PharmacologyBrowser({accession}:{accession:string}){
 const [recordType,setRecordType]=useState('pharmacological_record');
 const summary=useQuery({queryKey:['overview-pharmacology-summary',accession],queryFn:({signal})=>api<PharmacologySummary>(`/proteins/${accession}/overview/pharmacology/summary`,signal)});
 return <><Status loading={summary.isPending} error={summary.error}>{summary.data&&<>
  <div className="ov-pharmacology-totals"><div><strong>{number(summary.data.totals.pharmacological_record_count,0)}</strong><span>pharmacological source records</span></div><div><strong>{number(summary.data.totals.pharmacological_ligand_count,0)}</strong><span>distinct ligands in those records</span></div></div>
  <p className="ov-visual-note">Counts cover the complete protein selection, not the current page. Source records are not presented as independent experiments.</p>
  <div className="ov-pharmacology-distributions"><PharmacologyDistribution title="Action distribution" items={summary.data.actions} actions/><PharmacologyDistribution title="Type distribution" items={summary.data.types}/></div>
  <div className="ov-record-type-tabs" role="group" aria-label="Guide to Pharmacology record category">{summary.data.record_types.map(item=><button key={item.value} aria-pressed={recordType===item.value} onClick={()=>setRecordType(item.value)}><span>{label(item.value)}</span><strong>{number(item.count,0)}</strong><small>{number(item.ligand_count,0)} ligands</small></button>)}</div>
 </>}</Status><p className="ov-visual-note">Supporting records for the selected source category</p><BiologicalList key={recordType} accession={accession} section="pharmacology" recordType={recordType}/></>;
}
function OverviewSection({title,icon,tone,source,children,action}:{title:string;icon:ReactNode;tone:string;source:string;children:ReactNode;action?:ReactNode}){
 return <section className={`ov-section ov-${tone}`}><header><span className="ov-icon">{icon}</span><h3>{title}</h3><span className="ov-source"><Database size={14} aria-hidden="true"/>{source}</span></header><div className="ov-section-body">{children}</div>{action&&<div className="ov-section-action">{action}</div>}</section>;
}
function IdentityDetails({data}:{data:OverviewData}){
 return <><Fields items={[{label:'Entry name',value:data.protein.entry_name},{label:'Other protein names',value:data.protein.alternative_protein_names}]}/><h3>External identifiers</h3><DataTable items={data.external_references??[]} columns={[{accessorKey:'database_name',header:'Database'},{id:'identifier',header:'Identifier',cell:({row})=><LinkOut href={row.original.url}>{display(row.original.external_id)}</LinkOut>},{accessorKey:'identifier_type',header:'Object type'},{id:'scope',header:'Applies to',cell:({row})=>display(row.original.scope_id??row.original.scope_type)},{id:'paired',header:'Source pairing',cell:({row})=><div>{(['gene','transcript','protein']as const).filter(type=>row.original[`${type}_id_full`]&&row.original[`${type}_id_full`]!==row.original.external_id).map(type=><div key={type}><LinkOut href={row.original[`${type}_url`]}>{display(row.original[`${type}_id_full`])}</LinkOut></div>)}</div>}]}/><p className="small muted">Source cross-references describe database relationships, not verified sequence identity.</p><h3>Isoforms</h3><DataTable items={data.isoforms??[]} columns={[{id:'id',header:'Isoform',cell:({row})=><>{display(row.original.isoform_id)} {row.original.is_canonical===true&&<Badge>canonical</Badge>}</>},{accessorKey:'isoform_name',header:'Name'},{id:'length',header:'Length (aa)',cell:({row})=>display(row.original.lengths)},{id:'status',header:'Sequence availability',cell:({row})=>row.original.sequence_available?'Available':label(row.original.sequence_availability_reason)}]}/></>;
}
export default function Overview({data}:{data:OverviewData}){
 const {protein,annotations=[],membrane_labels=[]}=data;
 const [detail,setDetail]=useState<'identity'|'function'|'rhea'|'pharmacology'|null>(null);
 const [functionType,setFunctionType]=useState('');
 const [goSelection,setGoSelection]=useState<GoSelection|null>(null);
 const rheaPreview=(data.rhea?.items??[]).slice(0,1);const pharmacologyPreview=(data.pharmacology?.items??[]).slice(0,3);
 const detailTitles={identity:'Protein identifiers & isoforms',function:'Functional context · UniProt',rhea:'Biochemical reactions · Rhea',pharmacology:'Pharmacological context · Guide to Pharmacology'};
 const openButton=(section:typeof detail,text:string)=> <button className="ov-browse" onClick={()=>setDetail(section)}>{text}<ArrowRight size={14}/></button>;
 return <section className="overview-v2" id="overview">
  <div className="ov-identity panel"><div className="ov-identity-heading"><span className="ov-identity-icon"><Fingerprint size={25}/></span><div><span className="ov-eyebrow">Basic information</span><h1>{protein.protein_name??protein.accession}</h1></div>{openButton('identity','Names & identifiers')}</div>
   <dl className="ov-identity-fields"><div><dt><Database size={15} aria-hidden="true"/>UniProt</dt><dd><LinkOut href={`https://www.uniprot.org/uniprotkb/${protein.accession}`}>{protein.accession}</LinkOut></dd></div><div><dt><Dna size={15} aria-hidden="true"/>Gene</dt><dd>{protein.gene_names.join(' · ')||'Not assigned'}</dd></div><div><dt><Hash size={15} aria-hidden="true"/>HGNC</dt><dd>{protein.hgnc_ids?.length?protein.hgnc_ids.map((id,index)=><span key={id}>{index>0?' · ':''}<LinkOut href={`https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/${id}`}>{id}</LinkOut></span>):'Not available'}</dd></div><div><dt><Users size={15} aria-hidden="true"/>Organism</dt><dd>Homo sapiens </dd></div><div><dt><Dna size={15} aria-hidden="true"/>Default sequence</dt><dd>{display(protein.sequence_id)} {protein.sequence_id&&<Badge>canonical</Badge>}</dd></div><div><dt><Ruler size={15} aria-hidden="true"/>Length</dt><dd>{protein.length==null?'Not available':`${protein.length.toLocaleString()} aa`}</dd></div></dl>
  </div>
  <MembraneOverview accession={protein.accession} labels={membrane_labels}/>
  <div className="ov-grid">
   <div className="ov-functional-column">
   <OverviewSection title="Functional context" icon={<BookOpen size={21}/>} tone="blue" source="UniProt" action={openButton('function','Explore functional context')}>
    <FunctionSummary annotations={annotations} accession={protein.accession} activeType={functionType} onTypeChange={setFunctionType} onDetails={()=>setDetail('function')}/>
   </OverviewSection>
   <OverviewReactome accession={protein.accession}/>
   </div>
   <OverviewLocations accession={protein.accession} uniprot={data.locations?.uniprot??[]} hpa={data.locations?.hpa??[]}/>
   <OverviewGo accession={protein.accession} onSelect={setGoSelection}/>
   <OverviewSection title="Reactions & pharmacology" icon={<FlaskConical size={20}/>} tone="rose" source="Two source collections">
    <div className="ov-source-launchers"><button onClick={()=>setDetail('rhea')}><span><strong>Rhea</strong><small>Biochemical reactions</small></span><ArrowRight size={18}/></button><button onClick={()=>setDetail('pharmacology')}><span><strong>Guide to Pharmacology</strong><small>Ligands, actions and measurements</small></span><ArrowRight size={18}/></button></div>
    <div className="ov-reaction-columns"><div><span className="ov-mini-heading"><FlaskConical size={15}/>Rhea · reaction</span>{rheaPreview.length?rheaPreview.map((item,index)=><p className="ov-reaction" key={index}>{display(item.equation)}</p>):<p className="ov-no-data">No Rhea reaction available.</p>}</div><div><span className="ov-mini-heading"><Database size={15}/>Guide to Pharmacology · ligand actions</span>{pharmacologyPreview.length?<div className="ov-ligands">{pharmacologyPreview.map((item,index)=><button key={index} onClick={()=>setDetail('pharmacology')}><strong>{display(item.ligand_name??item.target_name)}</strong><PharmacologyAction value={item.action??item.type}/></button>)}</div>:<p className="ov-no-data">No pharmacological record available.</p>}</div></div>
   </OverviewSection>
  </div>
  {goSelection&&<Modal title={goSelection.name?`GO-slim · ${goSelection.name}`:'Gene Ontology · original annotations'} onClose={()=>setGoSelection(null)}>{goSelection.slim_id&&<div className="ov-go-selection"><Badge>{goSelection.slim_id}</Badge><p>Original positive source annotations connected through the published GO-slim mapping.</p><button className="ov-browse" onClick={()=>setGoSelection({aspect:goSelection.aspect})}>All annotations in this aspect, including NOT / ND <ArrowRight size={13}/></button></div>}<BiologicalList key={`${goSelection.aspect}:${goSelection.slim_id??''}`} accession={protein.accession} section="go" initialAspect={goSelection.aspect} slimId={goSelection.slim_id}/></Modal>}
  {detail&&<Modal title={detailTitles[detail]} onClose={()=>setDetail(null)}>{detail==='identity'?<IdentityDetails data={data}/>:detail==='function'?<FunctionDetails annotations={annotations} accession={protein.accession} activeType={functionType} onTypeChange={setFunctionType}/>:detail==='pharmacology'?<PharmacologyBrowser accession={protein.accession}/>:<BiologicalList accession={protein.accession} section={detail}/>}</Modal>}
 </section>;
}
