import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { HelpButton } from './HelpGuide';
import { Box, Download, Palette, RotateCcw } from 'lucide-react';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { ModeToggleGroup } from './ui/mode-toggle-group';
import { ContentTransition } from '@/lib/motion';
import StructureSequenceSelector from './StructureSequenceSelector';
import molstarScript from 'pdbe-molstar/build/pdbe-molstar-plugin.js?url';
import { bindingLabels, interfaceFetch, PartnerPicker, useInterfaceScores, useInterfaceSummary } from './InterfaceAnnotations';
import { annotationSourceGuide, continuousScoreColor, featureStyle, jsdScoreColor, missingAnnotationColor, sequenceLensLabels, variantCountBins, variantCountColorNote, variantFill } from './sequence-model';
import type { AnnotationSourceOptions, Feature, Track, Score, VariantSummary } from './sequence-model';
import 'pdbe-molstar/build/pdbe-molstar-light.css';
import './viewers.css';
import './sequence-refinement.css';

type Residue = { position: number; chain_id: string; auth_residue_number: number; insertion_code: string };
type Model = { chains?: {id:string;residue_count:number}[]; id: string; label: string; source: string; start: number | null; end: number | null; kind: string; url: string | null; mapping_status: string; residue_mapping: Residue[] };
type Viewer = { render: (el: HTMLElement, options: object) => Promise<void>; plugin?: { dispose: () => void; canvas3d?: { setProps: (props: object) => void }; managers: { structure: { hierarchy: { current: { structures: unknown[] } }; component: { applyPreset: (structures: unknown[], preset: string, params: object) => Promise<void> } } } }; visual: { focus: (selection:object[])=>Promise<void>; select: (p: object) => Promise<void>; clearSelection: (structure?:string|number,options?:{keepColors?:boolean;keepOpacity?:boolean}) => Promise<void>; reset: (p: object) => void } };
declare global { interface Window { PDBeMolstarPlugin?: new () => Viewer } }
let molstarPromise: Promise<void> | undefined;
function loadMolstar() {
  if (window.PDBeMolstarPlugin) return Promise.resolve();
  if (!molstarPromise) molstarPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script'); script.src = molstarScript;
    script.onload = () => resolve();
    script.onerror = () => { molstarPromise = undefined; script.remove(); reject(new Error('The structure viewer could not be loaded.')); };
    document.head.appendChild(script);
  });
  return molstarPromise;
}
const lenses: Record<string,string> = {plddt:'Confidence',domains:sequenceLensLabels.domains,membrane:sequenceLensLabels.membrane,ptm:sequenceLensLabels.ptm,variants:sequenceLensLabels.variants,jsd:sequenceLensLabels.jsd,binding:sequenceLensLabels.binding,pesto:'PeSTo interfaces',sppider:'SPPIDER-seq interfaces'};
export default function StructureViewer({ accession, selectedPosition, onSelectPosition }: { accession: string; selectedPosition?: number | null; onSelectPosition?: (position:number|null)=>void }) {
  const query = useQuery<{ items: Model[] }>({ queryKey: ['structures', accession], queryFn: ({signal})=>interfaceFetch(`/proteins/${accession}/structures`,signal) });
  const [selected, setSelected] = useState('');const [lens,setLens]=useState('plddt');
  const [renderStyle,setRenderStyle]=useState('ribbon');const [chain,setChain]=useState('');
  const appliedStyle=useRef<{viewer:Viewer;style:string}|null>(null);
  const [domainSource,setDomainSource]=useState('UniProt'),[ptmSources,setPtmSources]=useState<string[]>(['dbPTM']),[ptmType,setPtmType]=useState('all');
  const [committedRange,setCommittedRange]=useState<[number,number]|null>(selectedPosition?[selectedPosition,selectedPosition]:null);
  const [binding,setBinding]=useState('p_protein'),[partner,setPartner]=useState(''),[head,setHead]=useState<'receptor_probability'|'peptide_probability'>('receptor_probability');
  const [ready, setReady] = useState(false),[error,setError]=useState(''),[paintStatus,setPaintStatus]=useState('Loading model…');
  const container = useRef<HTMLDivElement>(null),viewer=useRef<Viewer|null>(null),paintQueue=useRef(Promise.resolve()),lastFocus=useRef<number|null>(null);
  const models = query.data?.items ?? [];
  const model = models.find(m => m.id === selected) ?? models[0];
  const chains=model?.chains??[];const activeChain=chains.find(c=>c.id===chain)??chains[0];
  useEffect(()=>setChain(''),[model?.id,accession]);
  const sequence=useQuery<{sequence:string;length:number;tracks:Track[];conservation:Score[];annotation_source_options?:AnnotationSourceOptions}>({queryKey:['sequence',accession,'uniprot'],queryFn:({signal})=>interfaceFetch(`/proteins/${accession}/sequence?topology=uniprot`,signal)});
  const variants=useQuery<VariantSummary>({queryKey:['sequence-variant-summary',accession],enabled:lens==='variants',queryFn:({signal})=>interfaceFetch(`/proteins/${accession}/variants/summary`,signal)});
  const summary=useInterfaceSummary(accession);
  const pestoStructure=summary.data?.pesto_structures.find(s=>s.fragment===`F${model?.id}`);
  const predictions=useInterfaceScores(accession,lens,pestoStructure?.structure_id??'',partner,lens==='pesto'||lens==='sppider');
  const ptmOptions=sequence.data?.annotation_source_options?.ptm??[];
  const ptmFeatures=useMemo(()=>sequence.data?.tracks.find(t=>t.id==='ptm')?.features.filter(f=>ptmSources.includes(f.source??''))??[],[sequence.data,ptmSources]);
  const ptmTypes=useMemo(()=>[...new Set(ptmFeatures.map(f=>featureStyle(f,'ptm').name))],[ptmFeatures]);
  const coloring=useMemo(()=>{
    const colors=new Map<number,string>(),legend=new Map<string,string>();
    const fillFeatures=(features:Feature[],style:(f:Feature,i:number)=>{name:string;color:string})=>{
      features.forEach((f,i)=>{const s=style(f,i);legend.set(s.name,s.color);for(let p=f.start;p<=f.end;p++){
        const prev=colors.get(p);if(prev&&prev!==s.color){colors.set(p,'#475569');legend.set('Overlapping annotations','#475569');}else colors.set(p,s.color);
      }});
    };
    if(lens==='domains'){
      const features=(sequence.data?.tracks.find(t=>t.id==='domains')?.features??[]).filter(f=>f.source===domainSource&&(domainSource==='Pfam'||/domain/i.test(String(f.source_type??f.type??f.label))));
      fillFeatures(features,f=>featureStyle(f,'domains'));
    }
    if(lens==='membrane')fillFeatures((sequence.data?.tracks.find(t=>t.id==='membrane')?.features??[]).filter(f=>f.source==='UniProt'),f=>featureStyle(f,'membrane'));
    if(lens==='ptm')fillFeatures(ptmFeatures.filter(f=>ptmType==='all'||featureStyle(f,'ptm').name===ptmType),f=>featureStyle(f,'ptm'));
    if(lens==='binding')fillFeatures((sequence.data?.tracks.find(t=>t.id==='function')?.features??[]).filter(f=>/binding/i.test(`${f.source_type??''} ${f.type??''} ${f.label??''}`)),f=>featureStyle(f,'function'));
    if(lens==='variants'&&variants.data){const counts=new Map(variants.data.canonical_sites.map(s=>[s.position,s.variant_count]));model?.residue_mapping.forEach(r=>colors.set(r.position,variantFill(counts.get(r.position)??0)));variantCountBins.forEach(bin=>legend.set(bin.label,bin.color));}
    if(lens==='jsd')sequence.data?.conservation.forEach(s=>{if(s.value!==null)colors.set(s.position,jsdScoreColor(s.value));});
    if(lens==='pesto')predictions.data?.items?.forEach(r=>{if(typeof r[binding]==='number')colors.set(r.position,continuousScoreColor(r[binding] as number));});
    if(lens==='sppider')predictions.data?.[head]?.forEach((v,i)=>colors.set(i+1,continuousScoreColor(v)));
    return {colors,legend};
  },[lens,sequence.data,variants.data,predictions.data,model,domainSource,ptmFeatures,ptmType,binding,head]);
  useEffect(() => {setSelected('');setPartner('');setDomainSource('UniProt');setPtmSources(['dbPTM']);setPtmType('all');setCommittedRange(null);setLens('plddt');lastFocus.current=null;}, [accession]);
  useEffect(()=>{if(selectedPosition==null){setCommittedRange(null);return;}const keepOrSelect=(current:[number,number]|null):[number,number]=>current&&selectedPosition>=current[0]&&selectedPosition<=current[1]?current:[selectedPosition,selectedPosition];setCommittedRange(keepOrSelect);},[selectedPosition]);
  useEffect(() => {
    let cancelled = false; let instance: Viewer | null = null;
    setReady(false); setError('');setPaintStatus('Loading model…');
    if (!model?.url || !container.current) return;
    const host = container.current;
    (async () => {
      await loadMolstar(); if (cancelled) return;
      instance = new window.PDBeMolstarPlugin!(); viewer.current = instance;
      await instance.render(host, { customData: { url: new URL(model.url!, location.origin).href, format: 'pdb' },
        alphafoldView: true, bgColor: { r: 248, g: 250, b: 252 }, hideControls: true,
        expanded: false, landscape: true, sequencePanel: false, leftPanel: false, rightPanel: false,
        logPanel: false, pdbeLink: false, loadingOverlay: true, validationAnnotation: false,
        domainAnnotation: false, symmetryAnnotation: false, loadMaps: false });
      if (!cancelled) setReady(true);
    })().catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : 'Structure could not be displayed'); });
    return () => { cancelled = true; instance?.plugin?.dispose(); viewer.current = null; host.replaceChildren(); };
  }, [accession, model?.url]);
  const mappedResidue = model?.mapping_status==='exact_current_canonical'?model.residue_mapping.find(r => r.position === selectedPosition):undefined;
  const committedSelection=useMemo(()=>model?.mapping_status==='exact_current_canonical'&&committedRange?model.residue_mapping.filter(r=>r.position>=committedRange[0]&&r.position<=committedRange[1]):[],[model,committedRange]);
  const appliedColors=useRef<{viewer:Viewer;colors:Map<number,string>;lens:string;style:string}|null>(null);
  function residueLabel(position:number){return `${sequence.data?.sequence[position-1]??'?'}${position}`;}
  function commitRange(range:[number,number],focusPosition=range[1]){setCommittedRange(current=>current?.[0]===range[0]&&current[1]===range[1]?current:range);onSelectPosition?.(focusPosition);}
  function clearRange(){setCommittedRange(null);onSelectPosition?.(null);}
  useEffect(()=>{
    if(!ready||!viewer.current)return;
    const instance=viewer.current;let cancelled=false;
    setPaintStatus('Applying colors…');
    paintQueue.current=paintQueue.current.catch(()=>{}).then(async()=>{
      if(cancelled)return;
      const keepColors=appliedColors.current?.viewer===instance&&appliedColors.current.colors===coloring.colors&&appliedColors.current.lens===lens&&appliedColors.current.style===renderStyle;
      if(appliedStyle.current?.viewer!==instance||appliedStyle.current.style!==renderStyle){
        await instance.visual.clearSelection();if(cancelled)return;
        const plugin=instance.plugin;
        if(!plugin)throw new Error('Structure renderer unavailable');
        await plugin.managers.structure.component.applyPreset(plugin.managers.structure.hierarchy.current.structures,
          renderStyle==='surface'?'coarse-surface':'polymer-cartoon',
          {ignoreHydrogens:true,quality:'medium',theme:{globalName:'plddt-confidence'}});
        plugin.canvas3d?.setProps({illumination:{enabled:renderStyle==='surface'}});
        appliedStyle.current={viewer:instance,style:renderStyle};
        if(cancelled)return;
      }
      const mapped=model?.mapping_status==='exact_current_canonical'?model.residue_mapping:[];
      const colored=mapped.filter(r=>coloring.colors.has(r.position));
      const data:object[]=keepColors||lens==='plddt'?[]:colored.map(r=>({auth_asym_id:r.chain_id,auth_seq_id:r.auth_residue_number,pdbx_PDB_ins_code:r.insertion_code||undefined,color:coloring.colors.get(r.position)}));
      // PDBe Mol* color:null keeps the scientific scale on the main representation.
      // Group only consecutive mapped residues without insertion codes; this keeps
      // long selections compact without selecting across unmapped positions.
      const segments:{first:Residue;last:Residue}[]=[];
      for(const residue of [...committedSelection].sort((a,b)=>a.chain_id.localeCompare(b.chain_id)||a.position-b.position)){
        const segment=segments.at(-1),last=segment?.last;
        if(segment&&last&&!last.insertion_code&&!residue.insertion_code&&last.chain_id===residue.chain_id&&last.position+1===residue.position&&last.auth_residue_number+1===residue.auth_residue_number)segment.last=residue;
        else segments.push({first:residue,last:residue});
      }
      segments.forEach(({first,last})=>data.push({auth_asym_id:first.chain_id,...(first===last?{auth_seq_id:first.auth_residue_number,pdbx_PDB_ins_code:first.insertion_code||undefined}:{beg_auth_seq_id:first.auth_residue_number,end_auth_seq_id:last.auth_residue_number}),color:null,representation:'ball-and-stick',representationColor:'#0d74ce'}));
      if(mappedResidue&&committedSelection.some(r=>r===mappedResidue)&&lastFocus.current!==mappedResidue.position)data.push({auth_asym_id:mappedResidue.chain_id,auth_seq_id:mappedResidue.auth_residue_number,pdbx_PDB_ins_code:mappedResidue.insertion_code||undefined,color:null,focus:true});
      if(data.length||(!keepColors&&lens!=='plddt'))await instance.visual.select({data,keepColors,keepOpacity:keepColors,...(keepColors||lens==='plddt'?{}:{nonSelectedColor:missingAnnotationColor})});
      else await instance.visual.clearSelection(undefined,{keepColors,keepOpacity:keepColors});
      appliedColors.current={viewer:instance,colors:coloring.colors,lens,style:renderStyle};
      if(cancelled)return;
      lastFocus.current=mappedResidue?.position??null;
      setError('');
      setPaintStatus('');
    }).catch(()=>{if(!cancelled){setError('Residue coloring could not be applied.');setPaintStatus('Coloring failed');}});
    return()=>{cancelled=true;};
  },[ready,model,coloring,lens,mappedResidue,committedSelection,selectedPosition,renderStyle]);
  const continuous=['jsd','pesto','sppider'].includes(lens);
  const annotationLoading=(sequence.isFetching||predictions.isFetching||variants.isFetching)&&lens!=='plddt';
  const displayStatus=lens==='sppider'&&!partner?'Choose a partner to color this query sequence':paintStatus;
  const dataError=sequence.error??(lens==='variants'?variants.error:null)??(lens==='pesto'||lens==='sppider'?predictions.error??summary.error:null);
  return <section className="panel structure-section" id="structure">
    <div className="section-heading"><span className="viewer-icon structure-icon"><Box size={23} /></span><div><h2>Protein structure <HelpButton title="Structure guide"><p>Ribbon shows helices, strands and loops; surface shows the molecular envelope. Both use the same model and annotation colors.</p><p>Residue linking requires an exact match to the current canonical sequence. Binding interface scores are predictions for the selected fragment or partner, not experimental interactions.</p></HelpButton></h2><p>3D annotations & predicted interfaces</p></div><span className="badge">Predicted structure</span></div>
    {query.isPending ? <p className="empty-state">Loading structure catalogue…</p> : query.isError ? <div className="empty-state"><p>{query.error.message}</p><Button variant="outline" size="sm" onClick={() => query.refetch()}>Retry</Button></div> : !models.length ? <p className="empty-state">No local structure is available for this protein. Sequence annotations remain accessible above.</p> : <>
      <div className="toolbar"><label>Model <select aria-label="Structure model" value={model?.id ?? ''} onChange={e => setSelected(e.target.value)}>{models.map(m => <option key={m.id} value={m.id}>{m.label} · {m.start ?? '?'}–{m.end ?? '?'}</option>)}</select></label>
        <label>Chain <select aria-label="Structure chain" value={activeChain?.id??''} disabled={!chains.length} onChange={e=>{setChain(e.target.value);if(ready)void viewer.current?.visual.focus([{auth_asym_id:e.target.value}]);}}>{chains.length?chains.map(c=><option key={c.id} value={c.id}>{c.id||'(blank ID)'} · {c.residue_count.toLocaleString()} residues{chains.length===1?' · single chain':''}</option>):<option value="">Unavailable</option>}</select></label>
        <Button variant="outline" size="sm" disabled={!ready||!activeChain} onClick={()=>{if(activeChain)void viewer.current?.visual.focus([{auth_asym_id:activeChain.id}]);}}>Focus chain</Button>
        <label>Render style <select aria-label="Structure render style" value={renderStyle} onChange={e=>setRenderStyle(e.target.value)}><option value="ribbon">Ribbon</option><option value="surface">Molecular surface</option></select></label>
        <Button variant="outline" size="sm" disabled={!ready} onClick={() => { viewer.current?.visual.reset({ camera: true }); }}><RotateCcw size={15} /> Reset camera</Button>
        {model?.url && <Button asChild variant="outline" size="sm"><a href={model.url} download={`${accession}-F${model.id}.pdb`}><Download size={15} /> PDB</a></Button>}
        {selectedPosition&&<ContentTransition transitionKey={selectedPosition} className="muted structure-selection-status" role="status">{selectedPosition ? `Shared residue focus: ${residueLabel(selectedPosition)}${mappedResidue ? ` → chain ${mappedResidue.chain_id}, ${mappedResidue.auth_residue_number}` : ' · not mapped in this model'}` : ''}</ContentTransition>}
      </div>
      {sequence.data?.sequence?<StructureSequenceSelector key={accession} sequence={sequence.data.sequence} mapping={model?.mapping_status==='exact_current_canonical'?model.residue_mapping:[]} value={committedRange} focusedPosition={selectedPosition} onCommit={commitRange} onClear={clearRange}/>:<p className="muted small">Canonical sequence is not available for local selection.</p>}
      <ModeToggleGroup className="structure-lens-controls" aria-label="Structure coloring" value={lens} onValueChange={setLens} options={Object.entries(lenses).map(([value,label])=>({value,label,disabled:value!=='plddt'&&model?.mapping_status!=='exact_current_canonical'}))}/><ContentTransition transitionKey={lens}>
      {lens==='domains'&&<div className="interface-controls"><label>Domain source<select aria-label="Structure domain source" value={domainSource} onChange={e=>setDomainSource(e.target.value)}><option>UniProt</option><option>Pfam</option></select></label></div>}
      {lens==='ptm'&&<div className="interface-controls structure-source-controls"><span>Verified canonical PTM positions</span><fieldset><legend>PTM sources</legend>{ptmOptions.map(option=>{const guide=annotationSourceGuide(option.source,option.kind);return <label key={option.id} title={guide.description}><Checkbox checked={ptmSources.includes(option.id)} disabled={option.available===false} onCheckedChange={()=>setPtmSources(current=>current.includes(option.id)?current.filter(source=>source!==option.id):[...current,option.id])}/>{option.label} <small>{option.count??'—'}</small></label>;})}</fieldset><label>Modification<select aria-label="Structure PTM type" value={ptmType} onChange={e=>setPtmType(e.target.value)}><option value="all">All types</option>{ptmTypes.map(t=><option key={t}>{t}</option>)}</select></label></div>}
      {lens==='binding'&&<div className="interface-controls"><span>UniProt binding-site annotations mapped to the canonical sequence. This view does not predict pockets.</span></div>}
      {lens==='pesto'&&<div className="interface-controls"><label>Binding class<select aria-label="Structure PeSTo score" value={binding} onChange={e=>setBinding(e.target.value)}>{Object.entries(bindingLabels).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label><span>{pestoStructure?`${pestoStructure.fragment} · ${pestoStructure.start}–${pestoStructure.end}`:'No PeSTo prediction for this model fragment'}</span></div>}
      {lens==='sppider'&&<><PartnerPicker accession={accession} value={partner} onChange={setPartner}/><div className="interface-controls"><label>Query role<select aria-label="Structure SPPIDER query role" value={head} onChange={e=>setHead(e.target.value as typeof head)}><option value="receptor_probability">Query as receptor</option><option value="peptide_probability">Query as peptide</option></select></label><span>Both modes color {accession}, conditional on the selected partner.</span></div></>}
      </ContentTransition>{(displayStatus||annotationLoading)&&<div className="structure-colour-note" role="status">{displayStatus}{annotationLoading?`${displayStatus?' · ':''}Loading annotation data…`:''}</div>}
      {model?.mapping_status !== 'exact_current_canonical' && <p className="viewer-warning">Canonical sequence match unverified · residue linking disabled.</p>}
      {(error||dataError)&&<p role="alert" className="viewer-warning">{error||dataError?.message}</p>}
      <div className="molstar-frame" ref={container} aria-label="Interactive three-dimensional protein structure" aria-busy={!ready||paintStatus==='Applying colors…'} />
      <div className="structure-legend-group"><div className="atlas-legend-heading"><Palette size={15}/><strong>{lenses[lens]}</strong>{lens==='variants'&&<span>Mapped DNA variants per residue</span>}</div><div className="viewer-legend">{lens==='plddt'?<><span>AlphaFold confidence (pLDDT)</span><span><i style={{background:'#0053d6'}}/> ≥90</span><span><i style={{background:'#65cbf3'}}/> 70–90</span><span><i style={{background:'#ffdb13'}}/> 50–70</span><span><i style={{background:'#ff7d45'}}/> &lt;50</span></>:continuous?<><span>{lens==='jsd'?'JSD conservation':lens==='pesto'?bindingLabels[binding]:head==='receptor_probability'?'Query as receptor':'Query as peptide'}</span><span>0 <b className={`structure-gradient${lens==='jsd'?' is-jsd':''}`}/> 1</span></>:[...coloring.legend].map(([name,color])=><span key={name}><i style={{background:color,border:color==='#ffffff'?'1px solid var(--slate-7)':undefined}}/>{name}</span>)}{lens!=='plddt'&&<span><i style={{background:missingAnnotationColor}}/>{lens==='jsd'||lens==='pesto'||lens==='sppider'?'No score in this view':'No annotation in this view'}</span>}{committedRange&&<span><i className="structure-selection-key"/>Blue sticks · selected {committedRange[0]===committedRange[1]?`residue ${committedRange[0]}`:`range ${committedRange[0]}–${committedRange[1]}`}</span>}</div>{(lens==='pesto'||lens==='sppider'||lens==='variants')&&<p className="structure-legend-note">{lens==='variants'?<>Unique mapped variants, not population frequency. {variantCountColorNote}</>:'Model scores, 0–1; not clinical pathogenicity or verified contacts. No threshold or aggregation across partners / fragments.'}</p>}</div>
    </>}
  </section>;
}
