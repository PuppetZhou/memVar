"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { InteractionDetailItem, InteractionDetailResponse, InteractionSource, InteractionSummaryResponse, MutationEffectResponse } from "../lib/api";
import { getJson } from "../lib/api-client";
import { useJsonResource } from "../lib/use-json-resource";
import { StatusMessage } from "./status-message";
import { formatFieldLabel, formatTermLabel } from "../lib/display-labels";

const SOURCES: InteractionSource[] = ["BioGRID", "IntAct"];

type Filters = { source: InteractionSource | ""; contextClass: string; context: string; category: string };

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not available";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumSignificantDigits: 7 });
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.map(valueText).join(", ");
  if (typeof value === "object") return Object.entries(value as Record<string, unknown>).map(([key, item]) => `${formatFieldLabel(key)}: ${valueText(item)}`).join(" · ");
  if (typeof value === "string" && /^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$/i.test(value)) return formatTermLabel(value);
  return String(value);
}

function sourceDetails(item: InteractionDetailItem) { return Object.values(item.source_specific)[0] ?? {}; }

function partnerText(item: InteractionDetailItem) {
  const partner = item.partner;
  return valueText(partner.display_name ?? partner.symbol ?? partner.accession ?? partner.raw_id ?? partner);
}

function InteractionRow({ item, open, onToggle }: { item: InteractionDetailItem; open: boolean; onToggle: () => void }) {
  const details = sourceDetails(item);
  const negative = item.source_database === "IntAct" && details.is_negative === true;
  return <>
    <tr className={open ? "expanded" : ""}>
      <th scope="row"><button type="button" className="row-toggle" aria-expanded={open} onClick={onToggle}><span aria-hidden="true">{open ? "▾" : "▸"}</span><span>{partnerText(item)}</span></button><small>{item.page_role ? formatTermLabel(item.page_role) : "Protein membership role unavailable"}</small></th>
      <td>{formatTermLabel(item.interaction_category)}{negative && <span className="negative-badge">Negative evidence</span>}</td>
      <td>{valueText(details.detection_method ?? details.experimental_system ?? details.interaction_type)}</td>
      <td>{item.publication ?? "Not available"}</td>
      <td>{item.context ?? "Not available"}<small>{item.context_class ? formatTermLabel(item.context_class) : "Context class unavailable"}</small></td>
      <td>{item.native_interaction_id ?? "Not available"}</td>
    </tr>
    {open && <tr className="detail-row"><td colSpan={6}><section className="interaction-detail"><h3>{item.source_database} source-specific evidence</h3><dl className="detail-fields">{Object.entries(details).filter(([, value]) => value !== null && value !== "").map(([key, value]) => <div key={key}><dt>{formatFieldLabel(key)}</dt><dd>{typeof value === "string" && ["interaction_type", "experimental_system_type", "role", "page_role"].includes(key) ? formatTermLabel(value) : valueText(value)}</dd></div>)}</dl>{item.source_database === "IntAct" && <p>Expansion method, negative evidence, endpoint features, and host/context fields remain source-specific; a context label alone does not establish in vivo activity.</p>}</section></td></tr>}
  </>;
}

function MutationEffects({ accession }: { accession: string }) {
  const [cursor, setCursor] = useState<string | null>(null);
  const [history, setHistory] = useState<(string | null)[]>([]);
  const [state, setState] = useState<{ kind: "loading" | "error" | "ready"; response?: MutationEffectResponse; error?: string }>({ kind: "loading" });
  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: "50" });
    if (cursor) params.set("cursor", cursor);
    setState({ kind: "loading" });
    getJson<MutationEffectResponse>(`/proteins/${encodeURIComponent(accession)}/interactions/mutation-effects?${params}`, controller.signal)
      .then((response) => setState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load IntAct mutation effects." });
      });
    return () => controller.abort();
  }, [accession, cursor]);
  const response = state.response;
  const start = history.length * 50 + 1;
  const end = response ? Math.min(start + response.items.length - 1, response.total_or_estimate.value) : 0;
  return <section className="mutation-effects-panel" aria-label="IntAct mutation effects"><p className="interaction-caveat">IntAct mutation effects are a separate feature–interaction evidence collection and are not merged into general interaction counts or genomic variant records.</p>{state.kind === "loading" && <p className="inline-loading" role="status">Loading IntAct mutation effects…</p>}{state.kind === "error" && <p className="inline-error" role="alert">{state.error}</p>}{response && <><div className="table-scroll"><table className="interaction-table"><thead><tr><th scope="col">Feature</th><th scope="col">Effect type</th><th scope="col">Affected protein</th><th scope="col">Interaction</th><th scope="col">Publication</th></tr></thead><tbody>{response.items.map((item, index) => <tr key={`${item.feature_accession ?? "feature"}-${index}`}><th scope="row">{valueText(item.feature_short_label ?? item.feature_accession ?? item.feature_ranges)}<small>{item.feature_ranges ?? "Feature range unavailable"}</small></th><td>{valueText(item.feature_type)}</td><td>{valueText(item.affected_protein.symbol ?? item.affected_protein.accession)}<small>{[item.affected_protein.full_name, item.affected_protein.organism].filter(Boolean).join(" · ") || "Full name and organism unavailable"}</small></td><td>{valueText(item.interaction_accession)}</td><td>{valueText(item.pubmed_id)}</td></tr>)}</tbody></table></div><div className="pagination"><button className="quiet-button" type="button" disabled={history.length === 0} onClick={() => { const previous = history[history.length - 1] ?? null; setHistory(history.slice(0, -1)); setCursor(previous); }}>Previous</button><span>Showing {response.items.length ? `${start}–${end}` : "0"} of {response.total_or_estimate.value.toLocaleString()}</span><button className="quiet-button" type="button" disabled={!response.next_cursor} onClick={() => { setHistory([...history, cursor]); setCursor(response.next_cursor); }}>Next</button></div></>}</section>;
}

function filtersFromParams(params: URLSearchParams): Filters {
  const source = params.get("source") ?? "";
  return { source: SOURCES.includes(source as InteractionSource) ? source as InteractionSource : "", contextClass: params.get("context_class") ?? "", context: params.get("context") ?? "", category: params.get("category") ?? "" };
}

export function InteractionBrowser({ accession }: { accession: string }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const initial = useMemo(() => filtersFromParams(new URLSearchParams(searchParams.toString())), [searchParams]);
  const [tab, setTab] = useState<"evidence" | "mutation">("evidence");
  const [filters, setFilters] = useState<Filters>(initial);
  const [applied, setApplied] = useState<Filters>(initial);
  const summaryState = useJsonResource<InteractionSummaryResponse>(
    `/proteins/${encodeURIComponent(accession)}/interactions/summary`,
    "Unable to load interaction filter options.",
  );
  const [state, setState] = useState<{ kind: "idle" | "loading" | "error" | "ready"; response?: InteractionDetailResponse; error?: string }>({ kind: initial.source ? "loading" : "idle" });
  const [cursor, setCursor] = useState<string | null>(null);
  const [history, setHistory] = useState<(string | null)[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    if (!applied.source || tab !== "evidence") { setState({ kind: "idle" }); return; }
    const controller = new AbortController(); const params = new URLSearchParams({ source: applied.source, limit: "50" });
    if (applied.contextClass) params.set("context_class", applied.contextClass); if (applied.context) params.set("context", applied.context); if (applied.category) params.set("category", applied.category); if (cursor) params.set("cursor", cursor);
    setState({ kind: "loading" }); setExpanded(null);
    getJson<InteractionDetailResponse>(`/proteins/${encodeURIComponent(accession)}/interactions?${params}`, controller.signal).then((response) => setState({ kind: "ready", response })).catch((error: unknown) => { if (error instanceof DOMException && error.name === "AbortError") return; setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load interaction details." }); });
    return () => controller.abort();
  }, [accession, applied, cursor, tab]);

  const summary = summaryState.kind === "ready" ? summaryState.response : null;
  const sourceItems = summary?.items.filter((item) => item.source_database === filters.source) ?? [];
  const contextClasses = Array.from(new Set(sourceItems.map((item) => item.context_class).filter((value): value is string => Boolean(value))));
  const contexts = Array.from(new Set(sourceItems.filter((item) => !filters.contextClass || item.context_class === filters.contextClass).map((item) => item.context).filter((value): value is string => Boolean(value))));
  const categories = Array.from(new Set(sourceItems.filter((item) => (!filters.contextClass || item.context_class === filters.contextClass) && (!filters.context || item.context === filters.context)).map((item) => item.interaction_category).filter((value): value is string => Boolean(value))));
  const response = state.response; const start = history.length * 50 + 1; const end = response ? Math.min(start + response.items.length - 1, response.total_or_estimate.value) : 0;

  function submit(event: FormEvent) { event.preventDefault(); if (!filters.source) return; setApplied(filters); setCursor(null); setHistory([]); const params = new URLSearchParams({ source: filters.source }); if (filters.contextClass) params.set("context_class", filters.contextClass); if (filters.context) params.set("context", filters.context); if (filters.category) params.set("category", filters.category); router.replace(`${pathname}?${params}`, { scroll: false }); }
  function reset() { const next: Filters = { source: "", contextClass: "", context: "", category: "" }; setFilters(next); setApplied(next); setCursor(null); setHistory([]); router.replace(pathname, { scroll: false }); }

  if (summaryState.kind === "error") {
    return <StatusMessage title="Interaction filters unavailable" tone="error">{summaryState.error}</StatusMessage>;
  }

  return <div className="interaction-browser"><div className="source-tabs" role="group" aria-label="Interaction detail view"><button type="button" aria-pressed={tab === "evidence"} onClick={() => setTab("evidence")}>Interaction evidence<span>source-filtered records</span></button><button type="button" aria-pressed={tab === "mutation"} onClick={() => setTab("mutation")}>IntAct mutation effects<span>separate evidence collection</span></button></div><div className="evidence-body">{tab === "mutation" ? <MutationEffects accession={accession} /> : <><form className="interaction-filters" onSubmit={submit}><label>Source <strong aria-hidden="true">*</strong><select required value={filters.source} onChange={(event) => setFilters({ source: event.target.value as InteractionSource | "", contextClass: "", context: "", category: "" })}><option value="">Select source</option>{SOURCES.map((source) => <option key={source}>{source}</option>)}</select></label><label>Context class<select value={filters.contextClass} disabled={!filters.source} onChange={(event) => setFilters({ ...filters, contextClass: event.target.value, context: "", category: "" })}><option value="">All context classes</option>{contextClasses.map((value) => <option key={value} value={value}>{formatTermLabel(value)}</option>)}</select></label><label>Context<select value={filters.context} disabled={!filters.source} onChange={(event) => setFilters({ ...filters, context: event.target.value, category: "" })}><option value="">All contexts</option>{contexts.map((value) => <option key={value}>{value}</option>)}</select></label><label>Category<select value={filters.category} disabled={!filters.source} onChange={(event) => setFilters({ ...filters, category: event.target.value })}><option value="">All categories</option>{categories.map((value) => <option key={value} value={value}>{formatTermLabel(value)}</option>)}</select></label><div className="filter-actions"><button className="primary-button" type="submit" disabled={!filters.source}>Apply</button><button className="quiet-button" type="button" onClick={reset}>Reset</button></div></form>{applied.source && <p className="interaction-caveat"><strong>Active source: {applied.source}.</strong> {applied.source === "BioGRID" ? "Physical and genetic evidence remain separate." : "IntAct negative evidence and expansion context are retained; the context is curation scope, not proof of activity."}</p>}{state.kind === "idle" && <StatusMessage title="Choose an interaction source">A source is required so each request reads one bounded, source-specific detail collection.</StatusMessage>}{state.kind === "loading" && <p className="inline-loading" role="status">Loading interaction records…</p>}{state.kind === "error" && <p className="inline-error" role="alert">{state.error}</p>}{response && <><p className="record-summary"><strong>{response.total_or_estimate.value.toLocaleString()}</strong> source-specific evidence records <span>Showing {response.items.length ? `${start}–${end}` : "0"}</span></p><div className="table-scroll"><table className="interaction-table"><thead><tr><th scope="col">Partner</th><th scope="col">Category</th><th scope="col">Method/type</th><th scope="col">Publication</th><th scope="col">Context</th><th scope="col">Native interaction ID</th></tr></thead><tbody>{response.items.map((item, index) => <InteractionRow key={`${item.native_interaction_id}-${index}`} item={item} open={expanded === index} onToggle={() => setExpanded(expanded === index ? null : index)} />)}</tbody></table></div><div className="pagination"><button className="quiet-button" type="button" disabled={history.length === 0} onClick={() => { const previous = history[history.length - 1] ?? null; setHistory(history.slice(0, -1)); setCursor(previous); }}>Previous</button><span>Showing {response.items.length ? `${start}–${end}` : "0"} of {response.total_or_estimate.value.toLocaleString()}</span><button className="quiet-button" type="button" disabled={!response.next_cursor} onClick={() => { setHistory([...history, cursor]); setCursor(response.next_cursor); }}>Next</button></div></>}</>}</div></div>;
}

export function InteractionDetailPageHeading({ accession }: { accession: string }) { return <div className="page-heading interaction-page-heading"><p className="eyebrow">Protein-scoped interaction evidence</p><h1>{accession} interactions</h1><p>Browse a bounded, source-specific evidence collection. Context labels describe dataset curation scope and do not establish tissue- or disease-specific interaction activity.</p><Link className="full-page-link" href={`/protein/${encodeURIComponent(accession)}#interactions`}><ArrowLeft size={16} aria-hidden="true" /> Back to protein overview</Link></div>; }
