"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { InteractionSource, InteractionSummaryItem, InteractionSummaryResponse } from "../lib/api";
import { useJsonResource } from "../lib/use-json-resource";
import { StatusMessage } from "./status-message";
import { formatTermLabel } from "../lib/display-labels";
import { Disclosure } from "./ui/disclosure";

const SOURCES: InteractionSource[] = ["BioGRID", "IntAct"];

function detailsHref(accession: string, item: InteractionSummaryItem) {
  const params = new URLSearchParams({ source: item.source_database });
  if (item.context_class) params.set("context_class", item.context_class);
  if (item.context) params.set("context", item.context);
  if (item.interaction_category) params.set("category", item.interaction_category);
  return `/protein/${encodeURIComponent(accession)}/interactions?${params}`;
}

function contextHref(accession: string, item: InteractionSummaryItem) {
  const params = new URLSearchParams({ source: item.source_database });
  if (item.context_class) params.set("context_class", item.context_class);
  if (item.context) params.set("context", item.context);
  return `/protein/${encodeURIComponent(accession)}/interactions?${params}`;
}

type ContextSummary = {
  source: InteractionSource;
  contextClass: string | null;
  context: string | null;
  evidenceRecordCount: number;
  categories: InteractionSummaryItem[];
};

function contextSummaries(items: InteractionSummaryItem[]): ContextSummary[] {
  const grouped = new Map<string, ContextSummary>();
  for (const item of items) {
    const key = JSON.stringify([item.context_class, item.context]);
    const existing = grouped.get(key);
    if (existing) {
      existing.evidenceRecordCount += item.evidence_record_count;
      existing.categories.push(item);
    } else {
      grouped.set(key, {
        source: item.source_database,
        contextClass: item.context_class,
        context: item.context,
        evidenceRecordCount: item.evidence_record_count,
        categories: [item],
      });
    }
  }
  return Array.from(grouped.values()).sort((left, right) =>
    right.evidenceRecordCount - left.evidenceRecordCount
      || (left.context ?? "").localeCompare(right.context ?? ""),
  );
}

function categoryClass(category: string | null) {
  const normalized = category?.toLocaleLowerCase();
  return ["physical", "genetic", "positive", "negative"].includes(normalized ?? "")
    ? `category-${normalized}`
    : "category-other";
}

function sourceNote(source: InteractionSource) {
  return source === "BioGRID"
    ? "Physical and genetic evidence are separate categories; counts are not unique protein pairs."
    : "Context labels describe curation scope, not interaction activity in that tissue or disease. Negative evidence and expansion context remain available in details.";
}

export function InteractionSummary({ accession }: { accession: string }) {
  const [source, setSource] = useState<InteractionSource>("BioGRID");
  const [detailsOpen, setDetailsOpen] = useState(false);
  const state = useJsonResource<InteractionSummaryResponse>(
    `/proteins/${encodeURIComponent(accession)}/interactions/summary`,
    "Unable to load interaction summary.",
  );

  const response = state.kind === "ready" ? state.response : undefined;
  const items = useMemo(() => response?.items.filter((item) => item.source_database === source) ?? [], [response, source]);
  const contexts = useMemo(() => contextSummaries(items), [items]);
  const maximum = Math.max(0, ...contexts.map((item) => item.evidenceRecordCount));

  return <section id="interactions" className="overview-section" aria-labelledby="interactions-heading">
    <div className="section-heading"><p className="eyebrow">M4 interaction evidence</p><h2 id="interactions-heading">Interaction summary</h2></div>
    <p className="section-intro">Each count separates retained evidence records from distinct native interaction identifiers. Neither measure is presented as a count of unique protein–protein edges.</p>
    <div className="evidence-panel interaction-summary-panel">
      <div className="source-tabs" role="group" aria-label="Interaction source">
        {SOURCES.map((candidate) => <button key={candidate} type="button" aria-pressed={source === candidate} onClick={() => { setSource(candidate); setDetailsOpen(false); }}>{candidate}<span>{candidate === "BioGRID" ? "physical and genetic evidence" : "context memberships and negative evidence"}</span></button>)}
      </div>
      <div className="evidence-body" tabIndex={0}>
        {state.kind === "loading" && <p className="inline-loading" role="status">Loading source and context summaries…</p>}
        {state.kind === "error" && <p className="inline-error" role="alert">{state.error}</p>}
        {state.kind === "ready" && <>
          <p className="interaction-caveat"><strong>{source}:</strong> {sourceNote(source)}</p>
          {items.length === 0 ? <StatusMessage title={`No ${source} records`}>No protein-mapped records for this source are present in the current website data release.</StatusMessage> : <>
            <section className="interaction-context-chart" aria-labelledby={`${source.toLocaleLowerCase()}-context-chart-heading`}>
              <div className="interaction-chart-heading">
                <h3 id={`${source.toLocaleLowerCase()}-context-chart-heading`}>Evidence records by curation context</h3>
                <span>{contexts.length.toLocaleString()} contexts</span>
              </div>
              <div className="interaction-category-legend" aria-label="Interaction categories">
                {Array.from(new Set(items.map((item) => item.interaction_category ?? "unavailable"))).map((category) => <span key={category}><i className={categoryClass(category)} aria-hidden="true" />{formatTermLabel(category)}</span>)}
              </div>
              <ul className="interaction-context-bars">
                {contexts.map((context) => {
                  const categoryDescription = context.categories.map((item) => `${formatTermLabel(item.interaction_category)} ${item.evidence_record_count.toLocaleString()}`).join(", ");
                  return <li key={`${context.contextClass}-${context.context}`}>
                    <Link href={contextHref(accession, context.categories[0])} aria-label={`${context.context ?? "Context unavailable"}, ${context.evidenceRecordCount.toLocaleString()} evidence records: ${categoryDescription}. Open filtered details.`}>
                      <span className="interaction-context-label"><strong>{context.context ?? "Context unavailable"}</strong><small>{context.contextClass ? formatTermLabel(context.contextClass) : "Context class unavailable"}</small></span>
                      <span className="interaction-bar-scale" aria-hidden="true"><span className="interaction-bar-fill" style={{ width: `${maximum ? Math.max(1, context.evidenceRecordCount / maximum * 100) : 0}%` }}>{context.categories.map((item, index) => <i key={`${item.interaction_category}-${index}`} className={categoryClass(item.interaction_category)} style={{ flexGrow: item.evidence_record_count }} />)}</span></span>
                      <strong className="interaction-context-count">{context.evidenceRecordCount.toLocaleString()}</strong>
                    </Link>
                  </li>;
                })}
              </ul>
            </section>
            <Disclosure open={detailsOpen} onToggle={() => setDetailsOpen(!detailsOpen)} id={`${source.toLocaleLowerCase()}-interaction-context-details`} className="interaction-context-disclosure" label={`Explore ${source} context and category details`}>
              <div className="interaction-summary-grid" role="list" aria-label={`${source} interaction context and category details`}>
                {items.map((item, index) => <Link key={`${item.context_class}-${item.context}-${item.interaction_category}-${index}`} href={detailsHref(accession, item)} className="interaction-summary-card" role="listitem">
                  <span>{item.context ?? "Context unavailable"}</span>
                  <small>{item.context_class ? formatTermLabel(item.context_class) : "Context class unavailable"} · {item.interaction_category ? formatTermLabel(item.interaction_category) : "Category unavailable"}</small>
                  <dl><div><dt>Evidence records</dt><dd>{item.evidence_record_count.toLocaleString()}</dd></div><div><dt>Distinct native IDs</dt><dd>{item.distinct_native_interaction_count.toLocaleString()}</dd></div></dl>
                  <em>Open filtered details →</em>
                </Link>)}
              </div>
            </Disclosure>
          </>}
        </>}
      </div>
    </div>
  </section>;
}
