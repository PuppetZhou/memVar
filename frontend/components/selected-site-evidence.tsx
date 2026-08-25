"use client";

import { type ReactNode, useEffect, useState } from "react";

import { getJson } from "../lib/api-client";
import {
  formatDdg,
  partnerFor,
  percentage,
  SiteEvidenceSummary,
  stabilityDirectionLabel,
} from "../lib/site-evidence";
import { formatSourceLabel, formatTermLabel } from "../lib/display-labels";
import { allCovalentPairsAreDisulfide, covalentBondLabel } from "../lib/covalent-bonds";
import { SourceBadge } from "./ui/source-badge";

type LoadState = { kind: "loading" | "error" | "ready"; data?: SiteEvidenceSummary; error?: string };

function EvidenceList({ evidence }: { evidence: SiteEvidenceSummary["covalent_pairs"][number]["evidence"] }) {
  if (!evidence.length) return <span className="empty-value">No evidence identifiers recorded.</span>;
  return <ul className="site-evidence-inline-list">{evidence.map((item, index) => <li key={`${item.evidence_code}-${item.source}-${item.identifier}-${index}`}>{[item.evidence_code, item.source, item.identifier].filter(Boolean).join(" · ")}</li>)}</ul>;
}

function OverlapList<T>({ title, items, render }: { title: string; items: T[]; render: (item: T, index: number) => ReactNode }) {
  return <section className="site-evidence-subsection"><h5>{title} <span>{items.length}</span></h5>{items.length ? <ul className="site-evidence-item-list">{items.map((item, index) => <li key={index}>{render(item, index)}</li>)}</ul> : <p className="empty-value">None overlapping this site.</p>}</section>;
}

export function SelectedSiteEvidence({ accession, position, onClose, onClearSelection, onSelectPartner, onOpenVariants }: {
  accession: string;
  position: number;
  onClose: () => void;
  onClearSelection: () => void;
  onSelectPartner: (position: number) => void;
  onOpenVariants: () => void;
}) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    getJson<SiteEvidenceSummary>(`/proteins/${encodeURIComponent(accession)}/sites/${position}/summary`, controller.signal)
      .then((data) => setState({ kind: "ready", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load selected-site evidence." });
      });
    return () => controller.abort();
  }, [accession, position]);

  const data = state.data;
  return <aside className="selected-site-evidence" aria-labelledby="selected-site-evidence-title" aria-busy={state.kind === "loading"}>
    <div className="sequence-preview-heading"><div><p className="eyebrow">Selected canonical site</p><h3 id="selected-site-evidence-title">{data ? `${data.identity.reference_residue}${data.identity.position.toLocaleString()}` : `Residue ${position.toLocaleString()}`}</h3></div><div className="site-evidence-actions"><button type="button" className="quiet-button" onClick={onClose}>Hide panel</button><button type="button" className="quiet-button" onClick={onClearSelection}>Clear selection</button></div></div>
    {state.kind === "loading" && <p role="status">Loading selected-site evidence…</p>}
    {state.kind === "error" && <p className="inline-error" role="alert">{state.error}</p>}
    {data && <div className="site-evidence-body">
      <section><h4>Identity</h4><dl className="site-evidence-metrics"><div><dt>Canonical position</dt><dd>{data.identity.position.toLocaleString()} · {data.identity.reference_residue}</dd></div><div><dt>Sequence version</dt><dd>{data.identity.sequence_version ?? "Not recorded"}</dd></div><div><dt>Coordinate basis</dt><dd>Canonical 1-based</dd></div></dl></section>
      <section><h4>Key signals</h4>
        {data.conservation ? <dl className="site-evidence-metrics"><div><dt>Conservation JSD</dt><dd>{data.conservation.jsd_conservation?.toFixed(4) ?? "Not available"}</dd></div><div><dt>Occupancy / Neff</dt><dd>{percentage(data.conservation.occupancy)} · {data.conservation.neff_site ?? "—"}</dd></div><div><dt>Confidence</dt><dd>{data.conservation.confidence ?? "Not recorded"} · {data.conservation.alignment_scope ?? "scope not recorded"}</dd></div></dl> : <p className="empty-value">No conservation observation at this canonical position.</p>}
        <dl className="site-evidence-metrics"><div><dt>Stability ΔΔG median</dt><dd>{formatDdg(data.stability.ddg_median)}</dd></div><div><dt>IQR</dt><dd>{formatDdg(data.stability.ddg_q25)} to {formatDdg(data.stability.ddg_q75)}</dd></div><div><dt>Min–max / substitutions</dt><dd>{formatDdg(data.stability.ddg_min)} to {formatDdg(data.stability.ddg_max)} · {data.stability.distinct_substitution_count}</dd></div></dl>
        <p className="coordinate-note">Negative ΔΔG is predicted stabilizing; positive is predicted destabilizing. {data.stability.interpretation}</p>
      </section>
      <section><h4>Stability substitutions</h4>{data.stability.substitutions.length ? <div className="site-evidence-table" role="table" aria-label="ThermoMPNN substitutions"><span role="columnheader">Mutation</span><span role="columnheader">ΔΔG</span><span role="columnheader">Direction</span>{data.stability.substitutions.map((item) => <div role="row" key={item.substitution}><b>{item.substitution}</b><span>{formatDdg(item.ddg, 3)}</span><span>{stabilityDirectionLabel(item.direction)}</span></div>)}</div> : <p className="empty-value">No drawable ThermoMPNN prediction at this site.</p>}</section>
      <section><h4>Covalent links {allCovalentPairsAreDisulfide(data.covalent_pairs) && <span className="covalent-section-type">Disulfide bonds (S—S)</span>}</h4>{data.covalent_pairs.length ? <div className="site-evidence-covalent">{data.covalent_pairs.map((pair) => { const partner = partnerFor(pair, data.identity.position); const groupedDisulfide = allCovalentPairsAreDisulfide(data.covalent_pairs); return <article key={pair.pair_id}>{!groupedDisulfide && <p className="covalent-bond-type">{covalentBondLabel(pair.feature_type)}</p>}<strong>{pair.start_endpoint} ↔ {pair.end_endpoint}</strong>{pair.description && <p>{pair.description}</p>}<button type="button" className="quiet-button" onClick={() => onSelectPartner(partner)}>Go to partner {partner.toLocaleString()}</button><EvidenceList evidence={pair.evidence} /></article>; })}</div> : <p className="empty-value">No covalent pair uses this site as an endpoint.</p>}</section>
      <section><h4>Overlapping context</h4>
        <OverlapList title="Topology" items={data.overlaps.topology} render={(item) => <>{formatTermLabel(item.feature_type)} · {item.description ?? "No description"} <small>{item.start}–{item.end} · {item.source}</small></>} />
        <OverlapList title="Pfam" items={data.overlaps.pfam} render={(item) => <>{item.description ?? item.pfam_id ?? item.pfam_accession} <small>{item.start}–{item.end} · Pfam</small></>} />
        <OverlapList title="Functional features" items={data.overlaps.functional} render={(item) => <>{formatTermLabel(item.feature_type)} · {item.description ?? "No description"} <small>{item.start}–{item.end} · {item.source}</small></>} />
        <OverlapList title="PTM" items={data.overlaps.ptm} render={(item) => <>{formatTermLabel(item.ptm_type)} · {item.record_count} record{item.record_count === 1 ? "" : "s"} <small>{item.pmids.length ? `PMID ${item.pmids.join(", ")}` : "No PMID recorded"}</small></>} />
      </section>
      <section><h4>Variants</h4><p className="sequence-preview-summary">Showing {data.variants.showing.toLocaleString()} of {data.variants.total.toLocaleString()} unique canonical variants · {data.variants.clinvar_plp_count.toLocaleString()} with explicit ClinVar P/LP evidence.</p>{Object.keys(data.variants.source_counts).length > 0 && <div className="source-badges">{Object.entries(data.variants.source_counts).map(([source, count]) => <SourceBadge key={source}>{formatSourceLabel(source)} {count}</SourceBadge>)}</div>}{data.variants.preview.length ? <ul className="site-evidence-variant-list">{data.variants.preview.map((item) => <li key={item.variant_key}><strong>{item.hgvsp ?? item.variant_key}</strong><span>{formatTermLabel(item.consequence)}</span>{item.has_clinvar_plp_evidence && <span className="plp-evidence-mark">P/LP evidence</span>}</li>)}</ul> : <p className="empty-value">No canonical variants are anchored at this residue.</p>}<p className="coordinate-note">P/LP means strict ClinVar evidence presence, not cross-disease or cross-RCV consensus.</p><button type="button" className="primary-button" onClick={onOpenVariants}>Open Variant table at residue {data.identity.position}</button></section>
      <section><h4>Provenance and limits</h4><ul className="site-evidence-item-list">{Object.entries(data.provenance).map(([key, value]) => <li key={key}><strong>{formatTermLabel(key)}</strong> · {value}</li>)}</ul></section>
    </div>}
  </aside>;
}
