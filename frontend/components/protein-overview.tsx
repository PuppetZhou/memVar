"use client";

import { useCallback, useState } from "react";
import { ProteinOverviewResponse } from "../lib/api";
import { useJsonResource } from "../lib/use-json-resource";
import { SearchForm } from "./search-form";
import { SequenceExplorer, SiteSelection } from "./sequence-explorer";
import { StatusMessage } from "./status-message";
import { VariantTable } from "./variant-table";
import { ExpressionPanel } from "./expression-panel";
import { QtlSummary } from "./qtl-summary";
import { InteractionSummary } from "./interaction-summary";
import { DiseasePanel } from "./disease-panel";
import { IdentifiersPanel } from "./identifiers-panel";
import { ReactomeHierarchy } from "./reactome-hierarchy";
import { StructurePanel } from "./structure-panel";
import { AlphaGenomePanel } from "./alphagenome-panel";
import { formatTermLabel } from "../lib/display-labels";
import { AnatomyNavigator } from "./anatomy-navigator";
import { GoEvidence } from "./go-evidence";
import { ProteinSectionNav } from "./protein-section-nav";
import { LazyProteinSection } from "./lazy-protein-section";

function display(value: string | number | null | undefined) {
  return value === null || value === undefined || value === "" ? "Not available" : String(value);
}

function DataRow({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="data-row"><dt>{label}</dt><dd>{children}</dd></div>;
}

function AnnotationTags({ terms, formatTerms = false }: { terms: string[]; formatTerms?: boolean }) {
  return terms.length ? <ul className="tag-list">{terms.map((term) => <li key={term}>{formatTerms ? formatTermLabel(term) : term}</li>)}</ul> : <span className="empty-value">Not available</span>;
}

function OverviewContent({ protein }: { protein: ProteinOverviewResponse }) {
  const annotations = protein.annotation_summary;
  const [selection, setSelection] = useState<SiteSelection>(null);
  const handleSelection = useCallback((next: SiteSelection) => setSelection(next), []);
  const uniProtUrl = `https://www.uniprot.org/uniprotkb/${encodeURIComponent(protein.uniprot_accession)}`;
  const annotationScore = protein.annotation_score === null ? "Not available" : `${protein.annotation_score}/5`;

  return (
    <>
      <section className="protein-header" aria-labelledby="protein-title">
        <div className="protein-heading">
          <p className="eyebrow">Canonical UniProt protein</p>
          <h1 id="protein-title">{protein.gene_symbol ?? protein.uniprot_accession}</h1>
          <p className="protein-title-name">{display(protein.protein_name)}</p>
        </div>
        <div className="protein-key">
          <span className="accession">{protein.uniprot_accession}</span>
          <a className="external-link" href={uniProtUrl} target="_blank" rel="noreferrer">View in UniProt <span aria-hidden="true">↗</span></a>
        </div>
        <div className="header-facts" aria-label="Protein summary">
          <span>{protein.membrane_class ? formatTermLabel(protein.membrane_class) : "Not available"}</span>
          <span>{protein.canonical_sequence.length.toLocaleString()} aa</span>
          <span>{display(protein.protein_existence)}</span>
          <span>Annotation {annotationScore}</span>
        </div>
      </section>

      <ProteinSectionNav />

      <section id="overview" className="overview-section" aria-labelledby="basic-info-heading">
        <div className="section-heading"><p className="eyebrow">Protein overview</p><h2 id="basic-info-heading">Basic information</h2></div>
        <div className="overview-grid">
          <article className="info-card">
            <h3>Identity</h3>
            <dl className="data-list">
              <DataRow label="UniProt accession">{protein.uniprot_accession}</DataRow>
              <DataRow label="Entry name">{display(protein.entry_name)}</DataRow>
              <DataRow label="Gene symbol">{display(protein.gene_symbol)}</DataRow>
              <DataRow label="Protein name">{display(protein.protein_name)}</DataRow>
              <DataRow label="Canonical sequence"><span>{protein.canonical_sequence.sequence_id} · {protein.canonical_sequence.length.toLocaleString()} aa</span>{protein.canonical_sequence.sequence_version !== null && <span className="subvalue">Sequence version {protein.canonical_sequence.sequence_version}</span>}</DataRow>
            </dl>
          </article>
          <article className="info-card">
            <h3>Membrane classification</h3>
            <dl className="data-list">
              <DataRow label="Primary class">{protein.membrane_class ? formatTermLabel(protein.membrane_class) : "Not available"}</DataRow>
              <DataRow label="Class labels"><AnnotationTags terms={protein.all_class_labels} formatTerms /></DataRow>
              <DataRow label="Transmembrane features">{display(protein.transmembrane_count)}</DataRow>
              <DataRow label="Intramembrane features">{display(protein.intramembrane_count)}</DataRow>
              <DataRow label="Lipidation features">{display(protein.lipidation_count)}</DataRow>
              <DataRow label="Lipidation anchor matches">{display(protein.lipidation_anchor_match_count)}</DataRow>
            </dl>
          </article>
        </div>
      </section>

      <IdentifiersPanel protein={protein} />

      <LazyProteinSection label="Structured annotations">
        <section className="overview-section annotation-grid annotation-section" aria-label="Structured annotation">
          <GoEvidence accession={protein.uniprot_accession} />
          <article className="info-card">
            <h2>Subcellular location</h2>
            {annotations.locations.length ? <ul className="location-list">{annotations.locations.map((location, index) => <li key={`${location.location_id}-${location.topology_id}-${index}`}><strong>{display(location.location_name)}</strong>{location.topology_name && <span>Topology: {location.topology_name}</span>}{location.orientation_name && <span>Orientation: {location.orientation_name}</span>}</li>)}</ul> : <p className="empty-value">Not available</p>}
            {annotations.locations_total > annotations.locations.length && <p className="list-note">Showing {annotations.locations.length} of {annotations.locations_total} location records.</p>}
          </article>
          <ReactomeHierarchy accession={protein.uniprot_accession} />
        </section>
        <p className="data-note">Structured annotations come from the website data layer. This page does not infer a free-text function summary from these records.</p>
      </LazyProteinSection>

      <LazyProteinSection id="sequence" label="Sequence explorer"><SequenceExplorer accession={protein.uniprot_accession} length={protein.canonical_sequence.length} onSelectionChange={handleSelection} /></LazyProteinSection>
      <LazyProteinSection id="structure" label="Protein structure"><StructurePanel accession={protein.uniprot_accession} selection={selection} onSelectionChange={handleSelection} /></LazyProteinSection>
      <LazyProteinSection id="variants" label="Variant summary"><section id="variants" className="overview-section" aria-labelledby="variants-heading">
        <div className="section-heading"><p className="eyebrow">M2 variant evidence</p><h2 id="variants-heading">Variant summary</h2></div>
        <p className="section-intro">One genomic variant per main row. Open ClinVar, COSMIC, stability, or another source directly, then inspect one independent evidence branch at a time.</p>
        <VariantTable accession={protein.uniprot_accession} selection={selection} compact />
      </section></LazyProteinSection>
      <LazyProteinSection id="anatomy" label="Anatomy navigator"><AnatomyNavigator accession={protein.uniprot_accession} /></LazyProteinSection>
      <LazyProteinSection id="expression" label="Expression"><ExpressionPanel accession={protein.uniprot_accession} /></LazyProteinSection>
      <LazyProteinSection id="qtl" label="QTL summary"><QtlSummary accession={protein.uniprot_accession} /></LazyProteinSection>
      <LazyProteinSection id="alphagenome" label="AlphaGenome regulatory landscape"><AlphaGenomePanel accession={protein.uniprot_accession} /></LazyProteinSection>
      <LazyProteinSection id="interactions" label="Interaction summary"><InteractionSummary accession={protein.uniprot_accession} /></LazyProteinSection>
      <LazyProteinSection id="diseases" label="Disease evidence"><DiseasePanel accession={protein.uniprot_accession} /></LazyProteinSection>
    </>
  );
}

export function ProteinOverview({ accession }: { accession: string }) {
  const state = useJsonResource<ProteinOverviewResponse>(
    `/proteins/${encodeURIComponent(accession)}`,
    "Unable to load this protein.",
  );

  return (
    <>
      <div className="page-search"><SearchForm initialQuery={accession} /></div>
      {state.kind === "loading" && <StatusMessage title="Loading protein overview">Retrieving the canonical protein record and its structured annotations.</StatusMessage>}
      {state.kind === "error" && <StatusMessage title="Protein overview unavailable" tone="error">{state.error}</StatusMessage>}
      {state.kind === "ready" && <OverviewContent protein={state.response} />}
    </>
  );
}
