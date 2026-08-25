"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { QtlDetailItem, QtlDetailResponse, QtlSource, QtlSummaryResponse } from "../lib/api";
import { getJson } from "../lib/api-client";
import { formatFieldLabel, formatSourceRelease, formatTermLabel } from "../lib/display-labels";

type Filters = { source: QtlSource | ""; type: string; tissue: string; context: string; population: string };

const SOURCES: QtlSource[] = ["GTEx", "eQTLGen", "QTLbase"];

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not available";
  if (typeof value === "number") return Math.abs(value) > 0 && Math.abs(value) < .001 ? value.toExponential(4) : value.toLocaleString(undefined, { maximumSignificantDigits: 7 });
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.map(valueText).join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function CompactFields({ title, record }: { title: string; record: Record<string, unknown> | null }) {
  const entries = Object.entries(record ?? {}).filter(([, value]) => value !== null && value !== "");
  return <div className="compact-fields"><strong>{title}</strong>{entries.length ? entries.map(([key, value]) => <span key={key}><small>{formatFieldLabel(key)}</small>{valueText(value)}</span>) : <span>Not available</span>}</div>;
}

function locusText(item: QtlDetailItem) {
  const locus = item.variant_or_locus;
  if (locus.identifier) return String(locus.identifier);
  if (locus.chromosome && locus.position !== null && locus.position !== undefined) return `chr${locus.chromosome}:${valueText(locus.position)}`;
  return "Locus unavailable";
}

function QtlRow({ item, open, onToggle }: { item: QtlDetailItem; open: boolean; onToggle: () => void }) {
  const sourceSpecific = Object.values(item.source_specific)[0] ?? {};
  return <>
    <tr className={open ? "expanded" : ""}>
      <th scope="row"><button type="button" className="row-toggle" aria-expanded={open} onClick={onToggle}><span aria-hidden="true">{open ? "▾" : "▸"}</span><span>{locusText(item)}</span></button><small>{item.genome_build} · {typeof item.variant_or_locus.kind === "string" ? formatTermLabel(item.variant_or_locus.kind) : valueText(item.variant_or_locus.kind)}</small></th>
      <td><CompactFields title="Gene" record={item.gene} /></td>
      <td><CompactFields title="Phenotype" record={item.phenotype} /></td>
      <td>{item.tissue ?? item.context ?? "Not available"}{item.population && <small>Population {item.population}</small>}</td>
      <td className="numeric">{valueText(item.p_value)}</td>
      <td><strong>{item.evidence_semantics}</strong><small>{item.source_database} · {formatTermLabel(item.qtl_type)}</small></td>
      <td>{formatSourceRelease(item.source_release)}</td>
    </tr>
    {open && <tr className="detail-row"><td colSpan={7}><section className="qtl-source-detail" aria-label={`${item.source_database} source-specific fields`}><h3>{item.source_database} source-specific fields</h3><CompactFields title="Source record" record={sourceSpecific} /><p>{item.source_database === "QTLbase" ? "This chromosome-position locus is an association and is not treated as an exact REF/ALT/rsID variant." : `Genome build ${item.genome_build} remains part of this record.`}</p></section></td></tr>}
  </>;
}

function filtersFromParams(params: URLSearchParams): Filters {
  const sourceValue = params.get("source") ?? "";
  return {
    source: SOURCES.includes(sourceValue as QtlSource) ? sourceValue as QtlSource : "",
    type: params.get("type") ?? "",
    tissue: params.get("tissue") ?? "",
    context: params.get("context") ?? "",
    population: params.get("population") ?? "",
  };
}

export function QtlBrowser({ accession }: { accession: string }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const initial = useMemo(() => filtersFromParams(new URLSearchParams(searchParams.toString())), [searchParams]);
  const [filters, setFilters] = useState<Filters>(initial);
  const [applied, setApplied] = useState<Filters>(initial);
  const [summary, setSummary] = useState<QtlSummaryResponse | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [cursor, setCursor] = useState<string | null>(null);
  const [cursorHistory, setCursorHistory] = useState<(string | null)[]>([]);
  const [state, setState] = useState<{ kind: "idle" | "loading" | "error" | "ready"; response?: QtlDetailResponse; error?: string }>({ kind: applied.source && applied.type ? "loading" : "idle" });
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getJson<QtlSummaryResponse>(`/proteins/${encodeURIComponent(accession)}/qtl/summary`, controller.signal)
      .then(setSummary)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setSummaryError(error instanceof Error ? error.message : "Unable to load available QTL filters.");
      });
    return () => controller.abort();
  }, [accession]);

  useEffect(() => {
    if (!applied.source || !applied.type) { setState({ kind: "idle" }); return; }
    const controller = new AbortController();
    const params = new URLSearchParams({ source: applied.source, qtl_type: applied.type, limit: "50" });
    if (applied.tissue) params.set("tissue", applied.tissue);
    if (applied.context) params.set("context", applied.context);
    if (applied.population) params.set("population", applied.population);
    if (cursor) params.set("cursor", cursor);
    setState({ kind: "loading" }); setExpanded(null);
    getJson<QtlDetailResponse>(`/proteins/${encodeURIComponent(accession)}/qtl?${params}`, controller.signal)
      .then((response) => setState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load QTL details." });
      });
    return () => controller.abort();
  }, [accession, applied, cursor]);

  const sourceItems = summary?.items.filter((item) => item.source_database === filters.source) ?? [];
  const availableTypes = Array.from(new Set(sourceItems.map((item) => item.qtl_type)));
  const tissueOptions = Array.from(new Set(sourceItems.filter((item) => !filters.type || item.qtl_type === filters.type).map((item) => item.tissue_or_context).filter((value): value is string => Boolean(value))));
  const populationOptions = Array.from(new Set(sourceItems.filter((item) => (!filters.type || item.qtl_type === filters.type) && (!filters.tissue || item.tissue_or_context === filters.tissue)).map((item) => item.population).filter((value): value is string => Boolean(value))));

  function selectSource(source: QtlSource | "") {
    const firstType = summary?.items.find((item) => item.source_database === source)?.qtl_type ?? "";
    setFilters({ source, type: firstType, tissue: "", context: "", population: "" });
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!filters.source || !filters.type) return;
    const clean = { ...filters };
    if (clean.source === "GTEx") { clean.context = ""; clean.population = ""; }
    if (clean.source === "eQTLGen") { clean.tissue = ""; clean.population = ""; }
    setFilters(clean); setApplied(clean); setCursor(null); setCursorHistory([]);
    const params = new URLSearchParams({ source: clean.source, type: clean.type });
    if (clean.tissue) params.set("tissue", clean.tissue);
    if (clean.context) params.set("context", clean.context);
    if (clean.population) params.set("population", clean.population);
    router.replace(`${pathname}?${params}`, { scroll: false });
  }

  function reset() {
    const next: Filters = { source: "", type: "", tissue: "", context: "", population: "" };
    setFilters(next); setApplied(next); setCursor(null); setCursorHistory([]); router.replace(pathname, { scroll: false });
  }

  const response = state.response;
  const activeLabels = [applied.source, applied.type && formatTermLabel(applied.type), applied.tissue && `tissue: ${applied.tissue}`, applied.context && `context: ${applied.context}`, applied.population && `population: ${applied.population}`].filter(Boolean);
  const pageStart = cursorHistory.length * 50 + 1;
  const pageEnd = response ? Math.min(pageStart + response.items.length - 1, response.total_or_estimate.value) : 0;

  return <div className="qtl-browser">
    <form className="qtl-filters" onSubmit={submit}>
      <label>Source <strong aria-hidden="true">*</strong><select required value={filters.source} onChange={(event) => selectSource(event.target.value as QtlSource | "")}><option value="">Select source</option>{SOURCES.map((source) => <option key={source}>{source}</option>)}</select></label>
      <label>QTL type <strong aria-hidden="true">*</strong><select required value={filters.type} disabled={!filters.source} onChange={(event) => setFilters({ ...filters, type: event.target.value, tissue: "", population: "" })}><option value="">Select type</option>{availableTypes.map((type) => <option key={type} value={type}>{formatTermLabel(type)}</option>)}</select></label>
      {filters.source !== "eQTLGen" && <label>Tissue<select value={filters.tissue} onChange={(event) => setFilters({ ...filters, tissue: event.target.value, population: "" })}><option value="">All tissues</option>{tissueOptions.map((tissue) => <option key={tissue}>{tissue}</option>)}</select></label>}
      {filters.source === "QTLbase" && <label>Context<input value={filters.context} placeholder="Assay context" onChange={(event) => setFilters({ ...filters, context: event.target.value })} /></label>}
      {filters.source === "QTLbase" && <label>Population<select value={filters.population} onChange={(event) => setFilters({ ...filters, population: event.target.value })}><option value="">All populations</option>{populationOptions.map((population) => <option key={population}>{population}</option>)}</select></label>}
      {filters.source === "eQTLGen" && <label>Context<input value={filters.context} placeholder="blood meta-analysis" onChange={(event) => setFilters({ ...filters, context: event.target.value })} /></label>}
      <div className="filter-actions"><button type="submit" className="primary-button">Apply</button><button type="button" className="quiet-button" onClick={reset}>Reset</button></div>
    </form>
    {summaryError && <p className="inline-error" role="alert">{summaryError}</p>}
    <div className="active-filter-bar"><span><strong>Active filters:</strong> {activeLabels.length ? activeLabels.join(" · ") : "Choose a source and QTL type"}</span>{response && <span><strong>Showing {response.items.length ? `${pageStart}–${pageEnd}` : "0"} of {response.total_or_estimate.value.toLocaleString()}</strong></span>}</div>
    {state.kind === "idle" && <div className="qtl-required-state"><h2>Source and QTL type are required</h2><p>This keeps every request inside one protein-mapped source/type bucket. Choose both filters to load a bounded page of 50 records.</p></div>}
    {state.kind === "loading" && <p className="inline-loading" role="status">Loading a bounded page of QTL records…</p>}
    {state.kind === "error" && <p className="inline-error" role="alert">{state.error}</p>}
    {response && <>
      <div className="semantics-banner persistent-semantics"><strong>{response.source_database} · {formatTermLabel(response.qtl_type)}</strong><span>{response.source_semantics.evidence_semantics} / {response.source_semantics.genome_build}</span></div>
      {response.items.length === 0 ? <div className="qtl-required-state"><h2>No matching QTL records</h2><p>The active source-specific filters returned no records for this protein.</p></div> : <div className="table-scroll"><table className="qtl-table">
        <thead><tr><th scope="col">Variant or locus / build</th><th scope="col">Gene</th><th scope="col">Phenotype</th><th scope="col">Tissue / context</th><th scope="col" className="numeric">P value</th><th scope="col">Semantics</th><th scope="col">Release</th></tr></thead>
        <tbody>{response.items.map((item, index) => <QtlRow item={item} open={expanded === index} onToggle={() => setExpanded(expanded === index ? null : index)} key={`${locusText(item)}-${index}`} />)}</tbody>
      </table></div>}
      <div className="pagination"><button className="quiet-button" type="button" disabled={cursorHistory.length === 0} onClick={() => { const history = [...cursorHistory]; const previous = history.pop() ?? null; setCursorHistory(history); setCursor(previous); }}>Previous</button><span>Page {cursorHistory.length + 1} · 50 records maximum</span><button className="quiet-button" type="button" disabled={!response.next_cursor} onClick={() => { setCursorHistory((history) => [...history, cursor]); setCursor(response.next_cursor); }}>Next</button></div>
    </>}
    <p className="full-page-link"><Link href={`/protein/${encodeURIComponent(accession)}#qtl`}><ArrowLeft size={16} aria-hidden="true" /> Back to protein overview</Link></p>
  </div>;
}
