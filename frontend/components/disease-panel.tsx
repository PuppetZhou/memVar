"use client";

import { useEffect, useState } from "react";
import { DiseaseItem, DiseaseResponse, HpoEvidenceItem, HpoResponse } from "../lib/api";
import { getJson } from "../lib/api-client";
import { formatFieldLabel, formatSourceRelease, formatTermLabel } from "../lib/display-labels";
import { sharedSourceRecordValue, sourceRecordMetadataIsUniform } from "../lib/source-context";
import { ActionLink } from "./ui/action-link";
import { Button } from "./ui/button";
import { SourceBadge } from "./ui/source-badge";
import { SourceContext } from "./ui/source-context";

const SOURCE_META = {
  clingen_validity: { title: "ClinGen gene–disease validity", note: "Expert-panel validity assertions; classifications are interpreted only within ClinGen validity." },
  clingen_dosage: { title: "ClinGen dosage sensitivity", note: "Haploinsufficiency and triplosensitivity curation is distinct from variant pathogenicity." },
  gencc: { title: "GenCC assertions", note: "Each submitter assertion remains an independent record." },
  omim: { title: "OMIM gene–disease", note: "Mapping key and relationship status retain OMIM-specific meaning." },
  hpo: { title: "HPO disease navigation", note: "Observed, explicitly absent, and inheritance annotations are requested separately for a disease." },
} as const;

type SourceName = keyof typeof SOURCE_META;
type HpoCategory = "observed" | "explicitly_absent" | "inheritance";

function sourceDisplayName(source: SourceName) {
  if (source === "hpo") return "HPO";
  if (source.startsWith("clingen")) return "ClinGen";
  return source === "gencc" ? "GenCC" : "OMIM";
}

const SOURCE_FIELDS: Record<SourceName, string[]> = {
  clingen_validity: ["classification", "moi", "expert_panel", "classification_date", "sop_version", "report_url", "hgnc_id", "gene_symbol", "source_release", "evidence_grain"],
  clingen_dosage: ["haploinsufficiency", "triplosensitivity", "curation_date", "report_url", "hgnc_id", "gene_symbol", "source_release", "evidence_grain"],
  gencc: ["classification", "moi", "submitter", "assertion_date", "assertion_id", "source_disease_id", "pmids", "public_report_url", "criteria_url", "source_submission_id", "source_release", "evidence_grain"],
  omim: ["inheritance", "mapping_key", "relationship_status", "cyto_location", "locus_mim_number", "gene_id", "ensembl_gene_id", "disease_id_source", "source_release", "evidence_grain"],
  hpo: ["unique_source_hpo_count", "hpo_annotation_evidence_count", "explicitly_absent_annotation_count", "gene_id", "gene_symbol", "source_release", "evidence_grain"],
};

const PREVIEW_FIELDS: Record<SourceName, string[]> = {
  clingen_validity: ["classification", "moi"], clingen_dosage: ["haploinsufficiency", "triplosensitivity"],
  gencc: ["classification", "moi", "submitter"], omim: ["inheritance", "mapping_key", "relationship_status"],
  hpo: ["unique_source_hpo_count", "explicitly_absent_annotation_count"],
};

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not available";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumSignificantDigits: 7 });
  if (Array.isArray(value)) return value.map(valueText).join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function isConflict(item: DiseaseItem) {
  const classification = String(item.assertion.classification ?? "").toLocaleLowerCase();
  return classification.includes("disputed") || classification.includes("refuted");
}

function databaseUrl(identifier: string | null) {
  if (!identifier) return null;
  if (identifier.startsWith("MONDO:")) return `https://monarchinitiative.org/disease/${encodeURIComponent(identifier)}`;
  if (identifier.startsWith("OMIM:")) return `https://omim.org/entry/${encodeURIComponent(identifier.slice(5))}`;
  if (identifier.startsWith("HP:")) return `https://hpo.jax.org/browse/term/${encodeURIComponent(identifier)}`;
  return null;
}

function FieldValue({ field, value }: { field: string; value: unknown }) {
  const text = valueText(value);
  if (field.endsWith("_url") && typeof value === "string") return <ActionLink href={value} external>Open source report</ActionLink>;
  if (field === "hgnc_id" && typeof value === "string") return <ActionLink href={`https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/${encodeURIComponent(value)}`} external>{text}</ActionLink>;
  if (field === "gene_id" && typeof value === "string") return <ActionLink href={`https://www.ncbi.nlm.nih.gov/gene/${encodeURIComponent(value)}`} external>{text}</ActionLink>;
  if (field === "ensembl_gene_id" && typeof value === "string") return <ActionLink href={`https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=${encodeURIComponent(value)}`} external>{text}</ActionLink>;
  if (field === "source_release" && typeof value === "string") return <>{formatSourceRelease(value)}</>;
  return <>{["classification", "relationship_status", "moi", "evidence_grain"].includes(field) ? formatTermLabel(text) : text}</>;
}

function HpoEvidence({ accession, diseaseId }: { accession: string; diseaseId: string }) {
  const [category, setCategory] = useState<HpoCategory>("observed");
  const [cursor, setCursor] = useState<string | null>(null);
  const [history, setHistory] = useState<(string | null)[]>([]);
  const [state, setState] = useState<{ kind: "loading" | "error" | "ready"; response?: HpoResponse; error?: string }>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ category, disease_id: diseaseId, limit: "25" });
    if (cursor) params.set("cursor", cursor);
    setState({ kind: "loading" });
    getJson<HpoResponse>(`/proteins/${encodeURIComponent(accession)}/diseases/hpo?${params}`, controller.signal)
      .then((response) => setState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load HPO evidence." });
      });
    return () => controller.abort();
  }, [accession, category, cursor, diseaseId]);

  function changeCategory(next: HpoCategory) { setCategory(next); setCursor(null); setHistory([]); }
  const response = state.response;
  const start = history.length * 25 + 1;
  const end = response ? Math.min(start + response.items.length - 1, response.total_or_estimate.value) : 0;

  function evidenceDetails(item: HpoEvidenceItem) {
    const fields = ["evidence_code", "reference", "onset", "frequency", "sex", "modifier", "biocuration"];
    return fields.filter((field) => item.evidence[field] !== null && item.evidence[field] !== undefined && item.evidence[field] !== "");
  }

  return <div className="hpo-evidence">
    <div className="hpo-tabs" role="group" aria-label="HPO evidence category">
      {(["observed", "explicitly_absent", "inheritance"] as HpoCategory[]).map((item) => <Button variant="quiet" key={item} type="button" aria-pressed={category === item} onClick={() => changeCategory(item)}>{formatTermLabel(item)}</Button>)}
    </div>
    {category === "explicitly_absent" && <p className="hpo-absence-note"><strong>Explicitly absent (NOT).</strong> These terms are not observed phenotypes.</p>}
    {state.kind === "loading" && <p className="inline-loading" role="status">Loading HPO evidence…</p>}
    {state.kind === "error" && <p className="inline-error" role="alert">{state.error}</p>}
    {response && <>
      {response.items.length === 0 ? <p className="empty-value">No {formatTermLabel(category).toLocaleLowerCase()} HPO evidence is available for this disease record.</p> : <ul className="hpo-list">{response.items.map((item, index) => <li key={`${item.hpo_id ?? item.hpo_name ?? "hpo"}-${index}`}><strong>{item.hpo_name ?? item.hpo_id ?? "HPO term unavailable"}</strong>{item.hpo_id && (databaseUrl(item.hpo_id) ? <ActionLink href={databaseUrl(item.hpo_id)!} external>{item.hpo_id}</ActionLink> : <small>{item.hpo_id}</small>)}<dl>{evidenceDetails(item).map((field) => <div key={field}><dt>{formatFieldLabel(field)}</dt><dd>{valueText(item.evidence[field])}</dd></div>)}</dl></li>)}</ul>}
      <div className="pagination"><Button variant="quiet" type="button" disabled={history.length === 0} onClick={() => { const previous = history[history.length - 1] ?? null; setHistory(history.slice(0, -1)); setCursor(previous); }}>Previous</Button><span>Showing {response.items.length ? `${start}–${end}` : "0"} of {response.total_or_estimate.value.toLocaleString()}</span><Button variant="quiet" type="button" disabled={!response.next_cursor} onClick={() => { setHistory([...history, cursor]); setCursor(response.next_cursor); }}>Next</Button></div>
    </>}
  </div>;
}

function MondoNavigation({ mappings }: { mappings: Record<string, unknown>[] }) {
  if (!mappings.length) return null;
  return <div className="mondo-navigation"><strong>Exact MONDO mappings</strong>{mappings.map((mapping, index) => {
    const id = typeof mapping.mondo_id === "string" ? mapping.mondo_id : null;
    const categories = Array.isArray(mapping.categories) ? mapping.categories as Record<string, unknown>[] : [];
    return <div key={`${id}-${index}`}><span>{id && databaseUrl(id) ? <ActionLink href={databaseUrl(id)!} external>{id}</ActionLink> : valueText(id)}</span><span>{valueText(mapping.mondo_name)}</span>{categories.length > 0 && <small>Categories: {categories.map((category) => valueText(category.category_name)).join(", ")}</small>}</div>;
  })}</div>;
}

function DiseaseRow({ item, accession, source, recordKey, hpoOpen, onHpoToggle }: { item: DiseaseItem; accession: string; source: SourceName; recordKey: string; hpoOpen: boolean; onHpoToggle: () => void }) {
  const idUrl = databaseUrl(item.disease_id);
  const fields = SOURCE_FIELDS[source].filter((key) => item.assertion[key] !== null && item.assertion[key] !== undefined && item.assertion[key] !== "");
  const conflict = isConflict(item);
  return <article className={`disease-row ${conflict ? "conflict" : ""}`} id={`disease-${recordKey.replaceAll(/[^a-zA-Z0-9-]/g, "-")}`}>
    <div className="disease-row-title"><h4>{item.disease_name ?? "Disease name unavailable"}</h4>{conflict && <SourceBadge tone="conflict"><span aria-hidden="true">⚠</span> Conflict: {valueText(item.assertion.classification)}</SourceBadge>}{item.disease_id && (idUrl ? <ActionLink href={idUrl} external>{item.disease_id}</ActionLink> : <span>{item.disease_id}</span>)}</div>
    <dl className="detail-fields">{fields.map((key) => <div key={key}><dt>{formatFieldLabel(key)}</dt><dd><FieldValue field={key} value={item.assertion[key]} /></dd></div>)}</dl>
    <MondoNavigation mappings={item.exact_mondo_mappings} />
    {item.disease_id && <div className="hpo-disclosure"><Button variant="quiet" type="button" aria-expanded={hpoOpen} aria-controls={`hpo-${recordKey}`} onClick={onHpoToggle}>{hpoOpen ? "Hide" : "View"} HPO phenotype evidence</Button>{hpoOpen && <div id={`hpo-${recordKey}`} className="disclosure-panel" data-open="true"><HpoEvidence accession={accession} diseaseId={item.disease_id} /></div>}</div>}
  </article>;
}

function DiseasePreview({ item, source }: { item: DiseaseItem; source: SourceName }) {
  const fields = PREVIEW_FIELDS[source].filter((field) => item.assertion[field] !== null && item.assertion[field] !== undefined && item.assertion[field] !== "");
  return <li className={isConflict(item) ? "conflict" : ""}><strong>{item.disease_name ?? "Gene-level source record"}</strong>{item.disease_id && <small>{item.disease_id}</small>}<span>{fields.length ? fields.map((field, index) => <span key={field}>{index > 0 && " · "}{formatFieldLabel(field)}: <FieldValue field={field} value={item.assertion[field]} /></span>) : "Source-specific details available"}</span></li>;
}

function DiseaseSourceCard({ accession, source, expanded, onToggle, activeRecord, onRecordToggle }: { accession: string; source: SourceName; expanded: boolean; onToggle: () => void; activeRecord: string; onRecordToggle: (key: string) => void }) {
  const [items, setItems] = useState<DiseaseItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");
  const meta = SOURCE_META[source];
  const sourceRelease = sharedSourceRecordValue(items.map((item) => item.assertion), "source_release");
  const evidenceGrain = sharedSourceRecordValue(items.map((item) => item.assertion), "evidence_grain");
  const hasSharedSourceContext = sourceRecordMetadataIsUniform(items.map((item) => item.assertion), "source_release") && sourceRecordMetadataIsUniform(items.map((item) => item.assertion), "evidence_grain");

  useEffect(() => {
    const controller = new AbortController();
    setState("loading");
    getJson<DiseaseResponse>(`/proteins/${encodeURIComponent(accession)}/diseases?source=${source}&limit=3`, controller.signal)
      .then((response) => {
        const section = response.sections[source];
        setItems(section?.items ?? []); setNextCursor(section?.next_cursor ?? null); setTotal(section?.total_or_estimate.value ?? 0); setState("ready");
      }).catch((reason: unknown) => { if (reason instanceof DOMException && reason.name === "AbortError") return; setError(reason instanceof Error ? reason.message : "Unable to load this source."); setState("error"); });
    return () => controller.abort();
  }, [accession, source]);

  function loadMore() {
    if (!nextCursor || state === "loading") return;
    setState("loading"); setError("");
    getJson<DiseaseResponse>(`/proteins/${encodeURIComponent(accession)}/diseases?source=${source}&limit=50&cursor=${encodeURIComponent(nextCursor)}`)
      .then((response) => { const section = response.sections[source]; if (!section) throw new Error(`No ${meta.title} section was returned.`); setItems((current) => [...current, ...section.items]); setNextCursor(section.next_cursor); setTotal(section.total_or_estimate.value); setState("ready"); })
      .catch((reason: unknown) => { setError(reason instanceof Error ? reason.message : "Unable to load more records."); setState("error"); });
  }

  useEffect(() => {
    const requestedIndex = Number(activeRecord.split("|").at(-1));
    if (expanded && activeRecord.startsWith(`${source}|`) && Number.isInteger(requestedIndex) && requestedIndex >= items.length && nextCursor && state === "ready") loadMore();
    // loadMore is intentionally driven by the cursor and loaded item count for URL restoration.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeRecord, expanded, items.length, nextCursor, source, state]);

  return <article className="disease-source-card" id={`disease-source-${source}`}>
    <header><div><SourceBadge>{sourceDisplayName(source)}</SourceBadge><h3>{meta.title}</h3></div></header>
    {state === "loading" && items.length === 0 && <p className="inline-loading" role="status">Loading this source…</p>}
    {state === "error" && items.length === 0 && <p className="inline-error" role="alert">{error}</p>}
    {items.length === 0 && state === "ready" ? <p className="empty-value">No records are available in this source.</p> : items.length > 0 && <>
      {hasSharedSourceContext && <SourceContext source={sourceDisplayName(source)} release={sourceRelease} recordGrain={evidenceGrain} caveat={meta.note} className="disease-source-context" />}
      <p className="record-summary"><strong>{total.toLocaleString()}</strong> source records <span>{new Set(items.map((item) => item.disease_id).filter(Boolean)).size} diseases in preview</span></p>
      <ul className="disease-preview">{items.slice(0, 3).map((item, index) => <DiseasePreview key={`${item.disease_id}-${index}`} item={item} source={source} />)}</ul>
      <Button variant="secondary" className="source-expand-button" type="button" aria-expanded={expanded} aria-controls={`disease-details-${source}`} onClick={onToggle}>{expanded ? "Collapse source" : `Expand source (${total.toLocaleString()})`}</Button>
      {expanded && <div id={`disease-details-${source}`} className="disease-source-detail disclosure-panel" data-open="true"><div className="disease-rows">{items.map((item, index) => { const key = `${source}|${item.disease_id ?? "none"}|${index}`; return <DiseaseRow accession={accession} item={item} source={source} recordKey={key} hpoOpen={activeRecord === key} onHpoToggle={() => onRecordToggle(activeRecord === key ? "" : key)} key={key} />; })}</div>{error && <p className="inline-error" role="alert">{error}</p>}{nextCursor && <p className="load-more"><Button variant="quiet" type="button" disabled={state === "loading"} onClick={loadMore}>{state === "loading" ? "Loading…" : `Load more · showing ${items.length} of ${total}`}</Button></p>}</div>}
    </>}
  </article>;
}

function initialUrlState() {
  if (typeof window === "undefined") return { sources: new Set<SourceName>(), record: "" };
  const params = new URLSearchParams(window.location.search);
  const sources = new Set((params.get("disease_sources") ?? "").split(",").filter((item): item is SourceName => item in SOURCE_META));
  return { sources, record: params.get("disease_record") ?? "" };
}

export function DiseasePanel({ accession }: { accession: string }) {
  const [expanded, setExpanded] = useState<Set<SourceName>>(new Set());
  const [activeRecord, setActiveRecord] = useState("");

  useEffect(() => {
    const initial = initialUrlState();
    setExpanded(initial.sources);
    setActiveRecord(initial.record);
  }, []);

  function updateUrl(sources: Set<SourceName>, record: string) {
    const url = new URL(window.location.href);
    if (sources.size) url.searchParams.set("disease_sources", [...sources].join(",")); else url.searchParams.delete("disease_sources");
    if (record) url.searchParams.set("disease_record", record); else url.searchParams.delete("disease_record");
    url.hash = sources.size ? `disease-source-${[...sources][sources.size - 1]}` : "diseases";
    window.history.replaceState(null, "", url);
  }

  function toggleSource(source: SourceName) {
    const next = new Set(expanded);
    if (next.has(source)) next.delete(source); else next.add(source);
    setExpanded(next); updateUrl(next, activeRecord);
  }

  function toggleRecord(record: string) { setActiveRecord(record); updateUrl(expanded, record); }

  return <section id="diseases" className="overview-section" aria-labelledby="disease-heading">
    <div className="section-heading"><p className="eyebrow">M4 disease evidence</p><h2 id="disease-heading">Disease source overview</h2></div>
    <p className="section-intro">Each source retains its own assertion grain and classification semantics. MemVar does not vote across sources or calculate a consensus disease score.</p>
    <div className="disease-source-grid">{(Object.keys(SOURCE_META) as SourceName[]).map((source) => <DiseaseSourceCard accession={accession} source={source} expanded={expanded.has(source)} onToggle={() => toggleSource(source)} activeRecord={activeRecord} onRecordToggle={toggleRecord} key={source} />)}</div>
  </section>;
}
