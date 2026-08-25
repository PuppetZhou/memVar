"use client";

import { useState } from "react";
import { ExpressionModality, ExpressionResponse } from "../lib/api";
import { useJsonResource } from "../lib/use-json-resource";
import { ExpressionDetails } from "./expression/expression-details";
import { ExpressionOverview } from "./expression/expression-overview";
import { EXPRESSION_SPECS } from "./expression/model";
import { DifferentialExpression } from "./expression/differential-expression";
import { StatusMessage } from "./status-message";

export function ExpressionPanel({ accession }: { accession: string }) {
  const state = useJsonResource<ExpressionResponse>(
    `/proteins/${encodeURIComponent(accession)}/expression?modality=all`,
    "Unable to load expression data.",
  );
  const [open, setOpen] = useState<Partial<Record<ExpressionModality, boolean>>>({});

  function selectCell(modality: ExpressionModality, columnId: string) {
    setOpen((current) => ({ ...current, [modality]: true }));
    window.requestAnimationFrame(() => window.requestAnimationFrame(() => {
      const target = document.getElementById(`expression-detail-${modality}-${encodeURIComponent(columnId)}`);
      target?.scrollIntoView({ behavior: "smooth", block: "center" });
      target?.focus({ preventScroll: true });
    }));
  }

  const groups = state.kind === "ready" ? state.response.groups : {};
  return <section id="expression" className="overview-section expression-section" aria-labelledby="expression-heading">
    <div className="section-heading"><p className="eyebrow">M3 expression evidence</p><h2 id="expression-heading">Expression</h2></div>
    <p className="section-intro">Compare tissue patterns across four independent expression modalities; units and missing states remain source-specific.</p>
    {state.kind === "loading" && <StatusMessage title="Loading expression overview">Retrieving four complete, bounded source modalities.</StatusMessage>}
    {state.kind === "error" && <StatusMessage title="Expression unavailable" tone="error">{state.error}</StatusMessage>}
    {state.kind === "ready" && <>
      <div className="evidence-panel expression-panel"><ExpressionOverview groups={groups} onSelect={selectCell} /></div>
      <div className="expression-source-details" aria-label="Expression source details">
        <div className="expression-details-heading"><div><p className="eyebrow">Original evidence</p><h3>Source records</h3></div><span>Expand a modality for tissues, values and provenance</span></div>
        {EXPRESSION_SPECS.map((spec) => groups[spec.key] ? <ExpressionDetails key={spec.key} group={groups[spec.key]!} open={Boolean(open[spec.key])} onToggle={() => setOpen((current) => ({ ...current, [spec.key]: !current[spec.key] }))} /> : <StatusMessage key={spec.key} title={`No ${spec.label} response`}>This modality was not included in the expression response.</StatusMessage>)}
      </div>
    </>}
    <DifferentialExpression accession={accession} />
  </section>;
}
