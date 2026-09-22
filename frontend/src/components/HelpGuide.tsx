import { useState, type ReactNode } from 'react';
import { CircleHelp, X } from 'lucide-react';
import { Dialog, DialogClose, DialogContent, DialogTitle, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import './help-guide.css';

// Source definitions and local display conventions are deliberately separated.
const guides = {
 variants: { title:'Reading variants', sections:[
  ['Rows and coordinates','A row is a selected transcript annotation; one genomic variant may occupy several rows. Genomic alleles use GRCh38. Residue searches and ranges use verified UniProt positions.'],
  ['Transcripts','Ensembl canonical is a VEP transcript flag, separate from verified UniProt sequence mapping. Filters cover published representative consequences, not every possible transcript.'],
  ['Evidence','ClinVar classifications, population frequencies and computational scores are separate evidence. Missing values are not zero. Consequence labels and source memberships can overlap.'],
 ], links:[['ClinVar classifications','https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/']] },
 clinical: { title:'ClinVar chart', sections:[
  ['Explore','Hover a segment or focus a legend item to see its count and percentage. Click a legend item to keep it highlighted; click again to clear. The chart does not change table filters.'],
  ['Display groups','Each matching genomic variant belongs to one display group. Discordant labels remain conflicting; unclassified includes records without a usable classification. Open a variant for the original assertions.'],
  ['Review status','Stars indicate review level, not pathogenicity probability. Germline classification, oncogenicity and somatic clinical impact remain separate in the evidence panel.'],
 ], links:[['Classification definitions','https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/'],['Review stars','https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/']] },
 predictions: { title:'Prediction toolkit', sections:[
  ['Choose predictors','Select published fields as individual predictor columns; scroll the table to compare additional scores. Method groups organize the available outputs; tool labels may include model variants and are not independent votes. Coverage varies by field.'],
  ['AlphaMissense','Predicts the effect of amino acid substitutions using evolutionary and structural context. We show the original 0–1 score and linked source category; this is computational evidence, not a clinical classification.'],
  ['Read scores','Scales and directions differ. Matched source calls determine category colors; other tints follow documented score direction. Conservation uses blue. We do not create a combined score or new thresholds.'],
  ['AlphaGenome','The Variant Browser contains variant-scoring outputs. The separate AlphaGenome section shows reference-sequence tracks, not alternate-allele effects.'],
 ], links:[['AlphaMissense method','https://deepmind.google/research/publications/21083/']] },
 expression: { title:'Expression guide', sections:[
  ['Browse','Choose RNA or protein measurements, then a database and tissue, cell or cancer context. The matrix starts with ten source-defined groups; use Show more or Show all to access the full collection.'],
  ['Values and coverage','Numeric bars show original source values or explicitly labelled project medians. Open a group to inspect its original values. Coverage counts are source records; changing how many groups are visible does not change the full-collection scale.'],
  ['Measurements','RNA and protein measurements retain source units and assay context. HPA pTPM and nTPM are different RNA normalization measures; the measurement guide explains these and nCPM. Compare values within one collection and unit. Missing measurements are not zero.'],
 ], links:[['Human Protein Atlas data','https://www.proteinatlas.org/about/download']] },
 qtl: { title:'Regulatory associations', sections:[
  ['Read an association','Inspect the molecular phenotype, tissue, genome assembly, effect measure and P value together. Source association counts are not independent discoveries or proof of protein-level causality.'],
  ['Tissue map','Body regions group source labels for navigation only. They do not harmonize tissues, assays or cohorts. Unrecognized labels remain under Other / unmapped.'],
 ], links:[] },
 ppi: { title:'Interaction evidence', sections:[
  ['Collections','Choose a full source, disease/research project or IntAct mutation collection. Project names are source labels, not diagnoses or proof of tissue specificity. Collections overlap and should not be summed.'],
  ['Chart','The ring describes source categories under the current filters. Hover or focus a legend item for its share. Use the collection entries and table filters to browse records.'],
  ['Mutation features','Counts are source features, not unique mutations or independent experiments. Original ranges and sequence changes are linked through the affected protein; they are not validated canonical coordinates or mapped project variants. Interaction effect is not clinical pathogenicity.'],
 ], links:[['IntAct mutation records','https://www.ebi.ac.uk/training/online/courses/intact-quick-tour/getting-data-from-intact/']] },
 diseases: { title:'Diseases & phenotypes', sections:[
  ['Source evidence','Gene–disease assertions and disease-level phenotypes retain source identity. Neither assigns a clinical classification to an individual variant.'],
  ['PTMD2','PTM–disease context is protein-associated. Original State and MutationSite fields are retained; source positions have no verified canonical projection.'],
 ], links:[] },
 go: { title:'Gene Ontology', sections:[
  ['Three aspects','Molecular function describes activity; biological process describes the wider programme; cellular component describes where activity occurs.'],
  ['Preview','Bars count positive source annotations mapped to published GO-slim categories. Categories overlap. Counts are neither enrichment scores nor a ranking of function. Open a category for original terms and evidence.'],
 ], links:[['GO definitions','https://geneontology.org/docs/ontology-documentation/']] },
 sequence: { title:'Sequence guide', sections:[
  ['Coordinates','Tracks share the canonical sequence window. Only verified mappings are drawn; unmapped variants remain in the catalog. No color does not establish biological absence.'],
  ['Annotations','Colors distinguish source features. Click a feature or residue for the underlying records; clustered marks retain their individual positions and sources.'],
  ['Scores','JSD shows conservation on its original 0–1 scale, not pathogenicity. The dashed 0.5 line is a visual reference, not a threshold. Interface predictions retain fragment and partner context.'],
 ], links:[] },
} satisfies Record<string,{title:string;sections:string[][];links:string[][]}>;
export type HelpTopic=keyof typeof guides;

export function HelpButton({topic,title,label,children}:{topic?:HelpTopic;title?:string;label?:string;children?:ReactNode}){
 const [open,setOpen]=useState(false);const guide=topic?guides[topic]:undefined;const heading=title??guide?.title??'Help';
 return <Dialog open={open} onOpenChange={setOpen}><DialogTrigger asChild><button type="button" className="help-trigger" aria-label={`Help: ${heading}`}><CircleHelp size={16}/>{label&&<span>{label}</span>}</button></DialogTrigger><HelpDialog title={heading}>{guide&&<><div className="help-sections">{guide.sections.map(([name,text])=><section key={name}><h3>{name}</h3><p>{text}</p></section>)}</div>{guide.links.length>0&&<div className="help-sources">{guide.links.map(([name,url])=><a key={url} href={url} target="_blank" rel="noreferrer">{name} ↗</a>)}</div>}</>}{children}</HelpDialog></Dialog>;
}
function HelpDialog({title,children}:{title:string;children:ReactNode}){
 return <DialogContent className="help-dialog" aria-describedby={undefined} showCloseButton={false}><header><DialogTitle>{title}</DialogTitle><DialogClose asChild><Button type="button" variant="ghost" size="icon-sm" aria-label="Close help"><X/></Button></DialogClose></header><div className="help-body">{children}</div></DialogContent>;
}
