import type { CSSProperties } from 'react';
import { LinkOut } from './ui';

type EvidenceDefinition = {
  name: string;
  explanation: string;
  family: 'experimental' | 'phylogenetic' | 'computational' | 'author' | 'curator' | 'automatic' | 'other';
};

const GO_EVIDENCE: Record<string, EvidenceDefinition> = {
  EXP: { name: 'Inferred from experiment', explanation: 'Experimental evidence; the more specific assay code was not supplied.', family: 'experimental' },
  IDA: { name: 'Inferred from direct assay', explanation: 'A direct assay supports the annotation.', family: 'experimental' },
  IPI: { name: 'Inferred from physical interaction', explanation: 'A physical interaction experiment supports the annotation.', family: 'experimental' },
  IMP: { name: 'Inferred from mutant phenotype', explanation: 'A mutant phenotype supports the annotation.', family: 'experimental' },
  IGI: { name: 'Inferred from genetic interaction', explanation: 'A genetic interaction supports the annotation.', family: 'experimental' },
  IEP: { name: 'Inferred from expression pattern', explanation: 'An expression pattern supports the annotation.', family: 'experimental' },
  HTP: { name: 'High-throughput experiment', explanation: 'A high-throughput experiment supports the annotation.', family: 'experimental' },
  HDA: { name: 'High-throughput direct assay', explanation: 'A high-throughput direct assay supports the annotation.', family: 'experimental' },
  HMP: { name: 'High-throughput mutant phenotype', explanation: 'A high-throughput mutant phenotype supports the annotation.', family: 'experimental' },
  HGI: { name: 'High-throughput genetic interaction', explanation: 'A high-throughput genetic interaction supports the annotation.', family: 'experimental' },
  HEP: { name: 'High-throughput expression pattern', explanation: 'A high-throughput expression study supports the annotation.', family: 'experimental' },
  IBA: { name: 'Inferred from biological aspect of ancestor', explanation: 'Phylogenetic inference from an ancestral biological aspect.', family: 'phylogenetic' },
  IBD: { name: 'Inferred from biological aspect of descendant', explanation: 'Phylogenetic inference from a descendant biological aspect.', family: 'phylogenetic' },
  IKR: { name: 'Inferred from key residues', explanation: 'Phylogenetic inference informed by key residues.', family: 'phylogenetic' },
  IRD: { name: 'Inferred from rapid divergence', explanation: 'Phylogenetic inference based on rapid divergence.', family: 'phylogenetic' },
  ISS: { name: 'Inferred from sequence or structural similarity', explanation: 'Sequence or structural similarity supports the annotation.', family: 'computational' },
  ISO: { name: 'Inferred from sequence orthology', explanation: 'Orthology supports the annotation.', family: 'computational' },
  ISA: { name: 'Inferred from sequence alignment', explanation: 'A sequence alignment supports the annotation.', family: 'computational' },
  ISM: { name: 'Inferred from sequence model', explanation: 'A sequence model supports the annotation.', family: 'computational' },
  IGC: { name: 'Inferred from genomic context', explanation: 'Genomic context supports the annotation.', family: 'computational' },
  RCA: { name: 'Reviewed computational analysis', explanation: 'A curator-reviewed computational analysis supports the annotation.', family: 'computational' },
  TAS: { name: 'Traceable author statement', explanation: 'A statement traceable to a cited publication supports the annotation.', family: 'author' },
  NAS: { name: 'Non-traceable author statement', explanation: 'An author statement without a directly traceable publication supports the annotation.', family: 'author' },
  IC: { name: 'Inferred by curator', explanation: 'A curator inferred the annotation from other available evidence.', family: 'curator' },
  ND: { name: 'No biological data available', explanation: 'The source explicitly records that biological data were not available.', family: 'curator' },
  IEA: { name: 'Inferred from electronic annotation', explanation: 'An automated electronic method produced the annotation.', family: 'automatic' },
};

const REACTOME_EVIDENCE: Record<string, EvidenceDefinition> = {
  TAS: {
    name: 'Traceable author statement',
    explanation: 'Reactome export evidence code. The association is supported by a traceable author statement; this release does not provide a per-association PMID.',
    family: 'author',
  },
  IEA: {
    name: 'Inferred from electronic annotation',
    explanation: 'Reactome export evidence code. The association was inferred electronically rather than recorded as a direct experiment.',
    family: 'automatic',
  },
};

// Categorical colours identify source codes; they do not encode an evidence ranking.
const GO_CODE_COLOURS: Record<string, string> = {
  EXP: '#39713e', IDA: '#08796b', IPI: '#8050a4', IMP: '#315fac', IGI: '#a13e6b', IEP: '#8a6415',
  HTP: '#547238', HDA: '#237782', HMP: '#5555a4', HGI: '#925875', HEP: '#9a6229',
  IBA: '#7445a5', IBD: '#934495', IKR: '#575d9d', IRD: '#7c596d',
  ISS: '#356d8c', ISO: '#34659c', ISA: '#4c6291', ISM: '#4c7480', IGC: '#477160', RCA: '#626d38',
  TAS: '#98621c', NAS: '#9a5334', IC: '#71603f', ND: '#707477', IEA: '#546579',
};

function EvidenceLabel({ code, definition, colour }: { code: unknown; definition: EvidenceDefinition; colour?: string }) {
  const value = String(code || 'Unspecified');
  return <span className={`ov-evidence ov-evidence-${definition.family}`} data-evidence-code={value} style={colour ? {
    '--evidence-fg': colour, '--evidence-bg': `color-mix(in srgb, ${colour} 8%, white)`,
    '--evidence-line': `color-mix(in srgb, ${colour} 32%, white)`,
  } as CSSProperties : undefined} title={`${definition.name}. ${definition.explanation}`}>
    <strong>{value}</strong><span>{definition.family==='automatic'?'Automatic · ':''}{definition.name}</span>
  </span>;
}

export function GoEvidenceLabel({ code }: { code: unknown }) {
  const value = String(code || 'Unspecified');
  const definition = GO_EVIDENCE[value] ?? { name: 'Source evidence code', explanation: 'The code is retained exactly as supplied by the source.', family: 'other' as const };
  return <EvidenceLabel code={value} definition={definition} colour={GO_CODE_COLOURS[value] ?? '#56677a'} />;
}

export function ReactomeEvidenceLabel({ code }: { code: unknown }) {
  const value = String(code || 'Unspecified');
  const definition = REACTOME_EVIDENCE[value] ?? { name: 'Reactome source code', explanation: 'The code is retained exactly as supplied by the Reactome export.', family: 'other' as const };
  return <EvidenceLabel code={value} definition={definition} />;
}

export function GoEvidenceHelp() {
  return <p className="ov-evidence-help">Colours distinguish evidence codes; they are not a confidence ranking. <LinkOut href="https://geneontology.org/docs/guide-go-evidence-codes/">GO evidence-code guide</LinkOut></p>;
}

function referenceUrl(reference: string) {
  const pmid = reference.match(/^PMID:(\d+)$/i);
  if (pmid) return `https://pubmed.ncbi.nlm.nih.gov/${pmid[1]}/`;
  const goReference = reference.match(/^GO_REF:(\d+)$/i);
  if (goReference) return `https://geneontology.org/GO_REF/${goReference[1]}`;
  const doi = reference.match(/^DOI:(.+)$/i);
  if (doi) return `https://doi.org/${doi[1]}`;
  const reactome = reference.match(/^Reactome:(R-[A-Z]{3}-\d+)$/i);
  if (reactome) return `https://reactome.org/content/detail/${reactome[1]}`;
  return undefined;
}

function referenceTokens(value: unknown): string[] {
  if (Array.isArray(value)) return value.flatMap(referenceTokens);
  if (value == null || value === '') return [];
  return String(value).split(/[|;,]\s*/).map(item => item.trim()).filter(Boolean);
}

export function GoReferenceLinks({ value }: { value: unknown }) {
  const references = referenceTokens(value);
  if (!references.length) return <span className="ov-reference-empty">No literature reference supplied</span>;
  return <span className="ov-reference-links">{references.map((reference, index) => <LinkOut key={`${reference}:${index}`} href={referenceUrl(reference)}>{reference}</LinkOut>)}</span>;
}
