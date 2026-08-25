"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Activity, ChevronRight, Columns3, Database, ExternalLink, PanelRightOpen, Users, X } from "lucide-react";
import { ClinvarAssertion as ClinvarAssertionRecord, CosmicEvidence, PopulationFrequencyGroup, StabilityPrediction, VariantCatalogSummaryResponse, VariantEffect, VariantEvidenceResponse, VariantFilterOptionsResponse, VariantItem, VariantListResponse, VariantPopulationFrequencyResponse, VariantSummaryCount, VariantSummaryFacet } from "../lib/api";
import { getJson } from "../lib/api-client";
import { SiteSelection } from "./sequence-explorer";
import { StatusMessage } from "./status-message";
import { formatFieldLabel, formatSourceLabel, formatTermLabel } from "../lib/display-labels";
import { clinicalClassification, clinicalClassificationTone } from "../lib/variant-classification";
import { clinvarRecordUrl, normalizedSource, VARIANT_EVIDENCE_BRANCHES, VariantEvidenceBranch } from "../lib/variant-evidence";
import { columnsForPreset, toggleVariantColumn, VARIANT_OPTIONAL_COLUMNS, VariantOptionalColumn, VariantViewPreset, variantTableColumnCount } from "../lib/variant-table-view";
import { SourceBadge } from "./ui/source-badge";
import { SourceContext } from "./ui/source-context";

type Filters = { scope: "canonical" | "isoform" | "all"; consequence: string; source: string; start: string; end: string };
type OpenEvidence = { variantKey: string; branch: VariantEvidenceBranch } | null;

function readable(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not available";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return Math.abs(value) > 0 && Math.abs(value) < .001 ? value.toExponential(3) : value.toLocaleString(undefined, { maximumSignificantDigits: 6 });
  if (Array.isArray(value)) return value.map(readable).join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function DetailFields({ record, omit = [] }: { record: Record<string, unknown>; omit?: string[] }) {
  const omitted = new Set(omit.map((key) => key.toLocaleLowerCase().replaceAll(/[_\s-]/g, "")));
  const entries = Object.entries(record).filter(([key, value]) => value !== null && value !== "" && !["variant_key", "accession_bucket", "page_accession"].includes(key) && !omitted.has(key.toLocaleLowerCase().replaceAll(/[_\s-]/g, "")));
  const termFields = new Set(["consequence", "representative_consequence", "site_parse_status", "variant_class", "impact", "effect_scope", "clinical_significance", "review_status"]);
  return entries.length ? <dl className="detail-fields">{entries.map(([key, value]) => <div key={key}><dt>{formatFieldLabel(key)}</dt><dd>{key === "database_source" && typeof value === "string" ? value.split(";").map(formatSourceLabel).join("; ") : termFields.has(key) && typeof value === "string" ? formatTermLabel(value) : readable(value)}</dd></div>)}</dl> : <p className="empty-value">No fields are available in this source record.</p>;
}

function ClinVarAssertion({ record, index }: { record: ClinvarAssertionRecord; index: number }) {
  const classification = clinicalClassification({ ClinicalSignificance: record.clinical_significance });
  const tone = clinicalClassificationTone(classification);
  const externalUrl = clinvarRecordUrl({ RCVaccession: record.rcv_accession });
  return <article className={`clinvar-assertion tone-${tone}`}>
    <header>
      <div><span>ClinVar assertion {index + 1}</span><strong>{classification ?? "Classification not provided"}</strong></div>
      <div className="clinvar-assertion-actions">
        {record.review_status && <small>{formatTermLabel(record.review_status)}</small>}
        {externalUrl && <a href={externalUrl} target="_blank" rel="noreferrer">Open {record.rcv_accession} in ClinVar <ExternalLink aria-hidden="true" size={15} /></a>}
      </div>
    </header>
    <DetailFields record={record as Record<string, unknown>} omit={["clinical_significance", "rcv_accession", "review_status"]} />
  </article>;
}

function CosmicFact({ record }: { record: CosmicEvidence }) {
  return <article className="cosmic-fact">
    <dl className="cosmic-fact-grid">
      <div><dt>Genome screen sample count</dt><dd>{readable(record.genome_screen_sample_count)}</dd></div>
      <div><dt>MONDO disease IDs</dt><dd>{record.mondo_ids.length ? record.mondo_ids.join(", ") : "Not available"}</dd></div>
      <div><dt>Disease categories</dt><dd>{record.disease_categories.length ? record.disease_categories.map(formatTermLabel).join(", ") : "Not available"}</dd></div>
      <div><dt>CGC tier</dt><dd>{record.cgc_tier === null ? "Not annotated" : `Tier ${record.cgc_tier}`}</dd></div>
    </dl>
    <div className="cgc-role-row"><span>CGC roles</span>{record.cgc_roles.length ? <span className="cgc-role-chips">{record.cgc_roles.map((role) => <span key={role} className={`cgc-role-chip role-${role.toLocaleLowerCase()}`}>{role}</span>)}</span> : <span className="empty-value">Not annotated</span>}</div>
  </article>;
}

function stabilityLabel(prediction: StabilityPrediction) {
  if (prediction.direction === "predicted_stabilizing") return "Predicted stabilizing";
  if (prediction.direction === "predicted_destabilizing") return "Predicted destabilizing";
  return "Small predicted change";
}

function StabilityValue({ prediction }: { prediction: StabilityPrediction | null }) {
  if (!prediction) return <span className="stability-missing">— <small>Not predicted</small></span>;
  const clamped = Math.max(-3, Math.min(3, prediction.ddg));
  const width = Math.abs(clamped) / 3 * 50;
  const className = prediction.ddg <= -0.5 ? "stabilizing" : prediction.ddg >= 0.5 ? "destabilizing" : "small-change";
  return <span className={`stability-value ${className}`} title={`${stabilityLabel(prediction)}; ${prediction.ddg.toFixed(4)} ${prediction.unit}`}>
    <span className="stability-number">{prediction.ddg >= 0 ? "+" : ""}{prediction.ddg.toFixed(2)} <small>{prediction.unit}</small></span>
    <span className="stability-mini-bar" aria-hidden="true"><i style={prediction.ddg < 0 ? { right: "50%", width: `${width}%` } : { left: "50%", width: `${width}%` }} /></span>
    <small>{stabilityLabel(prediction)}</small>
  </span>;
}

function populationAf(value: number): string {
  return value === 0 ? "0" : value.toExponential(2);
}

function populationWidth(value: number | null): number {
  if (value === null || value === 0) return 0;
  const minimumLogAf = -6;
  return Math.max(2, Math.min(100, (Math.log10(value) - minimumLogAf) / -minimumLogAf * 100));
}

function PopulationBar({ group }: { group: PopulationFrequencyGroup }) {
  const width = populationWidth(group.allele_frequency);
  const title = group.allele_frequency === null
    ? `${group.label} (${group.ancestry_group.toUpperCase()}): AF unavailable`
    : `${group.label} (${group.ancestry_group.toUpperCase()}): AF ${populationAf(group.allele_frequency)}`;
  return <li className="population-frequency-bar" data-population={group.ancestry_group} data-available={group.allele_frequency !== null} title={title}>
    <span className="population-frequency-label"><strong>{group.label}</strong><small>{group.ancestry_group.toUpperCase()}</small></span>
    <span className="population-frequency-rail" aria-hidden="true"><i style={{ width: `${width}%` }} /></span>
    <strong>{group.allele_frequency === null ? "—" : populationAf(group.allele_frequency)}</strong>
    <span className="sr-only">{title}</span>
    <small>{group.allele_frequency === null ? "No AF value for this callset" : group.allele_frequency === 0 ? "Explicit source AF = 0" : "Exact source AF"}</small>
  </li>;
}

function PopulationFrequencyBranch({ accession, variantKey }: { accession: string; variantKey: string }) {
  const [state, setState] = useState<{ kind: "loading" | "error" | "ready"; data?: VariantPopulationFrequencyResponse; error?: string }>({ kind: "loading" });
  const [requestVersion, setRequestVersion] = useState(0);
  const [requestedCallset, setRequestedCallset] = useState<"exome" | "genome" | "joint">("joint");
  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    const params = new URLSearchParams({ protein_accession: accession });
    params.set("callset", requestedCallset);
    getJson<VariantPopulationFrequencyResponse>(`/variants/${encodeURIComponent(variantKey)}/population-frequency?${params}`, controller.signal)
      .then((data) => setState({ kind: "ready", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load local population frequencies." });
      });
    return () => controller.abort();
  }, [accession, requestedCallset, variantKey, requestVersion]);
  if (state.kind === "loading") return <section className="variant-branch-panel population-branch"><h4>gnomAD population frequencies</h4><p className="inline-loading" role="status">Loading locally materialized gnomAD frequency groups…</p></section>;
  if (state.kind === "error") return <section className="variant-branch-panel population-branch"><h4>gnomAD population frequencies</h4><div className="variant-detail-error" role="alert"><p>{state.error}</p><button type="button" className="quiet-button" onClick={() => setRequestVersion((value) => value + 1)}>Retry local query</button></div></section>;
  const data = state.data!;
  const callsetControls = data.available_callsets.length > 1 && <div className="population-callset-tabs" role="group" aria-label="gnomAD callset">
    {data.available_callsets.map((callset) => <button key={callset} type="button" aria-pressed={data.callset === callset} onClick={() => setRequestedCallset(callset)}>{formatTermLabel(callset)}</button>)}
  </div>;
  if (data.availability !== "matched") return <section className="variant-branch-panel population-branch"><div className="population-unavailable-heading"><h4>gnomAD population frequencies</h4>{callsetControls}</div><p className="branch-takeaway">{data.message}</p><p className="branch-note">The website reads the complete local gnomAD v4.1 release. A missing row is not represented as AF 0.</p></section>;
  const availableGroups = data.groups.filter((group) => group.allele_frequency !== null).length;
  return <section className="variant-branch-panel population-branch">
    <header className="population-frequency-heading"><div><h4>gnomAD v4.1 genetic ancestry frequency</h4><p>{data.genome_build} · {data.callset} callset · {availableGroups} of {data.total_or_estimate.value} groups with AF</p></div><span>AF</span></header>
    {callsetControls}
    <p className="branch-takeaway">{data.message}</p>
    <p className="branch-note">Exome, genome, and joint callsets remain independent. Bar length uses the same fixed log10 AF scale for every variant; hue identifies the ancestry group. Exact AF is always printed.</p>
    <div className="population-frequency-scale" aria-hidden="true"><span>10⁻⁶</span><span>10⁻³</span><span>1</span></div>
    {data.groups.length ? <ol className="population-frequency-bars" aria-label={`gnomAD ${data.callset} ancestry allele frequency bars`}>{data.groups.map((group) => <PopulationBar key={group.ancestry_group} group={group} />)}</ol> : <p className="empty-value">No gnomAD v4.1 row is available for this variant.</p>}
    <dl className="frequency-grid population-frequency-provenance"><div><dt>Variant key</dt><dd>{variantKey}</dd></div><div><dt>Available measurement</dt><dd>Source AF only</dd></div><div><dt>Unavailable fields</dt><dd>{data.unavailable_fields.map((field) => field.toUpperCase()).join(", ")}</dd></div><div><dt>Displayed callset</dt><dd>{formatTermLabel(data.callset)}</dd></div></dl>
  </section>;
}

function ProteinEffectsBranch({ effects }: { effects: VariantEffect[] }) {
  return effects.length ? <div className="effect-list">{effects.map((effect, index) => <article key={`${effect.uniprot_isoform_id}-${effect.hgvsp}-${index}`} className={effect.effect_scope === "canonical" ? "canonical-effect" : "isoform-effect"}><div><strong>{effect.effect_scope === "canonical" ? "Canonical effect" : "Isoform child effect"}</strong><span>{effect.uniprot_isoform_id ?? effect.uniprot_accession}</span></div><p>{readable(effect.hgvsp)} · {formatTermLabel(effect.consequence)}</p><small>{effect.is_drawable ? `Drawable at canonical position ${effect.protein_start}${effect.protein_end !== effect.protein_start ? `–${effect.protein_end}` : ""}` : `Not drawn: ${formatTermLabel(effect.site_parse_status)}`}{effect.transcript_ids ? ` · Transcript ${effect.transcript_ids}` : ""}</small></article>)}</div> : <p className="empty-value">No protein effects returned.</p>;
}

function VariantBranch({ evidence }: { evidence: VariantEvidenceResponse }) {
  if (evidence.branch === "facts") return <section className="variant-branch-panel facts-branch"><h4>Variant-level facts</h4><p className="branch-takeaway">Stable genomic identity and source fields for this variant. No cross-source interpretation is added.</p><DetailFields record={evidence.core} /></section>;
  if (evidence.branch === "effects") return <section className="variant-branch-panel effects-branch"><h4>Protein effects <span>{evidence.effects.length}</span></h4><p className="branch-takeaway">Canonical effects are presented first; isoform coordinates are not projected onto the canonical sequence.</p><ProteinEffectsBranch effects={evidence.effects} /></section>;
  if (evidence.branch === "stability") return <section className="variant-branch-panel thermompnn-branch"><h4>ThermoMPNN stability prediction</h4>{evidence.prediction ? <div className="thermompnn-card"><StabilityValue prediction={evidence.prediction} /><dl className="frequency-grid"><div><dt>Canonical substitution</dt><dd>{evidence.prediction.ref_aa}{evidence.prediction.canonical_position}{evidence.prediction.alt_aa}</dd></div><div><dt>Structure input</dt><dd>{evidence.prediction.pdb_name}</dd></div><div><dt>Model</dt><dd>{evidence.prediction.model_name}</dd></div><div><dt>Meaning</dt><dd>Predicted thermodynamic stability change</dd></div></dl><p className="branch-note">Negative values are predicted stabilizing and positive values predicted destabilizing. This prediction is not protein fitness, function, pathogenicity, an experimental measurement, or clinical evidence.</p></div> : <p className="empty-value">Not predicted for this protein-specific variant membership.</p>}</section>;
  if (evidence.branch === "clinvar") {
    const first = evidence.assertions[0];
    const sourceContextIsUniform = evidence.assertions.every((record) => record.source_release === first?.source_release && record.evidence_grain === first?.evidence_grain);
    return <section className="variant-branch-panel clinvar-branch"><h4>ClinVar assertions <span>{evidence.assertions.length}</span></h4>{evidence.assertions.length > 0 && sourceContextIsUniform && <SourceContext source="ClinVar" release={first?.source_release} recordGrain={first?.evidence_grain} caveat="Each assertion retains its source classification. memVar does not vote across assertions or combine them with model predictions and COSMIC evidence." className="variant-source-context" />}{evidence.assertions.length > 0 && !sourceContextIsUniform && <p className="branch-note">ClinVar assertions are shown independently; source release or record grain differs across the displayed records and remains visible in each record.</p>}{evidence.assertions.length ? <div className="clinvar-assertion-list">{evidence.assertions.map((record, index) => <ClinVarAssertion key={`${record.rcv_accession}-${index}`} record={record} index={index} />)}</div> : <p className="empty-value">No ClinVar records for this variant and protein.</p>}</section>;
  }
  return <section className="variant-branch-panel cosmic-branch"><h4>COSMIC branch <span>{evidence.records.length}</span></h4><p className="branch-note">Genome screen sample counts are source records, not cancer-specific frequency or pathogenicity. CGC tier and role describe the gene, not the pathogenicity of this variant. No record link is inferred without a stable COSMIC mutation identifier.</p>{evidence.records.length ? <div className="cosmic-fact-list">{evidence.records.map((record, index) => <CosmicFact key={`${record.genome_screen_sample_count}-${record.cgc_tier}-${record.cgc_roles.join("-")}-${index}`} record={record} />)}</div> : <p className="empty-value">No COSMIC records for this variant and protein.</p>}</section>;
}

function VariantDetail({ accession, variantKey, branch, onBranchChange, onClose }: { accession: string; variantKey: string; branch: VariantEvidenceBranch; onBranchChange: (branch: VariantEvidenceBranch) => void; onClose: () => void }) {
  const [requestVersion, setRequestVersion] = useState(0);
  const [state, setState] = useState<{ kind: "loading" | "error" | "ready"; branch?: VariantEvidenceBranch; evidence?: VariantEvidenceResponse; error?: string }>({ kind: "loading" });
  const evidenceCache = useRef(new Map<string, VariantEvidenceResponse>());
  const panelId = `variant-evidence-${variantKey.replaceAll(/[^a-zA-Z0-9_-]/g, "-")}`;
  useEffect(() => {
    if (branch === "population") return;
    const cacheKey = `${variantKey}:${branch}`;
    const cached = evidenceCache.current.get(cacheKey);
    if (cached) {
      setState({ kind: "ready", branch, evidence: cached });
      return;
    }
    const controller = new AbortController();
    setState({ kind: "loading", branch });
    getJson<VariantEvidenceResponse>(`/variants/${encodeURIComponent(variantKey)}/evidence/${branch}?protein_accession=${encodeURIComponent(accession)}`, controller.signal)
      .then((evidence) => {
        evidenceCache.current.set(cacheKey, evidence);
        setState({ kind: "ready", branch, evidence });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", branch, error: error instanceof Error ? error.message : "Unable to load variant evidence." });
      });
    return () => controller.abort();
  }, [accession, variantKey, branch, requestVersion]);
  useEffect(() => () => evidenceCache.current.clear(), []);
  const branchStateIsCurrent = state.branch === branch;

  return <div id={panelId} className={`variant-detail branch-${branch}`}>
    <header className="variant-detail-heading"><div><p>Selected variant evidence</p><h3>{variantKey}</h3></div><button type="button" className="variant-detail-close" onClick={onClose}><X aria-hidden="true" size={17} />Close evidence</button></header>
    <div className="variant-branch-tabs" role="tablist" aria-label={`Evidence branches for ${variantKey}`}>{VARIANT_EVIDENCE_BRANCHES.map((item) => <button key={item.key} id={`${panelId}-tab-${item.key}`} type="button" role="tab" aria-selected={branch === item.key} aria-controls={`${panelId}-panel`} onClick={() => onBranchChange(item.key)}>{item.label}</button>)}</div>
    <div id={`${panelId}-panel`} role="tabpanel" aria-labelledby={`${panelId}-tab-${branch}`} className="variant-branch-content">
      {branch === "population" ? <PopulationFrequencyBranch accession={accession} variantKey={variantKey} /> : <>
        {(!branchStateIsCurrent || state.kind === "loading") && <p className="inline-loading" role="status">Loading the selected evidence branch…</p>}
        {branchStateIsCurrent && state.kind === "error" && <div className="variant-detail-error" role="alert"><p>{state.error}</p><button type="button" className="quiet-button" onClick={() => setRequestVersion((value) => value + 1)}>Retry</button></div>}
        {branchStateIsCurrent && state.kind === "ready" && state.evidence && <VariantBranch evidence={state.evidence} />}
      </>}
    </div>
  </div>;
}

function EvidenceAction({ item, branch, active, controls, onOpen, children }: { item: VariantItem; branch: VariantEvidenceBranch; active: boolean; controls: string; onOpen: (branch: VariantEvidenceBranch, trigger: HTMLButtonElement) => void; children: React.ReactNode }) {
  return <button type="button" className={`evidence-action source-${branch} ${active ? "is-active" : ""}`} aria-label={`Open ${branch} evidence for ${item.primary_effect.hgvsp ?? item.variant_key}`} aria-expanded={active} aria-controls={controls} onClick={(event) => onOpen(branch, event.currentTarget)}>{children}</button>;
}

function VariantRow({ item, accession, openEvidence, visibleColumns, onOpen, onClose, onBranchChange }: { item: VariantItem; accession: string; openEvidence: OpenEvidence; visibleColumns: VariantOptionalColumn[]; onOpen: (branch: VariantEvidenceBranch, trigger: HTMLButtonElement) => void; onClose: () => void; onBranchChange: (branch: VariantEvidenceBranch) => void }) {
  const effect = item.primary_effect;
  const open = openEvidence?.variantKey === item.variant_key;
  const panelId = `variant-evidence-${item.variant_key.replaceAll(/[^a-zA-Z0-9_-]/g, "-")}`;
  const sourceActions = item.source_badges.map((source) => ({ source, branch: normalizedSource(source) }));
  return <>
    <tr className={`variant-summary-row ${open ? "expanded" : ""}`}>
      <th scope="row" className="variant-field-identity"><button className="row-toggle" type="button" aria-expanded={open} aria-controls={panelId} aria-label={`${open ? "Close" : "Open"} all evidence for ${item.variant_key}`} onClick={(event) => open ? onClose() : onOpen("facts", event.currentTarget)}><PanelRightOpen aria-hidden="true" size={18} /><span><strong>{readable(effect.hgvsp)}</strong><small>{effect.effect_scope === "canonical" ? "Canonical protein effect" : "Isoform protein effect"}{effect.protein_start ? ` · position ${effect.protein_start}${effect.protein_end !== effect.protein_start ? `–${effect.protein_end}` : ""}` : " · unlocated"}</small><em>All evidence <ChevronRight aria-hidden="true" size={14} /></em></span></button></th>
      <td className="variant-field-protein"><strong>{formatTermLabel(effect.consequence)}</strong><code>{item.variant_key}</code><small>{item.genome_build} · {formatTermLabel(item.variant_class)}</small></td>
      {visibleColumns.includes("evidence") && <td className="variant-field-source"><div className="source-actions">{sourceActions.length ? sourceActions.map(({ source, branch }) => branch === "other" ? <SourceBadge key={source}>{formatSourceLabel(source)}</SourceBadge> : <EvidenceAction key={source} item={item} branch={branch} controls={panelId} active={open && openEvidence?.branch === branch} onOpen={onOpen}>{branch === "population" ? <Users aria-hidden="true" size={15} /> : <Database aria-hidden="true" size={15} />}{formatSourceLabel(source)}</EvidenceAction>) : <SourceBadge>Source not supplied</SourceBadge>}</div><small>Each source opens its own evidence branch.</small></td>}
      {visibleColumns.includes("predictions") && <td className="variant-field-prediction"><div className="variant-model-stack"><span><small>AlphaMissense · predicted</small><strong>{readable(item.am_class)}</strong>{item.am_pathogenicity !== null && <em>{readable(item.am_pathogenicity)}</em>}</span>{item.stability_prediction ? <EvidenceAction item={item} branch="stability" controls={panelId} active={open && openEvidence?.branch === "stability"} onOpen={onOpen}><Activity aria-hidden="true" size={16} /><span><small>Stability ΔΔG · predicted</small><StabilityValue prediction={item.stability_prediction} /></span></EvidenceAction> : <span><small>Stability ΔΔG · predicted</small><StabilityValue prediction={null} /></span>}</div></td>}
      {visibleColumns.includes("population") && <td className="variant-field-population"><dl className="variant-population-stack"><div><dt>gnomAD joint AF</dt><dd>{readable(item.joint_af)}</dd></div><div><dt>dbSNP</dt><dd>{readable(item.existing_variation)}</dd></div></dl></td>}
    </tr>
    {open && <tr className="detail-row"><td colSpan={variantTableColumnCount(visibleColumns)}><VariantDetail accession={accession} variantKey={item.variant_key} branch={openEvidence.branch} onBranchChange={onBranchChange} onClose={onClose} /></td></tr>}
  </>;
}

function ColumnChooser({ preset, visibleColumns, onPreset, onToggle }: { preset: VariantViewPreset; visibleColumns: VariantOptionalColumn[]; onPreset: (preset: Exclude<VariantViewPreset, "custom">) => void; onToggle: (column: VariantOptionalColumn) => void }) {
  return <details className="variant-column-chooser"><summary><Columns3 aria-hidden="true" size={17} />Display <span>{variantTableColumnCount(visibleColumns)} columns</span></summary><div className="variant-column-menu"><strong>Choose an information view</strong><div className="variant-view-presets" role="group" aria-label="Variant column presets">{(["balanced", "clinical", "protein"] as const).map((name) => <button key={name} type="button" aria-pressed={preset === name} onClick={() => onPreset(name)}>{name === "balanced" ? "Balanced" : name === "clinical" ? "Clinical review" : "Protein science"}</button>)}</div><fieldset><legend>Optional columns</legend>{VARIANT_OPTIONAL_COLUMNS.map((column) => <label key={column.key}><input type="checkbox" checked={visibleColumns.includes(column.key)} onChange={() => onToggle(column.key)} /><span><strong>{column.label}</strong><small>{column.description}</small></span></label>)}</fieldset><p>Protein variant, effect identity, and the All evidence action always remain available.</p></div></details>;
}

function summaryItemLabel(item: VariantSummaryCount, kind: "protein_form" | "consequence" | "clinvar") {
  if (kind === "protein_form") {
    return item.category === "canonical"
      ? `Canonical protein form${item.isoform_id ? ` · ${item.isoform_id}` : ""}`
      : `Isoform${item.isoform_id ? ` · ${item.isoform_id}` : ""}`;
  }
  return formatTermLabel(item.category);
}

function VariantSummaryFacetPanel({ title, facet, kind, countLabel }: {
  title: string;
  facet: VariantSummaryFacet;
  kind: "protein_form" | "consequence" | "clinvar";
  countLabel?: string;
}) {
  return <section className="variant-summary-facet" aria-label={title}>
    <header><h3>{title}</h3>{countLabel && <span>{countLabel}</span>}</header>
    <p>Distinct variant keys; category counts can overlap and are not additive.</p>
    <ul>{facet.items.map((item) => <li key={`${item.category}-${item.isoform_id ?? "none"}`}><span>{summaryItemLabel(item, kind)}</span><strong>{item.variant_count.toLocaleString()}</strong></li>)}</ul>
  </section>;
}

function VariantSummaryPanel({ accession }: { accession: string }) {
  const [state, setState] = useState<{ kind: "loading" | "error" | "ready"; response?: VariantCatalogSummaryResponse }>({ kind: "loading" });
  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    getJson<VariantCatalogSummaryResponse>(`/proteins/${encodeURIComponent(accession)}/variants/summary`, controller.signal)
      .then((response) => setState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [accession]);

  if (state.kind === "loading") return <p className="variant-summary-status" role="status">Loading distinct variant summary…</p>;
  if (state.kind === "error") return <p className="variant-summary-status" role="status">Variant summary unavailable. The browser table remains available.</p>;
  const summary = state.response!;
  return <section className="variant-summary-panel" aria-labelledby="variant-summary-heading">
    <header className="variant-summary-heading"><div><p>Summary first</p><h2 id="variant-summary-heading">Protein-scoped variant catalog</h2></div><strong>{summary.total.value.toLocaleString()}<small>distinct variants</small></strong></header>
    <p className="variant-summary-grain">The total counts <strong>distinct variant keys</strong> once. Protein-form, consequence, and ClinVar facets also count distinct variant keys, but their categories may overlap; do not add category counts together.</p>
    <div className="variant-summary-facets">
      <VariantSummaryFacetPanel title="Protein forms and isoforms" facet={summary.protein_forms} kind="protein_form" countLabel={`${summary.protein_forms.items.length} forms`} />
      <VariantSummaryFacetPanel title="Consequence terms" facet={summary.consequences} kind="consequence" countLabel={`${summary.consequences.items.length} terms`} />
      <VariantSummaryFacetPanel title="ClinVar pathogenicity categories" facet={summary.clinvar_pathogenicity} kind="clinvar" />
    </div>
    <p className="variant-summary-clinvar-note">ClinVar categories retain the classifications present in source assertions. They may overlap for a variant and do not represent a vote, rank, or consensus.</p>
  </section>;
}

export function VariantTable({ accession, selection = null, compact = false }: { accession: string; selection?: SiteSelection; compact?: boolean }) {
  const [filters, setFilters] = useState<Filters>({ scope: "canonical", consequence: "", source: "", start: "", end: "" });
  const [applied, setApplied] = useState(filters);
  const [cursor, setCursor] = useState<string | null>(null);
  const [cursorHistory, setCursorHistory] = useState<(string | null)[]>([]);
  const [state, setState] = useState<{ kind: "loading" | "error" | "ready"; response?: VariantListResponse; error?: string }>({ kind: "loading" });
  const [optionState, setOptionState] = useState<{ kind: "loading" | "error" | "ready"; response?: VariantFilterOptionsResponse; error?: string }>({ kind: "loading" });
  const [openEvidence, setOpenEvidence] = useState<OpenEvidence>(null);
  const [preset, setPreset] = useState<VariantViewPreset>("balanced");
  const [visibleColumns, setVisibleColumns] = useState<VariantOptionalColumn[]>(columnsForPreset("balanced"));
  const returnFocusRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!openEvidence) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpenEvidence(null);
      window.requestAnimationFrame(() => returnFocusRef.current?.focus());
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [openEvidence]);

  useEffect(() => {
    const controller = new AbortController();
    setOptionState({ kind: "loading" });
    getJson<VariantFilterOptionsResponse>(`/proteins/${encodeURIComponent(accession)}/variants/options?scope=${encodeURIComponent(filters.scope)}`, controller.signal)
      .then((response) => setOptionState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setOptionState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load variant filter options." });
      });
    return () => controller.abort();
  }, [accession, filters.scope]);

  useEffect(() => {
    if (!selection) return;
    const next = { ...filters, start: String(selection.start), end: String(selection.end) };
    setFilters(next); setApplied(next); setCursor(null); setCursorHistory([]);
    // filters is intentionally omitted: a sequence selection replaces only the site fields.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selection?.start, selection?.end]);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ scope: applied.scope, limit: compact ? "12" : "50" });
    if (applied.consequence.trim()) params.set("consequence", applied.consequence.trim());
    if (applied.source.trim()) params.set("source", applied.source.trim());
    if (applied.start && applied.end) { params.set("start", applied.start); params.set("end", applied.end); }
    if (cursor) params.set("cursor", cursor);
    setState({ kind: "loading" }); setOpenEvidence(null);
    getJson<VariantListResponse>(`/proteins/${encodeURIComponent(accession)}/variants?${params}`, controller.signal)
      .then((response) => setState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load variants." });
      });
    return () => controller.abort();
  }, [accession, applied, cursor, compact]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if ((filters.start && !filters.end) || (!filters.start && filters.end)) return;
    setApplied(filters); setCursor(null); setCursorHistory([]);
  }

  function clearFilters() {
    const next: Filters = { scope: "canonical", consequence: "", source: "", start: "", end: "" };
    setFilters(next); setApplied(next); setCursor(null); setCursorHistory([]);
  }

  function openBranch(variantKey: string, branch: VariantEvidenceBranch, trigger: HTMLButtonElement) {
    returnFocusRef.current = trigger;
    setOpenEvidence({ variantKey, branch });
  }

  function closeEvidence() {
    setOpenEvidence(null);
    window.requestAnimationFrame(() => returnFocusRef.current?.focus());
  }

  function applyPreset(next: Exclude<VariantViewPreset, "custom">) {
    setPreset(next);
    setVisibleColumns(columnsForPreset(next));
  }

  const response = state.response;
  const pageNumber = cursorHistory.length + 1;
  return <div className={`variant-browser ${compact ? "compact-variants" : ""}`}>
    <div className="variant-browser-toolbar"><div><strong>Filter and focus</strong><span>Start with a bounded summary, then open one evidence branch at a time.</span></div><ColumnChooser preset={preset} visibleColumns={visibleColumns} onPreset={applyPreset} onToggle={(column) => { setVisibleColumns((columns) => toggleVariantColumn(columns, column)); setPreset("custom"); }} /></div>
    <VariantSummaryPanel accession={accession} />
    <form className="variant-filters" onSubmit={submit}>
      <label>Protein effects<select value={filters.scope} onChange={(event) => setFilters({ ...filters, scope: event.target.value as Filters["scope"], consequence: "", source: "" })}><option value="canonical">Canonical</option><option value="isoform">Isoform-only</option><option value="all">All protein effects</option></select></label>
      <label>Consequence<select value={filters.consequence} disabled={optionState.kind !== "ready"} onChange={(event) => setFilters({ ...filters, consequence: event.target.value })}><option value="">{optionState.kind === "loading" ? "Loading options…" : "All consequences"}</option>{optionState.response?.consequences.map((option) => <option key={option.value} value={option.value}>{formatTermLabel(option.value)} ({option.variant_count.toLocaleString()})</option>)}</select></label>
      <label>Source<select value={filters.source} disabled={optionState.kind !== "ready"} onChange={(event) => setFilters({ ...filters, source: event.target.value })}><option value="">{optionState.kind === "loading" ? "Loading options…" : "All sources"}</option>{optionState.response?.sources.map((option) => <option key={option.value} value={option.value}>{formatSourceLabel(option.value)} ({option.variant_count.toLocaleString()})</option>)}</select></label>
      <label>Site start<input type="number" min={1} value={filters.start} onChange={(event) => setFilters({ ...filters, start: event.target.value })} /></label>
      <label>Site end<input type="number" min={1} value={filters.end} onChange={(event) => setFilters({ ...filters, end: event.target.value })} /></label>
      <div className="filter-actions"><button type="submit" className="primary-button">Apply filters</button><button type="button" className="quiet-button" onClick={clearFilters}>Reset</button></div>
    </form>
    {optionState.kind === "error" && <p className="inline-error" role="alert">{optionState.error}</p>}
    <div className="active-filter-bar"><span>Active: {formatTermLabel(applied.scope)}{applied.consequence ? ` · ${formatTermLabel(applied.consequence)}` : ""}{applied.source ? ` · source ${formatSourceLabel(applied.source)}` : ""}{applied.start && applied.end ? ` · site ${applied.start}–${applied.end}` : ""}</span>{response && <strong>Showing {response.items.length.toLocaleString()} of {response.total_or_estimate.value.toLocaleString()} variants</strong>}</div>
    {state.kind === "loading" && <StatusMessage title="Loading variants">Retrieving this bounded server-side page.</StatusMessage>}
    {state.kind === "error" && <StatusMessage title="Variants unavailable" tone="error">{state.error}</StatusMessage>}
    {state.kind === "ready" && response && response.items.length === 0 && <StatusMessage title="No variants match">No protein-scoped variants match the active effect, source, consequence, and site filters.</StatusMessage>}
    {state.kind === "ready" && response && response.items.length > 0 && <>
      <div className="table-scroll"><table className="variant-table"><caption>Protein-scoped variants for {accession}, page {pageNumber}. Source evidence and model outputs remain independent; each action opens one focused branch.</caption><thead><tr><th scope="col" className="variant-field-identity">Protein variant & action</th><th scope="col" className="variant-field-protein">Effect and genomic identity</th>{visibleColumns.includes("evidence") && <th scope="col" className="variant-field-source">Source evidence</th>}{visibleColumns.includes("predictions") && <th scope="col" className="variant-field-prediction">Model context</th>}{visibleColumns.includes("population") && <th scope="col" className="variant-field-population">Population and identifiers</th>}</tr></thead><tbody>{response.items.map((item) => <VariantRow key={item.variant_key} item={item} accession={accession} openEvidence={openEvidence?.variantKey === item.variant_key ? openEvidence : null} visibleColumns={visibleColumns} onOpen={(branch, trigger) => openBranch(item.variant_key, branch, trigger)} onClose={closeEvidence} onBranchChange={(branch) => setOpenEvidence({ variantKey: item.variant_key, branch })} />)}</tbody></table></div>
      <nav className="pagination" aria-label="Variant pages"><button type="button" className="quiet-button" disabled={cursorHistory.length === 0} onClick={() => { const history = [...cursorHistory]; const previous = history.pop() ?? null; setCursorHistory(history); setCursor(previous); }}>Previous</button><span>Page {pageNumber}</span><button type="button" className="quiet-button" disabled={!response.next_cursor} onClick={() => { setCursorHistory((history) => [...history, cursor]); setCursor(response.next_cursor); }}>Next</button></nav>
    </>}
    {compact && <p className="full-page-link"><Link href={`/protein/${encodeURIComponent(accession)}/variants`}>View all variants in the full browser <ChevronRight aria-hidden="true" size={15} /></Link></p>}
  </div>;
}
