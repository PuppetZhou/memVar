"use client";

import { useMemo, useState } from "react";
import { Identifier, ProteinOverviewResponse } from "../lib/api";
import { formatTermLabel } from "../lib/display-labels";
import { ActionLink } from "./ui/action-link";
import { Button } from "./ui/button";
import { Disclosure } from "./ui/disclosure";

type IdentifierGroup = Identifier & { mappedIsoforms: string[] };

function identifierValue(identifier: Identifier) {
  return identifier.identifier_full ?? identifier.identifier_label ?? identifier.isoform_id ?? identifier.identifier_base ?? "Not available";
}

function deduplicate(identifiers: Identifier[]): IdentifierGroup[] {
  const groups = new Map<string, IdentifierGroup>();
  for (const identifier of identifiers) {
    const key = [identifier.identifier_database, identifier.identifier_type, identifierValue(identifier)].join("|");
    const current = groups.get(key);
    const isoforms = new Set(current?.mappedIsoforms ?? []);
    if (identifier.isoform_id) isoforms.add(identifier.isoform_id);
    groups.set(key, { ...(current ?? identifier), mappedIsoforms: [...isoforms].sort() });
  }
  return [...groups.values()];
}

function externalUrl(identifier: Identifier, accession: string) {
  const value = identifierValue(identifier);
  const base = identifier.identifier_base ?? value;
  if (identifier.identifier_database === "UniProt") {
    if (["uniprot_accession", "isoform_id"].includes(identifier.identifier_type)) return `https://www.uniprot.org/uniprotkb/${encodeURIComponent(value)}`;
    if (identifier.identifier_type === "entry_name") return `https://www.uniprot.org/uniprotkb/${encodeURIComponent(accession)}`;
  }
  if (identifier.identifier_database === "HGNC") return `https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/${encodeURIComponent(value)}`;
  if (identifier.identifier_database === "GeneID") return `https://www.ncbi.nlm.nih.gov/gene/${encodeURIComponent(value)}`;
  if (identifier.identifier_database === "Ensembl") {
    if (base.startsWith("ENSG")) return `https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=${encodeURIComponent(base)}`;
    if (base.startsWith("ENST")) return `https://www.ensembl.org/Homo_sapiens/Transcript/Summary?t=${encodeURIComponent(base)}`;
    if (base.startsWith("ENSP")) return `https://www.ensembl.org/Homo_sapiens/Transcript/ProteinSummary?p=${encodeURIComponent(base)}`;
  }
  if (identifier.identifier_database === "RefSeq") {
    if (/^[NX]P_/.test(base)) return `https://www.ncbi.nlm.nih.gov/protein/${encodeURIComponent(base)}`;
    if (/^[NX]M_/.test(base)) return `https://www.ncbi.nlm.nih.gov/nuccore/${encodeURIComponent(base)}`;
  }
  return null;
}

function IdentifierEntry({ identifier, accession }: { identifier: IdentifierGroup; accession: string }) {
  const value = identifierValue(identifier);
  const url = externalUrl(identifier, accession);
  return <li className="identifier-entry">
    <div><span className="identifier-kind">{formatTermLabel(identifier.identifier_type)}</span><code>{value}</code></div>
    {url && <div className="identifier-actions"><ActionLink href={url} external aria-label={`Open ${value} in ${identifier.identifier_database ?? "source database"}`}>Open</ActionLink></div>}
    {identifier.mappedIsoforms.length > 0 && identifier.identifier_type === "gene_stable_id" && <small>Mapped isoforms: {identifier.mappedIsoforms.join(", ")}</small>}
  </li>;
}

export function IdentifiersPanel({ protein }: { protein: ProteinOverviewResponse }) {
  const [showAllAliases, setShowAllAliases] = useState(false);
  const [showIsoforms, setShowIsoforms] = useState(false);
  const grouped = useMemo(() => deduplicate(protein.identifiers), [protein.identifiers]);
  const geneIds = grouped.filter((item) => item.identifier_type === "gene_stable_id");
  const aliases = grouped.filter((item) => ["gene_primary", "gene_synonym"].includes(item.identifier_type));
  const isoformItems = grouped.filter((item) => ["isoform_id", "isoform_synonym", "transcript_id", "protein_id"].includes(item.identifier_type));
  const isoformGroups = new Map<string, IdentifierGroup[]>();
  for (const item of isoformItems) {
    const key = item.isoform_id ?? "Unassigned mappings";
    isoformGroups.set(key, [...(isoformGroups.get(key) ?? []), item]);
  }

  const primaryIdentifiers: IdentifierGroup[] = [
    { isoform_id: null, identifier_type: "uniprot_accession", identifier_database: "UniProt", identifier_full: protein.uniprot_accession, identifier_base: protein.uniprot_accession, identifier_version: null, alias_type: null, identifier_label: null, mappedIsoforms: [] },
    ...grouped.filter((item) => item.identifier_type === "entry_name"),
    ...grouped.filter((item) => item.identifier_type === "gene_primary"),
  ];

  return <section className="overview-section identifiers-panel" aria-labelledby="identifiers-heading">
    <div className="section-heading"><p className="eyebrow">Searchable mappings</p><h2 id="identifiers-heading">Identifiers and aliases</h2><p>{protein.identifiers.length.toLocaleString()} source mappings, organized without discarding one-to-many relationships.</p></div>
    <div className="identifier-sections">
      <article className="identifier-section"><h3>Primary identity</h3><ul>{primaryIdentifiers.map((item) => <IdentifierEntry key={`${item.identifier_type}-${identifierValue(item)}`} identifier={item} accession={protein.uniprot_accession} />)}</ul></article>
      <article className="identifier-section"><h3>Gene identifiers <span>{geneIds.length}</span></h3>{geneIds.length ? <ul>{geneIds.map((item) => <IdentifierEntry key={`${item.identifier_database}-${identifierValue(item)}`} identifier={item} accession={protein.uniprot_accession} />)}</ul> : <p className="empty-value">No stable gene identifiers are available.</p>}</article>
      <article className="identifier-section identifier-aliases"><h3>Gene aliases <span>{aliases.length}</span></h3>{aliases.length ? <><ul className="alias-chip-list">{aliases.slice(0, showAllAliases ? aliases.length : 8).map((item) => <li key={`${item.identifier_type}-${identifierValue(item)}`}><span>{identifierValue(item)}</span><small>{formatTermLabel(item.identifier_type)}</small></li>)}</ul>{aliases.length > 8 && <Button variant="quiet" type="button" aria-expanded={showAllAliases} onClick={() => setShowAllAliases((value) => !value)}>{showAllAliases ? "Show fewer" : `Show all ${aliases.length} aliases`}</Button>}</> : <p className="empty-value">No aliases are available.</p>}</article>
      <article className="identifier-section identifier-isoforms"><Disclosure id="isoform-identifier-groups" open={showIsoforms} onToggle={() => setShowIsoforms((value) => !value)} label={<span>Isoforms and transcripts <strong>· {isoformItems.length}</strong></span>}>
        <div className="isoform-groups">{[...isoformGroups.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([isoform, items]) => <section key={isoform}><h4>{isoform}</h4><ul>{items.map((item) => <IdentifierEntry key={`${item.identifier_database}-${item.identifier_type}-${identifierValue(item)}`} identifier={item} accession={protein.uniprot_accession} />)}</ul></section>)}</div>
      </Disclosure></article>
    </div>
  </section>;
}
