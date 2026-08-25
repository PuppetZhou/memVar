export const FIELD_LABELS: Record<string, string> = {
  p_value: "P value", qtl_type: "QTL type", genome_build: "Genome build", moi: "Mode of inheritance",
  hgnc_id: "HGNC ID", gene_id: "NCBI Gene ID", ensembl_gene_id: "Ensembl Gene ID", gene_symbol: "Gene symbol",
  source_database: "Source database", source_release: "Source release", evidence_grain: "Evidence grain",
  site_parse_status: "Site parsing status", source_disease_id: "Source disease ID", disease_id_source: "Disease ID source",
  report_url: "Source report", public_report_url: "Public report", criteria_url: "Criteria report", pmids: "PubMed IDs",
  haploinsufficiency: "Haploinsufficiency", triplosensitivity: "Triplosensitivity", cyto_location: "Cytogenetic location",
  locus_mim_number: "Locus MIM number", mapping_key: "Mapping key", relationship_status: "Relationship status",
  classification_date: "Classification date", curation_date: "Curation date", assertion_date: "Assertion date",
  assertion_id: "Assertion ID", assertion_version: "Assertion version", submitter_id: "Submitter ID", classification_id: "Classification ID",
  unique_source_hpo_count: "Unique HPO terms", hpo_annotation_evidence_count: "HPO annotation records",
  explicitly_absent_annotation_count: "Explicitly absent records", hpo_id: "HPO ID", hpo_name: "HPO term",
  evidence_code: "Evidence code", interaction_category: "Interaction category", context_class: "Context class",
  native_interaction_id: "Native interaction ID", mapped_accessions: "Mapped UniProt accessions",
  mapped_accession_count: "Mapped accession count", source_submission_id: "Source submission ID",
};

export const BIOLOGICAL_TERM_LABELS: Record<string, string> = {
  start_lost: "Start lost", stop_gained: "Stop gained", missense_variant: "Missense variant",
  splice_donor_variant: "Splice donor variant", gene_primary: "Primary gene name", gene_synonym: "Gene synonym",
  isoform_synonym: "Isoform synonym", explicitly_absent: "Explicitly absent", canonical: "Canonical",
  isoform: "Isoform-only", all: "All protein effects", clingen_validity: "ClinGen gene–disease validity",
  clingen_dosage: "ClinGen dosage sensitivity", gencc: "GenCC", omim: "OMIM", hpo: "HPO",
  transcript_id: "Transcript ID", protein_id: "Protein ID", gene_stable_id: "Gene stable ID",
  entry_name: "UniProt entry name", isoform_id: "UniProt isoform ID", uniprot_accession: "UniProt accession",
  apaQTL: "apaQTL", caQTL: "caQTL", eQTL: "eQTL", hQTL: "hQTL", mQTL: "mQTL",
  pQTL: "pQTL", sQTL: "sQTL", stQTL: "stQTL", tuQTL: "tuQTL",
};

const SOURCE_LABELS = new Map<string, string>([
  ["clinvar", "ClinVar"],
  ["cosmic", "COSMIC"],
  ["dbsnp", "dbSNP"],
  ["gnomad", "gnomAD"],
  ["alphamissense", "AlphaMissense"],
]);

const ACRONYMS = new Map<string, string>([
  ["qtl", "QTL"], ["hpo", "HPO"], ["hgnc", "HGNC"], ["moi", "MOI"], ["id", "ID"], ["ids", "IDs"],
  ["rna", "RNA"], ["dna", "DNA"], ["ptm", "PTM"], ["jsd", "JSD"], ["af", "AF"], ["ac", "AC"],
  ["an", "AN"], ["pmid", "PMID"], ["pmids", "PMIDs"], ["gtex", "GTEx"], ["fdr", "FDR"],
  ["eqtl", "eQTL"], ["sqtl", "sQTL"], ["pqtl", "pQTL"], ["ihc", "IHC"], ["mim", "MIM"],
]);

function fallback(value: string) {
  const words = value.replaceAll("_", " ").trim().split(/\s+/).filter(Boolean);
  return words.map((word, index) => ACRONYMS.get(word.toLowerCase()) ?? (index === 0 ? word[0]?.toUpperCase() + word.slice(1) : word.toLowerCase())).join(" ");
}

export function formatFieldLabel(value: string) { return FIELD_LABELS[value] ?? fallback(value); }
export function formatTermLabel(value: string | null | undefined) {
  if (value === null || value === undefined || value === "") return "Not available";
  return BIOLOGICAL_TERM_LABELS[value] ?? fallback(value);
}

export function formatSourceRelease(value: string | null | undefined) {
  if (value === null || value === undefined || value === "" || value === "not_recorded") return "Not recorded";
  if (value === "per_record") return "Recorded per source record";
  return value;
}

export function formatSourceLabel(value: string | null | undefined) {
  if (value === null || value === undefined || value === "") return "Not available";
  return SOURCE_LABELS.get(value.trim().toLowerCase()) ?? value;
}
