import { membranePalette } from '../lib/membrane-palette';
import { palette, sequenceScoreColor, bindingSiteColor } from '../lib/palette';
export type Feature = { id?: string; start: number; end: number; label?: string; type?: string; source?: string; source_type?: string; description?: string; group?: string; record_ids?: string[]; [key: string]: unknown };
export type Track = { id: string; label: string; type?: string; color?: string; features: Feature[] };
export type Score = { position: number; value: number | null; status?: string };
export type VariantSummary = { canonical_sites: {position: number; count: number; variant_count: number; substitution_count: number; clinical_counts?: import('./VariantDistribution').ClinicalCounts}[]; totals: {unique_variants: number; canonical_mapped_variants: number; canonical_unmapped_variants: number; [key:string]:number}; notes?: string[]; sequence_id?: string };
export type AnnotationSourceOption = {id:string;label:string;source:string;kind?:string;method?:string|null;count?:number;available?:boolean};
export type AnnotationSourceOptions = {domains:AnnotationSourceOption[];ptm:AnnotationSourceOption[];topology:AnnotationSourceOption[]};

export const sequenceLensLabels:Record<string,string>={
  domains:'Domains',membrane:'Membrane topology',ptm:'PTM',variants:'Variant count',jsd:'JSD conservation',binding:'Binding sites',
};
export const missingAnnotationColor=palette.missing;
export const variantCountColorNote='Colours show variant counts, not clinical pathogenicity.';
// memVar count colours, using the author-selected palette. Existing count bins are unchanged.
// Zero is white; missing annotations use a separate neutral fill.
export const sequencePtmPresenceColor=palette.rose;
export const variantCountBins=[
  {label:'0',minimum:0,maximum:0,color:'#ffffff',textColor:'#172a3a'},
  {label:'1',minimum:1,maximum:1,color:palette.mist,textColor:'#172a3a'},
  {label:'2–4',minimum:2,maximum:4,color:palette.ice,textColor:'#172a3a'},
  {label:'5',minimum:5,maximum:5,color:palette.blue,textColor:'#172a3a'},
  {label:'6',minimum:6,maximum:6,color:palette.butter,textColor:'#172a3a'},
  {label:'7–8',minimum:7,maximum:8,color:palette.apricot,textColor:'#172a3a'},
  {label:'9+',minimum:9,maximum:Number.POSITIVE_INFINITY,color:palette.rose,textColor:'#111111'},
] as const;

type SourceGuide={description:string;url?:string};
const SOURCE_GUIDES:Record<string,SourceGuide>={
  UniProt:{description:'Curated protein features on the current UniProt entry and canonical sequence.',url:'https://www.uniprot.org/help/sequence_annotation'},
  Pfam:{description:'Profile-HMM protein-family domains aligned to the current canonical sequence.',url:'https://www.ebi.ac.uk/interpro/entry/pfam/'},
  dbPTM:{description:'Integrated post-translational modification records mapped to verified canonical positions.',url:'https://biomics.lab.nycu.edu.tw/dbPTM/'},
  GlyGen:{description:'Glycosylation-focused source records; only verified mapped positions are drawn.',url:'https://glygen.org/'},
  ProteomeScout:{description:'Experimentally reported PTM records aggregated from proteomics sources.',url:'https://proteomescout.wustl.edu/'},
  DeepTMHMM2:{description:'Sequence-model membrane-topology prediction; it is not a curated experimental annotation.',url:'https://dtu.biolib.com/DeepTMHMM'},
  HTP:{description:'Human Transmembrane Proteome integrated topology record, kept separate from other sources.'},
  TOPDB:{description:'TOPDB membrane-topology source record; each source record is displayed independently.',url:'https://topdb.enzim.hu/'},
  OPM:{description:'Structure-derived membrane placement from an individual OPM structure and chain.',url:'https://opm.phar.umich.edu/'},
};
export function annotationSourceGuide(source:string,kind?:string):SourceGuide{
  const known=SOURCE_GUIDES[source];if(known)return known;
  if(kind==='prediction'||kind==='method_prediction')return {description:`${source} computational prediction; shown as its own layer without source voting.`};
  if(kind==='structure_region')return {description:`${source} structure-derived region from one source model or chain; not a consensus topology.`};
  if(kind==='experimental_evidence')return {description:`${source} experimental source record; original record boundaries are retained.`};
  if(kind==='integrated_topology')return {description:`${source} integrated topology record; displayed separately from curated and predicted layers.`};
  return {description:`${source} source annotation. Original source identity and record boundaries are retained.`};
}
export function continuousScoreColor(value:number):string{
  return sequenceScoreColor(value, 'interface');
}
export function jsdScoreColor(value:number):string{
  return sequenceScoreColor(value, 'jsd');
}

export const featurePalette = [
  {name:'Dephosphorylation',color:palette.blueInk,match:/dephospho/i},
  {name:'Phosphorylation',color:palette.apricot,match:/phospho/i},
  {name:'Glycosylation',color:palette.sage,match:/glyco|glycan/i},
  {name:'Ubiquitination',color:palette.coral,match:/ubiquit/i},
  {name:'Acetylation',color:palette.cyan,match:/acetyl/i},
  {name:'Methylation',color:palette.blue,match:/methyl/i},
  {name:'Disulfide bond',color:palette.rose,match:/disulfide/i},
  {name:'Sumoylation',color:palette.peach,match:/sumoyl/i},
  {name:'Lipidation',color:palette.leaf,match:/lipid|palmitoyl/i},
  {name:'Nitrosylation',color:palette.ice,match:/nitroso|nitrosyl/i},
  {name:'Oxidation',color:palette.butter,match:/oxidation/i},
  {name:'Cross-link',color:palette.mist,match:/cross-link/i},
  {name:'Other PTM',color:'#64748b',match:/.*/},
];
function membraneName(f:Feature){const native=String(f.source_type??f.label??'');const raw=f.source==='UniProt'&&native==='Topological domain'?String(f.label??f.description??native):native;const htp:Record<string,string>={M:'Transmembrane',L:'Intramembrane reentrant loop',I:'Cytoplasmic',O:'Non-cytoplasmic',S:'Signal'};return /^HTP(?:$|[:/_])/i.test(f.source??'')?(htp[raw]??raw):f.source==='DeepTMHMM2'&&raw==='TMhelix'?'Transmembrane':raw;}
export function isMembraneFeature(f:Feature){return /transmembrane|intramembrane/i.test(membraneName(f));}
export function featureStyle(f: Feature, track: string): {name:string;color:string} {
  const name = `${f.source_type??f.type??''} ${f.label??''}`;
  if(track==='ptm') {if(f.source==='GlyGen'&&/^[NO]-linked$/i.test(f.source_type??''))return {name:'Glycosylation',color:palette.sage};return featurePalette.find(p=>p.match.test(name))!;}
  if(track==='secondary') return /helix/i.test(name)?{name:'Helix',color:palette.rose}:/strand|sheet/i.test(name)?{name:'Beta strand',color:palette.blue}:{name:'Turn / loop',color:palette.sage};
  if(track==='membrane') {const type=membraneName(f);return /transmembrane|intramembrane/i.test(type)?{name:'Membrane segment',color:membranePalette.membrane}:/extra|outside|non-cyto/i.test(type)?{name:'Non-cytoplasmic / outside',color:membranePalette.outside}:/cyto|inside/i.test(type)?{name:'Cytoplasmic / inside',color:membranePalette.inside}:/signal/i.test(type)?{name:'Signal region',color:membranePalette.signal}:{name:'Topology',color:membranePalette.other};}
  if(track==='domains') return f.source==='Pfam'?{name:'Pfam domain',color:palette.apricot}:/domain/i.test(name)?{name:'UniProt domain',color:palette.peach}:{name:'Region / processing',color:palette.leaf};
  if(/binding/i.test(`${f.source_type??''} ${f.type??''} ${f.label??''}`))return {name:'Binding site',color:bindingSiteColor};
  return {name:'Functional site',color:palette.rose};
}
export const sourceColors:Record<string,string>={UniProt:palette.blue,Pfam:palette.apricot,dbPTM:palette.sage,GlyGen:palette.cyan,ProteomeScout:palette.leaf,PTMD2:palette.rose,DeepTMHMM2:'#475569'};
export function variantCountBin(count:number){return variantCountBins.find(bin=>count>=bin.minimum&&count<=bin.maximum)??variantCountBins[variantCountBins.length-1];}
export function variantFill(count:number):string{return variantCountBin(count).color;}
export function variantTextColor(count:number):string{return variantCountBin(count).textColor;}
