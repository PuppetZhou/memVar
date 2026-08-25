import Image from "next/image";
import { Activity, Dna, Fingerprint, Network } from "lucide-react";
import { SearchForm } from "../components/search-form";

const supportedIdentifiers = [
  "UniProt accession",
  "gene symbol or alias",
  "HGNC identifier",
  "Ensembl gene",
  "transcript or isoform ID",
];

const evidenceJourney = [
  { code: "01", group: "Foundation", title: "Sequence & structure", detail: "Canonical sequence, mapped sites, domains, and available structural context.", href: "/protein/P00533#sequence", Icon: Fingerprint },
  { code: "02", group: "Genetic evidence", title: "Variants", detail: "Protein-linked variant evidence kept separate by source and consequence.", href: "/protein/P00533#variants", Icon: Dna },
  { code: "03", group: "Molecular context", title: "Tissue & regulation", detail: "Expression modalities and molecular QTL evidence without a combined scale.", href: "/protein/P00533#expression", Icon: Activity },
  { code: "04", group: "Network & clinical", title: "Interactions & disease", detail: "Source-specific interaction and disease evidence for biological context.", href: "/protein/P00533#interactions", Icon: Network },
];

export default function HomePage() {
  return <main id="main-content">
    <section className="hero home-hero" aria-labelledby="home-heading">
      <div className="shell home-hero-grid">
        <div className="hero-content">
          <p className="eyebrow">Reviewed human membrane proteins</p>
          <h1 id="home-heading">Evidence, organized around the canonical protein.</h1>
          <p className="hero-copy">memVar is a canonical protein-centric evidence portal for exploring reviewed human membrane proteins—from sequence and variants to expression, regulation, interactions, and disease evidence.</p>
          <SearchForm className="hero-search" autoFocus />
          <div className="hero-search-support"><a className="example-link" href="/protein/P00533"><span aria-hidden="true">→</span> Open verified example: EGFR / P00533</a><p>Search can return candidate selection when one identifier legitimately maps to more than one protein entry.</p></div>
        </div>
        <aside className="home-evidence-overview" aria-labelledby="evidence-overview-heading">
          <p className="eyebrow">How to read memVar</p>
          <h2 id="evidence-overview-heading">Keep evidence in its own context.</h2>
          <figure className="home-evidence-figure">
            <Image src="/assets/biorender-memvar-overview.jpg" width={2752} height={1536} sizes="(max-width: 920px) calc(100vw - 3rem), 480px" priority alt="Membrane protein centered among canonical sequence and paired sites, protein variants, tissue expression, regulatory genomics, protein interactions, and independent disease evidence records." />
            <figcaption><a href="https://www.biorender.com/" target="_blank" rel="noreferrer">Created with BioRender.com</a></figcaption>
          </figure>
          <div className="home-evidence-boundary"><strong>Interpret by source</strong><p>Source-specific evidence stays separate, and predictions are not clinical conclusions.</p></div>
        </aside>
      </div>
    </section>

    <section className="shell home-search-guide" aria-labelledby="search-guide-heading">
      <div><p className="eyebrow">Start with an identifier</p><h2 id="search-guide-heading">Find the entry before comparing the evidence.</h2><p>Use a protein, gene, alias, or stable identifier. Exact mappings go directly to a protein page; valid one-to-many mappings stay visible for you to choose.</p></div>
      <ul className="home-identifier-list" aria-label="Supported identifiers">{supportedIdentifiers.map((identifier) => <li key={identifier}>{identifier}</li>)}</ul>
    </section>

    <section className="home-journey" aria-labelledby="journey-heading">
      <div className="shell">
        <div className="home-section-heading"><div><p className="eyebrow">Protein evidence journey</p><h2 id="journey-heading">Follow one protein across connected evidence domains.</h2></div><p>These links open the EGFR example at the corresponding protein-page section.</p></div>
        <ol className="evidence-journey-list">{evidenceJourney.map((domain, index) => <li key={domain.title} className={`journey-domain journey-${index + 1}`}><span className="journey-index" aria-hidden="true">{domain.code}</span><span className="journey-connector" aria-hidden="true" /><a href={domain.href}><span className="journey-card-heading"><span className="journey-icon"><domain.Icon aria-hidden="true" size={21} strokeWidth={1.9} /></span><span><small>{domain.group}</small><strong>{domain.title}</strong></span></span><span>{domain.detail}</span><em>Explore EGFR</em></a></li>)}</ol>
      </div>
    </section>

    <section className="shell home-interpretation" aria-labelledby="interpretation-heading">
      <div><p className="eyebrow">Interpretation boundary</p><h2 id="interpretation-heading">A portal for inspection, not a combined score.</h2></div>
      <p>memVar does not merge expression modalities, vote across disease sources, or turn predictions into clinical conclusions. Use the linked source-specific records and their stated limitations when interpreting a result.</p>
      <a href="/about/data-sources">Read data sources and interpretation <span aria-hidden="true">→</span></a>
    </section>
  </main>;
}
