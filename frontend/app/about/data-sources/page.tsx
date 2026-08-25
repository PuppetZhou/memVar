"use client";

import { DataSourcesResponse } from "../../../lib/api";
import { useJsonResource } from "../../../lib/use-json-resource";
import { StatusMessage } from "../../../components/status-message";
import { formatSourceRelease, formatTermLabel } from "../../../lib/display-labels";

export default function DataSourcesPage() {
  const state = useJsonResource<DataSourcesResponse>("/data-sources", "Unable to load the source registry.");

  return <main id="main-content" className="page-main shell">
    <div className="page-heading source-page-heading"><p className="eyebrow">memVar source registry</p><h1>Data sources and interpretation</h1><p>memVar presents source-specific evidence records. It does not create a combined pathogenicity, disease, expression, or interaction score.</p></div>
    {state.kind === "loading" && <StatusMessage title="Loading source registry">Retrieving the website-owned registry and its declared caveats.</StatusMessage>}
    {state.kind === "error" && <StatusMessage title="Source registry unavailable" tone="error">{state.error}</StatusMessage>}
    {state.kind === "ready" && <div className="source-registry-grid">{state.response.items.map((source) => <article className="source-registry-card" key={source.source_id}><h2>{source.display_name}</h2><dl className="data-list"><div className="data-row"><dt>Layer</dt><dd>{formatTermLabel(source.layer)}</dd></div><div className="data-row"><dt>Source release</dt><dd>{formatSourceRelease(source.source_release)}</dd></div><div className="data-row"><dt>Record grain</dt><dd>{source.record_grain ?? "Not recorded"}</dd></div><div className="data-row"><dt>Interpretation boundary</dt><dd>{source.caveat ?? "No additional caveat is declared in the current registry."}</dd></div></dl></article>)}</div>}
  </main>;
}
