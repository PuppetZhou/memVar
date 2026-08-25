"use client";

import { type FormEvent, useEffect, useState } from "react";
import { ChevronDown, ChevronRight, ListFilter } from "lucide-react";

import { GoAspect, GoEvidenceResponse, GoTermSummary, GoTermsResponse } from "../lib/api";
import { getJson } from "../lib/api-client";
import { applyGoTextFilters, formatGoDate, goAspectLabel, goTermEvidencePath, pubmedUrl, quickGoTermUrl, toggledGoAspect } from "../lib/go-evidence";
import { ActionLink } from "./ui/action-link";
import { SourceContext } from "./ui/source-context";

type LoadState<T> = { kind: "loading" | "error" | "ready"; data?: T; error?: string };

const PAGE_SIZE = 20;
const ASPECTS: GoAspect[] = ["MF", "BP", "CC"];
const ASPECT_DESCRIPTIONS: Record<GoAspect, string> = {
  MF: "Activities performed by the gene product.",
  BP: "Biological programs and pathways involving the gene product.",
  CC: "Cellular locations where the gene product acts.",
};

function termsPath(accession: string, options: { aspect: GoAspect | null; query: string; evidenceCode: string; includeNegated: boolean; cursor?: string | null }) {
  const params = new URLSearchParams({ limit: String(options.aspect ? PAGE_SIZE : 1) });
  if (options.aspect) params.set("aspect", options.aspect);
  if (options.query.trim()) params.set("q", options.query.trim());
  if (options.evidenceCode.trim()) params.set("evidence_code", options.evidenceCode.trim());
  if (options.includeNegated) params.set("include_negated", "true");
  if (options.cursor) params.set("cursor", options.cursor);
  return `/proteins/${encodeURIComponent(accession)}/go/terms?${params}`;
}

function TermEvidence({ accession, term, evidenceCode, includeNegated }: { accession: string; term: GoTermSummary; evidenceCode: string; includeNegated: boolean }) {
  const [open, setOpen] = useState(false);
  const [retry, setRetry] = useState(0);
  const [state, setState] = useState<LoadState<GoEvidenceResponse>>({ kind: "loading" });
  const [items, setItems] = useState<GoEvidenceResponse["items"]>([]);
  const [cursor, setCursor] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setState((current) => ({ kind: "loading", data: current.data }));
    setItems([]);
    getJson<GoEvidenceResponse>(goTermEvidencePath(accession, term.go_id, { evidenceCode, includeNegated, limit: PAGE_SIZE }), controller.signal)
      .then((data) => { setItems(data.items); setCursor(data.next_cursor); setState({ kind: "ready", data }); })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load GO evidence." });
      });
    return () => controller.abort();
  }, [accession, evidenceCode, includeNegated, open, retry, term.go_id]);

  function loadMore() {
    if (!cursor) return;
    getJson<GoEvidenceResponse>(goTermEvidencePath(accession, term.go_id, { evidenceCode, includeNegated, cursor, limit: PAGE_SIZE }))
      .then((data) => { setItems((current) => [...current, ...data.items]); setCursor(data.next_cursor); setState({ kind: "ready", data }); })
      .catch((error: unknown) => setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load more GO evidence." }));
  }

  return <details className="go-term-evidence" onToggle={(event) => setOpen(event.currentTarget.open)}>
    <summary><ChevronRight className="go-disclosure-icon" aria-hidden="true" size={17} />View {term.annotation_count.toLocaleString()} annotation record{term.annotation_count === 1 ? "" : "s"}</summary>
    {open && <div className="go-evidence-detail">
      {state.kind === "loading" && <p role="status">Loading annotation records…</p>}
      {state.kind === "error" && <p className="go-evidence-error" role="alert">{state.error} <button type="button" onClick={() => setRetry((value) => value + 1)}>Retry</button></p>}
      {state.kind === "ready" && <>
        {items.length ? <ol className="go-evidence-records">{items.map((item) => { const pmid = pubmedUrl(item.reference_id); return <li key={item.go_evidence_id}><dl><div><dt>Qualifier</dt><dd>{item.qualifier ?? "Not recorded"}{item.is_negated && " · NOT / negated"}</dd></div><div><dt>Evidence code</dt><dd>{item.evidence_code ?? "Not recorded"}</dd></div><div><dt>Reference</dt><dd>{pmid ? <ActionLink href={pmid} external>{item.reference_id}</ActionLink> : item.reference_id ?? "Not recorded"}</dd></div><div><dt>Assigned by</dt><dd>{item.assigned_by ?? "Not recorded"}</dd></div><div><dt>Date</dt><dd>{formatGoDate(item.annotation_date)}</dd></div>{item.with_from && <div><dt>With / from</dt><dd>{item.with_from}</dd></div>}{item.annotation_extension && <div><dt>Extension</dt><dd>{item.annotation_extension}</dd></div>}</dl></li>; })}</ol> : <p className="empty-value">No annotation records match this disclosure.</p>}
        {cursor && <button type="button" className="quiet-button go-load-more" onClick={loadMore}>Load more evidence</button>}
      </>}
    </div>}
  </details>;
}

export function GoEvidence({ accession }: { accession: string }) {
  const [aspect, setAspect] = useState<GoAspect | null>(null);
  const [draftQuery, setDraftQuery] = useState("");
  const [draftEvidenceCode, setDraftEvidenceCode] = useState("");
  const [query, setQuery] = useState("");
  const [evidenceCode, setEvidenceCode] = useState("");
  const [includeNegated, setIncludeNegated] = useState(false);
  const [retry, setRetry] = useState(0);
  const [state, setState] = useState<LoadState<GoTermsResponse>>({ kind: "loading" });
  const [items, setItems] = useState<GoTermSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const filters = { aspect, query, evidenceCode, includeNegated };

  useEffect(() => {
    const controller = new AbortController();
    setState((current) => ({ kind: "loading", data: current.data }));
    setItems([]);
    setCursor(null);
    getJson<GoTermsResponse>(termsPath(accession, filters), controller.signal)
      .then((data) => { setItems(aspect ? data.items : []); setCursor(aspect ? data.next_cursor : null); setState({ kind: "ready", data }); })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load Gene Ontology terms." });
      });
    return () => controller.abort();
  }, [accession, aspect, query, evidenceCode, includeNegated, retry]);

  function loadMore() {
    if (!cursor) return;
    getJson<GoTermsResponse>(termsPath(accession, { ...filters, cursor }))
      .then((data) => { setItems((current) => [...current, ...data.items]); setCursor(data.next_cursor); setState({ kind: "ready", data }); })
      .catch((error: unknown) => setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load more GO terms." }));
  }

  function applyTextFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = applyGoTextFilters(draftQuery, draftEvidenceCode);
    setQuery(next.query);
    setEvidenceCode(next.evidenceCode);
  }

  function clearFilters() {
    setDraftQuery("");
    setDraftEvidenceCode("");
    setQuery("");
    setEvidenceCode("");
    setIncludeNegated(false);
  }

  function openAspect(nextAspect: GoAspect) {
    if (toggledGoAspect(aspect, nextAspect) === null) {
      closeAspect();
      return;
    }
    setAspect(nextAspect);
    setDraftQuery("");
    setDraftEvidenceCode("");
    setQuery("");
    setEvidenceCode("");
    setIncludeNegated(false);
  }

  function closeAspect() {
    clearFilters();
    setAspect(null);
  }

  const response = state.data;
  const aspectCounts = new Map(response?.aspect_counts.map((item) => [item.aspect, item]) ?? []);
  return <article className="info-card go-evidence-card">
    <div className="go-evidence-heading"><div><p className="eyebrow">Annotation drill-down</p><h2>Gene Ontology evidence</h2></div>{response && <span>{response.total_or_estimate.value.toLocaleString()} terms</span>}</div>
    {response && <SourceContext source={response.provenance.display_name} release={response.provenance.source_release} recordGrain={response.provenance.record_grain} caveat={response.provenance.caveat ?? undefined} className="go-source-context" />}
    <p className="go-evidence-intro">Start with an ontology category, then reveal bounded term summaries and annotation records only when needed. Counts describe recorded evidence; they do not rank biological conclusions.</p>
    {response && <div className="go-aspect-overview" aria-label="Gene Ontology categories">{ASPECTS.map((value) => { const count = aspectCounts.get(value); const selected = aspect === value; return <button type="button" className={`go-aspect-card ${selected ? "is-selected" : ""}`} key={value} aria-pressed={selected} onClick={() => openAspect(value)}><span className="go-aspect-card-heading"><span><b>{value}</b><strong>{goAspectLabel(value)}</strong></span>{selected ? <ChevronDown aria-hidden="true" size={20} /> : <ChevronRight aria-hidden="true" size={20} />}</span><small>{ASPECT_DESCRIPTIONS[value]}</small><span className="go-aspect-metrics"><span><b>{(count?.term_count ?? 0).toLocaleString()}</b><small>Terms</small></span><span><b>{(count?.annotation_count ?? 0).toLocaleString()}</b><small>Annotations</small></span><span><b>{(count?.reference_count ?? 0).toLocaleString()}</b><small>References</small></span></span></button>; })}</div>}
    {aspect && <div className="go-category-browser"><div className="go-category-browser-heading"><div><span className="go-category-kicker">Selected category</span><h3>{goAspectLabel(aspect)} <span>{aspect}</span></h3></div><button type="button" className="quiet-button" onClick={closeAspect}>Back to category overview</button></div><form className="go-evidence-controls" aria-label={`Filter ${goAspectLabel(aspect)} terms`} onSubmit={applyTextFilters}><div className="go-filter-title"><ListFilter aria-hidden="true" size={18} /><strong>Filter this category</strong></div><label>Search terms or GO ID<input value={draftQuery} onChange={(event) => setDraftQuery(event.target.value)} placeholder="e.g. receptor or GO:0005006" /></label><label>Evidence code<input value={draftEvidenceCode} onChange={(event) => setDraftEvidenceCode(event.target.value)} placeholder="e.g. IDA" /></label><label className="go-negated-toggle"><input type="checkbox" checked={includeNegated} onChange={(event) => setIncludeNegated(event.target.checked)} /> Include NOT / negated annotations</label><div className="go-filter-actions"><button type="submit">Apply filters</button><button type="button" className="quiet-button" onClick={clearFilters}>Clear filters</button></div></form>{!includeNegated && <p className="go-negated-note"><strong>NOT annotations are excluded by default.</strong> Enable the explicit filter above to inspect negated records without mixing them into the positive summary.</p>}</div>}
    {state.kind === "loading" && <p className="go-evidence-status" role="status">Loading bounded GO term summaries…</p>}
    {state.kind === "error" && <p className="go-evidence-error" role="alert">{state.error} <button type="button" onClick={() => setRetry((value) => value + 1)}>Retry</button></p>}
    {state.kind === "ready" && aspect && <><p className="go-evidence-status">Showing {items.length.toLocaleString()} of {response!.total_or_estimate.value.toLocaleString()} {goAspectLabel(aspect).toLocaleLowerCase()} terms · {response!.annotation_count.toLocaleString()} annotation records match the active filters.</p>{items.length ? <ul className="go-term-list">{items.map((term) => <li key={`${term.aspect}-${term.go_id}`}><div className="go-term-main"><div className="go-term-identity"><ActionLink href={quickGoTermUrl(term.go_id)} external>{term.go_id}</ActionLink><span>{term.aspect}</span></div><strong>{term.go_term_name}</strong><span>{term.annotation_count.toLocaleString()} annotations · {term.reference_count.toLocaleString()} distinct references</span><small><b>Evidence codes</b> {term.evidence_codes.map((code) => `${code.evidence_code} (${code.annotation_count})`).join(", ") || "Not recorded"}</small></div><TermEvidence accession={accession} term={term} evidenceCode={evidenceCode} includeNegated={includeNegated} /></li>)}</ul> : <p className="empty-value">No GO terms match these filters.</p>}{cursor && <button type="button" className="quiet-button go-load-more" onClick={loadMore}>Load more terms</button>}</>}
  </article>;
}
