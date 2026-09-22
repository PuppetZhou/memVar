import catalogSources from '../../../config/catalog_sources.json';

/**
 * Public-facing explanations, based on the implemented protein-page controls and
 * confirmed source contracts. Counts, releases and build snapshots come only
 * from /api/catalog/statistics; do not duplicate them in this file.
 *
 * Maintainer evidence: modules/foundation/docs/rules.md;
 * Web/docs/plan/{protein_overview,variant,context,expression,disease}.md;
 * Web/frontend/src/components/HelpGuide.tsx and AlphaGenome.tsx.
 */
export interface DocumentationItem {
  title: string;
  body: string;
  href?: string;
}
export interface DocumentationSection {
  id: string;
  title: string;
  intro?: string;
  items: DocumentationItem[];
}
export interface SourceDescription {
  id: string;
  name: string;
  group: string;
  description: string;
  url?: string;
}

export const documentationIntro = {
  title: 'Explore membrane proteins in context',
  lead: 'memVar connects human membrane proteins with sequence features, genetic variation, structures and molecular evidence.',
  paragraphs: [
    'Start from a protein or gene, then move between its canonical sequence, variants, membrane features, expression, regulatory associations, interactions and disease context.',
    'Each view preserves the source and the object it describes. A protein annotation, a gene-level association, a structural observation and a computational prediction are different kinds of evidence.',
  ],
};

export const documentationSections: DocumentationSection[] = [
  {
    id: 'getting-started', title: 'Find, inspect, compare',
    items: [
      {title: 'Find a protein', body: 'Search by a gene name or UniProt accession, such as EGFR or P00533. Membrane class and location filters help narrow the protein list.', href: '/search?query=EGFR'},
      {title: 'Start with the overview', body: 'Basic Information summarizes identity, cellular location, membrane association, GO annotations and molecular context. Open a card to inspect the original records and source links.', href: '/protein/P00533'},
      {title: 'Follow a position', body: 'Use the Sequence Browser to select a residue range, resize the window or return to the full protein. Open a feature, clustered mark or residue to inspect its annotations.'},
      {title: 'Compare evidence', body: 'Select variant predictors, explore source-specific records and use collection, tissue or interaction filters. Each table opens further evidence without combining different sources into a new verdict.'},
    ],
  },
  {
    id: 'scope', title: 'What is included?',
    intro: 'The protein set and its membrane annotations serve different purposes.',
    items: [
      {title: 'Protein inclusion', body: 'The project starts from reviewed entries in the UniProt human reference proteome carrying the Membrane keyword. The confirmed project scope retains entries with a source HGNC reference. A source HGNC reference missing from the local HGNC snapshot is retained with its unresolved status.'},
      {title: 'Membrane annotation sources', body: 'UniProt membrane labels describe association mechanisms. TOPDB, HTP, structural resources and DeepTMHMM2 add topology or membrane context to the selected proteins; their coverage is not a separate union used to expand the protein set.'},
      {title: 'Variant scope', body: 'The current catalog contains the selected single-nucleotide variants with coding-protein consequences and a reported protein change. It is not a catalog of every indel or every possible non-coding variant.'},
      {title: 'Published snapshots', body: 'Data overview summarizes coverage; this documentation lists current service snapshots and source versions. Source release names and local processing snapshots are distinguished; unavailable release metadata remains unspecified.', href: '/results'},
    ],
  },
  {
    id: 'protein-and-sequence', title: 'Protein, sequence and structure',
    items: [
      {title: 'Basic Information', body: 'Identity and membrane features use the linked protein context. DeepTMHMM2 is shown as a separate prediction source. GO previews organize the three aspects; Reactome pathways and reaction or ligand records open their own details.'},
      {title: 'Sequence Browser', body: 'Variant density, domains and regions, membrane features, functional sites, PTMs, secondary structure, conservation and predicted interfaces share one canonical sequence window. The full sequence atlas provides a residue-by-residue view.'},
      {title: 'PTMs and overlapping features', body: 'Compact markers can group nearby annotations for readability. Opening a marker preserves the underlying positions, feature types and sources. PTMD2 disease-associated records are available in Diseases & phenotypes.'},
      {title: 'Structure context', body: 'Inspect the available structures and coloring options alongside sequence evidence. Structural observations retain their model, chain and residue context; sequence association alone does not validate a structural residue mapping.'},
      {title: 'Conservation and interfaces', body: 'JSD is a conservation score, not pathogenicity. Its mid-scale guide is a visual reference. PeSTo and SPPIDER-seq retain model, fragment and partner context, rather than being treated as independent experimental confirmations.'},
    ],
  },
  {
    id: 'variants', title: 'Read a variant record',
    items: [
      {title: 'Genomic and protein identity', body: 'The catalog separates the genomic allele and GRCh38 position from the protein substitution and residue position. A row has a selected gene and transcript context; one genomic variant can therefore appear in more than one row.'},
      {title: 'Transcript selection', body: 'Published representative consequences prefer MANE Select, with Ensembl canonical used where the confirmed rules permit it. The canonical filter refers to the VEP transcript flag; it does not prove a match to the UniProt canonical sequence.'},
      {title: 'Clinical evidence', body: 'Open ClinVar or other source records to inspect their original assertions. Germline clinical classification, oncogenicity, somatic clinical impact and computational predictions remain distinct.'},
      {title: 'Predictor selection', body: 'Choose the score fields shown in the table and open the prediction panels for source scales and interpretation. AlphaMissense is among the default fields. Different tools are not independent votes, and memVar does not derive a combined clinical classification.'},
      {title: 'Population frequency', body: 'Allele frequency, allele count and allele number retain their source population context. A frequency of zero differs from an unavailable value. Rarity by itself is not a pathogenicity classification.'},
    ],
  },
  {
    id: 'biological-context', title: 'Explore biological context',
    items: [
      {title: 'Expression', body: 'Choose a normal tissue, cancer, cell-line or single-cell context, then a measurement collection and a specific tissue or cell. RNA and protein assays retain their own units; overview bars describe record coverage, not expression magnitude.'},
      {title: 'Regulatory associations', body: 'Browse QTL sources, molecular types and tissue contexts. Read the phenotype, assembly, effect measure and P value together. The body map groups source labels for navigation; it is not a harmonized tissue ontology or proof of causality.'},
      {title: 'AlphaGenome', body: 'The prediction explorer shows reference-sequence tracks with assay, tissue or cell, strand and scale. These tracks are separate from measured expression and from alternate-allele scoring in the Variant Browser. Tracks use the available stored resolution; zooming does not recover finer data.'},
      {title: 'Protein interactions', body: 'The category chart summarizes the current records. Use full-source or project collections and table filters to inspect evidence. Collections overlap. IntAct mutation records describe changes to interactions, not clinical pathogenicity, and their source coordinates are not verified canonical variant mappings.'},
      {title: 'Diseases & phenotypes', body: 'Choose a source to inspect gene–disease assertions, inheritance and phenotype evidence. Disease-level phenotypes do not assign a clinical classification to each variant. PTMD2 preserves its original PTM–disease text and mapping status.'},
    ],
  },
  {
    id: 'interpreting-evidence', title: 'Interpret values and evidence',
    items: [
      {title: 'Keep the evidence type visible', body: 'Curated annotations, experimental measurements, structural observations, associations and predictions answer different questions. Sources may cite the same underlying study; more records do not automatically mean more independent evidence.'},
      {title: 'Coordinates and mappings', body: 'Protein tracks use one-based residue positions on the selected canonical sequence. Genomic alleles use the displayed assembly. Original structure or source coordinates are kept separately. Records without a verified canonical mapping can remain available in source or catalog details.'},
      {title: 'Missing is not zero', body: 'A dash or an unavailable status indicates absent or unresolved information. A numerical zero is retained when supplied by the source. No annotation or no local record does not establish biological absence.'},
      {title: 'Read the unit and denominator', body: 'Counts may refer to proteins, variants, transcript consequences, source records, dataset–context pairs or structure residues. Overlapping source and ontology groups are not necessarily additive. Numeric colors and source badges do not create scientific thresholds.'},
      {title: 'Return to the source', body: 'Use record links, identifiers and source evidence to check the original context. Disease associations and model outputs support research interpretation; they are not a substitute for a variant-specific clinical assessment.'},
    ],
  },
  {
    id: 'api', title: 'Read-only API',
    intro: 'The same service exposes protein, annotation and evidence endpoints used by the website.',
    items: [
      {title: 'Interactive endpoint documentation', body: 'Open the API reference for available endpoints, required parameters, filters and response schemas.', href: '/docs'},
      {title: 'OpenAPI specification', body: 'The machine-readable specification describes the currently served API.', href: '/openapi.json'},
      {title: 'Pagination and scope', body: 'Use the pagination parameters documented for each endpoint. Some endpoints use offsets and others return a next cursor. An individual page is not an export of the complete dataset.'},
    ],
  },
];

export const apiExamples = [
  {title: 'Search for EGFR', path: '/api/proteins?query=EGFR&limit=10', description: 'Protein identities matching the search term.'},
  {title: 'Protein overview', path: '/api/proteins/P00533/overview', description: 'Identity, source annotations and links for one protein.'},
  {title: 'Sequence annotations', path: '/api/proteins/P00533/sequence', description: 'Canonical sequence context and available annotation tracks.'},
  {title: 'Variant records', path: '/api/proteins/P00533/variants?limit=10', description: 'A page of selected transcript consequences with linked variant evidence.'},
];

// The shared source directory is bundled locally so this guide also works if the API is unavailable.
// Versions remain API-only; source names, groups and URLs have one maintenance location.
const sourceExplanations: {id:string;description:string}[] = [
  {id:'uniprot',description:'Reviewed protein identity, canonical sequences, features, cellular location and membrane annotations.'},
  {id:'hgnc',description:'Gene identities connecting protein entries to gene-level evidence.'},
  {id:'ensembl',description:'Genomic and transcript references, variant consequences and transcript flags.'},
  {id:'go',description:'Molecular function, biological process and cellular component annotations; GO-slim previews retain original term evidence.'},
  {id:'reactome',description:'Source-defined pathways linked to protein context.'},
  {id:'rhea',description:'Biochemical reaction identities and source links.'},
  {id:'gtopdb',description:'Target and ligand interaction records.'},
  {id:'deeptmhmm2',description:'Sequence-based predictions of protein type, topology, signal peptides and membrane context.'},
  {id:'topdb',description:'Source topology and its supporting evidence, retained separately.'},
  {id:'htp',description:'Human transmembrane topology, method outputs and supporting source records.'},
  {id:'tmalphafold',description:'Source membrane topology and geometry with separate CCTOP and structure-based method context.'},
  {id:'pdbtm',description:'Structure- and chain-specific transmembrane topology records.'},
  {id:'alphafold',description:'Available local predicted structure models with sequence validation and model confidence.'},
  {id:'opm',description:'Structure-specific membrane orientation and residue geometry.'},
  {id:'mplid',description:'Structure-residue lipid-contact observations with original distance and source labels.'},
  {id:'biodolphin',description:'Protein–ligand instances, chemical identities and source binding-site records.'},
  {id:'pfam',description:'Domain annotations with source identifiers and canonical sequence boundaries.'},
  {id:'dbptm',description:'Site-specific post-translational modification annotations and their source evidence.'},
  {id:'glygen',description:'Source PTM annotations retained with protein identity and mapping context.'},
  {id:'proteomescout',description:'Source post-translational modification annotations.'},
  {id:'pesto',description:'Structure-based interface predictions retaining model, fragment and partner context.'},
  {id:'sppider',description:'Sequence-based protein-interface predictions, presented separately from experimental interactions.'},
  {id:'clinvar',description:'Variant source records, original clinical assertions and review status.'},
  {id:'cosmic',description:'Somatic variant source membership and original source annotations.'},
  {id:'gnomad',description:'Population allele frequencies, counts and source population context.'},
  {id:'dbnsfp',description:'Computational scores and source calls, including selected transcript-dependent outputs.'},
  {id:'alphagenome',description:'Variant-scoring outputs and separately presented reference-sequence prediction tracks.'},
  {id:'hpa',description:'Tissue, cell, cancer and subcellular observations with source assay and unit.'},
  {id:'gtex',description:'Tissue expression and tissue-specific regulatory association records.'},
  {id:'eqtlgen',description:'Source gene-expression association statistics.'},
  {id:'qtlbase',description:'Molecular QTL records retaining their source phenotype, tissue and effect definitions.'},
  {id:'biogrid',description:'Physical and genetic interaction records and source project collections.'},
  {id:'intact',description:'Molecular interaction evidence, collection memberships and mutation effects.'},
  {id:'clingen',description:'Gene–disease and dosage-sensitivity evidence.'},
  {id:'gencc',description:'Submitted gene–disease assertions and source classifications.'},
  {id:'hpo',description:'Disease-associated phenotype terms and source evidence.'},
  {id:'omim',description:'Gene and phenotype catalog relationships retained as source context.'},
  {id:'ptmd2',description:'Protein-associated PTM–disease records; original source positions are not verified canonical projections.'},
  {id:'dbsnp',description:'Reference variant identifiers connected to the stored genomic allele.'},
  {id:'thermompnn',description:'Predicted protein stability changes with the original model, unit and sign convention.'},
  {id:'mondo',description:'Disease identifiers and ontology relationships used in the confirmed disease mappings.'},
  {id:'medgen',description:'Source disease and phenotype identifiers retained in the disease evidence namespace.'},
];

export const sourceDescriptions: SourceDescription[] = catalogSources.map(source=>({
  ...source, description: sourceExplanations.find(item=>item.id===source.id)?.description??'Source-linked records retain their original evidence and context.',
}));
