"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { EChartsType } from "echarts";
import { ChevronRight, RotateCcw } from "lucide-react";
import {
  DifferentialExpressionContrast,
  DifferentialExpressionDataset,
  DifferentialExpressionSummaryResponse,
  DifferentialExpressionVolcanoResponse,
  VolcanoPoint,
} from "../../lib/api";
import { getJson } from "../../lib/api-client";
import {
  contrastDirection,
  DE_SORT_RULE,
  differentialExpressionCounts,
  formatDeNumber,
  sortDifferentialExpressionDatasets,
} from "../../lib/differential-expression-view";
import { formatTermLabel } from "../../lib/display-labels";
import { StatusMessage } from "../status-message";
import { SourceContext } from "../ui/source-context";

const POINT = {
  log2fc: 0,
  negLog10Fdr: 1,
  geneSymbol: 2,
  ensemblGeneId: 3,
  meanExpression: 4,
  rawFdr: 5,
  direction: 6,
  isMembrane: 11,
  isTarget: 12,
} as const;
const MEMBRANE_PAGE_SIZE = 25;
const EXPECTED_POINT_COLUMNS = ["log2fc", "neg_log10_fdr", "gene_symbol", "ensembl_gene_id", "mean_expression", "raw_fdr", "direction", "passes_expression_filter", "is_fdr_significant", "passes_log2fc_threshold", "is_significant_with_effect", "is_membrane_mapped", "is_current_target"];

let echartsPromise: Promise<typeof import("echarts")> | null = null;
function loadEcharts() {
  if (!echartsPromise) {
    echartsPromise = import("echarts").catch((error) => {
      echartsPromise = null;
      throw error;
    });
  }
  return echartsPromise;
}

function validateVolcanoResponse(response: DifferentialExpressionVolcanoResponse) {
  if (response.point_columns.length !== EXPECTED_POINT_COLUMNS.length || response.point_columns.some((column, index) => column !== EXPECTED_POINT_COLUMNS[index])) {
    throw new Error("The volcano point-column contract does not match this website release.");
  }
  if (response.points.length !== response.counts.plotted || response.counts.plotted + response.counts.unplottable !== response.counts.tested) {
    throw new Error("The volcano point counts do not satisfy the tested-gene contract.");
  }
  if (response.points.some((point) => point.length !== EXPECTED_POINT_COLUMNS.length || !Number.isFinite(point[POINT.log2fc]) || !Number.isFinite(point[POINT.negLog10Fdr]) || !Number.isFinite(point[POINT.rawFdr]))) {
    throw new Error("The volcano response contains an invalid plotting coordinate.");
  }
  return response;
}

function geneName(point: VolcanoPoint) {
  return point[POINT.geneSymbol] || point[POINT.ensemblGeneId] || "Unnamed gene";
}

function directionLabel(value: VolcanoPoint[6]) {
  if (value === "up") return "Upregulated";
  if (value === "down") return "Downregulated";
  return "Not significant";
}

function TargetResultSummary({ contrast }: { contrast: DifferentialExpressionContrast }) {
  const direction = contrastDirection(contrast);
  return <span className={`de-direction-badge is-${direction}`}>{direction === "mixed" ? "Mixed mapping" : directionLabel(direction)}</span>;
}

function TargetMetricTiles({ result }: { result: DifferentialExpressionContrast["target_results"][number] }) {
  return <span className="de-metric-tiles">
    <span><small>Mean expression</small><strong>{formatDeNumber(result.mean_expression)}</strong></span>
    <span><small>log2FC</small><strong>{formatDeNumber(result.log2fc)}</strong></span>
    <span><small>FDR</small><strong>{formatDeNumber(result.fdr, 5)}</strong></span>
  </span>;
}

function TargetResultDetails({ contrast }: { contrast: DifferentialExpressionContrast }) {
  const directions = new Set(contrast.target_results.map((result) => result.direction));
  return <details className={`de-target-results ${contrast.mapping_status === "multiple_gene_rows_same_symbol" ? "has-multiple" : ""}`}><summary>{contrast.target_result_total === 1 ? "Current protein mapping detail" : `${contrast.target_result_total} mapped Ensembl rows · ${directions.size > 1 ? "mixed results" : "same direction"}`}</summary><div>{contrast.target_results.map((result, index) => <dl key={`${result.ensembl_gene_id}-${index}`}><div><dt>Ensembl gene row</dt><dd>{result.ensembl_gene_id || `Gene row ${index + 1}`}</dd></div><div><dt>Statistics</dt><dd><TargetMetricTiles result={result} /></dd></div></dl>)}</div></details>;
}

function CurrentProteinStatistics({ contrast, compact = false }: { contrast: DifferentialExpressionContrast; compact?: boolean }) {
  const direction = contrastDirection(contrast);
  if (compact) return <span className={`de-current-protein-statistics is-${direction} is-compact`}>
    <span className="de-current-protein-statistics-heading"><span>Current protein</span><TargetResultSummary contrast={contrast} /></span>
    <span className="de-current-protein-statistics-rows">{contrast.target_results.map((result, index) => <span key={`${result.ensembl_gene_id}-${index}`} className="de-current-protein-statistics-row">
      <span className="de-current-protein-statistics-ensembl">{result.ensembl_gene_id || `Mapped gene row ${index + 1}`}</span>
      <TargetMetricTiles result={result} />
    </span>)}</span>
  </span>;
  return <div className={`de-current-protein-statistics is-${direction} ${compact ? "is-compact" : ""}`}>
    <div><span>Current protein</span><TargetResultSummary contrast={contrast} /></div>
    <dl>{contrast.target_results.map((result, index) => <div key={`${result.ensembl_gene_id}-${index}`}>
      <dt>{result.ensembl_gene_id || `Mapped gene row ${index + 1}`}</dt>
      <dd><TargetMetricTiles result={result} /></dd>
    </div>)}</dl>
  </div>;
}

function PointReadout({ point, pinned }: { point: VolcanoPoint | null; pinned: boolean }) {
  if (!point) return <div className="volcano-readout is-empty" aria-live="polite"><strong>Point details</strong><span>Hover, tap, or select a membrane-gene table row to inspect a gene.</span></div>;
  return <div className="volcano-readout" aria-live="polite">
    <div><strong>{geneName(point)}</strong><span>{pinned ? "Pinned selection" : "Point details"}</span></div>
    <dl>
      <div><dt>Mean expression</dt><dd>{formatDeNumber(point[POINT.meanExpression])}</dd></div>
      <div><dt>log2 fold change</dt><dd>{formatDeNumber(point[POINT.log2fc])}</dd></div>
      <div><dt>FDR</dt><dd>{formatDeNumber(point[POINT.rawFdr], 5)}</dd></div>
      <div><dt>Direction</dt><dd>{directionLabel(point[POINT.direction])}</dd></div>
      <div><dt>Membrane protein</dt><dd>{point[POINT.isMembrane] ? "Yes" : "No"}</dd></div>
      <div><dt>Ensembl gene ID</dt><dd>{point[POINT.ensemblGeneId] || "Not available"}</dd></div>
    </dl>
  </div>;
}

function CurrentProteinVolcanoReadout({ points }: { points: VolcanoPoint[] }) {
  const targetPoints = points.filter((point) => point[POINT.isTarget]);
  const directions = new Set(targetPoints.map((point) => point[POINT.direction]));
  const direction = directions.size > 1 ? "mixed" : targetPoints[0]?.[POINT.direction] ?? "not_significant";
  return <aside className={`volcano-current-protein is-${direction}`} aria-label="Current protein differential-expression readout">
    <div><strong>Current protein in this contrast</strong><span className={`de-direction-badge is-${direction}`}>{direction === "mixed" ? "Mixed mapping" : directionLabel(direction)}</span></div>
    {targetPoints.length === 0 ? <p>No finite target coordinates were returned for plotting. Missing values were not converted to zero.</p> : <dl>{targetPoints.map((point, index) => <div key={`${point[POINT.ensemblGeneId]}-${index}`}>
      <dt>{point[POINT.ensemblGeneId] || `Mapped gene row ${index + 1}`}</dt>
      <dd><TargetMetricTiles result={{ ensembl_gene_id: point[POINT.ensemblGeneId], mean_expression: point[POINT.meanExpression], log2fc: point[POINT.log2fc], fdr: point[POINT.rawFdr], direction: point[POINT.direction] }} /></dd>
    </div>)}</dl>}
  </aside>;
}

function MembraneGeneBrowser({ points, onSelect }: { points: VolcanoPoint[]; onSelect: (point: VolcanoPoint) => void }) {
  const [page, setPage] = useState(0);
  const membranePoints = useMemo(
    () => points.filter((point) => point[POINT.isMembrane]).sort((left, right) => Math.abs(right[POINT.log2fc]) - Math.abs(left[POINT.log2fc]) || geneName(left).localeCompare(geneName(right))),
    [points],
  );
  const pageCount = Math.max(1, Math.ceil(membranePoints.length / MEMBRANE_PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const visible = membranePoints.slice(safePage * MEMBRANE_PAGE_SIZE, (safePage + 1) * MEMBRANE_PAGE_SIZE);

  useEffect(() => setPage(0), [points]);

  return <details className="membrane-gene-browser">
    <summary>Browse plotted membrane genes ({membranePoints.length.toLocaleString()})</summary>
    {membranePoints.length === 0 ? <p className="empty-value">No membrane-mapped genes have finite coordinates in this contrast.</p> : <>
      <div className="table-scroll"><table>
        <caption className="sr-only">Membrane-mapped genes plotted in the active differential-expression contrast</caption>
        <thead><tr><th scope="col">Gene</th><th scope="col">Mean expression</th><th scope="col">log2 fold change</th><th scope="col">FDR</th><th scope="col">Direction</th></tr></thead>
        <tbody>{visible.map((point, index) => <tr key={`${point[POINT.ensemblGeneId]}-${safePage}-${index}`}>
          <th scope="row"><button type="button" onClick={() => onSelect(point)}>{geneName(point)}{point[POINT.isTarget] && <span>Current protein</span>}</button></th>
          <td>{formatDeNumber(point[POINT.meanExpression])}</td><td>{formatDeNumber(point[POINT.log2fc])}</td><td>{formatDeNumber(point[POINT.rawFdr], 5)}</td><td>{directionLabel(point[POINT.direction])}</td>
        </tr>)}</tbody>
      </table></div>
      <div className="pagination"><button className="quiet-button" type="button" disabled={safePage === 0} onClick={() => setPage((value) => Math.max(0, value - 1))}>Previous</button><span>Page {safePage + 1} of {pageCount}</span><button className="quiet-button" type="button" disabled={safePage + 1 >= pageCount} onClick={() => setPage((value) => Math.min(pageCount - 1, value + 1))}>Next</button></div>
    </>}
  </details>;
}

function VolcanoChart({ response }: { response: DifferentialExpressionVolcanoResponse }) {
  const chartElement = useRef<HTMLDivElement>(null);
  const chartRef = useRef<EChartsType | null>(null);
  const [readout, setReadout] = useState<VolcanoPoint | null>(() => response.points.find((point) => point[POINT.isTarget]) ?? null);
  const [pinned, setPinned] = useState(false);
  const pinnedRef = useRef(false);
  const [chartError, setChartError] = useState<string | null>(null);
  const [chartAttempt, setChartAttempt] = useState(0);

  const groups = useMemo(() => ({
    background: response.points.filter((point) => !point[POINT.isMembrane] && !point[POINT.isTarget]),
    membraneUp: response.points.filter((point) => point[POINT.isMembrane] && !point[POINT.isTarget] && point[POINT.direction] === "up"),
    membraneDown: response.points.filter((point) => point[POINT.isMembrane] && !point[POINT.isTarget] && point[POINT.direction] === "down"),
    membraneNeutral: response.points.filter((point) => point[POINT.isMembrane] && !point[POINT.isTarget] && point[POINT.direction] === "not_significant"),
    target: response.points.filter((point) => point[POINT.isTarget]),
  }), [response.points]);

  useEffect(() => {
    pinnedRef.current = pinned;
  }, [pinned]);

  useEffect(() => {
    setReadout(response.points.find((point) => point[POINT.isTarget]) ?? null);
    setPinned(false);
  }, [response]);

  useEffect(() => {
    const element = chartElement.current;
    if (!element || response.counts.plotted === 0) return;
    let cancelled = false;
    let resizeObserver: ResizeObserver | null = null;
    setChartError(null);

    void loadEcharts().then((echarts) => {
      if (cancelled || !chartElement.current) return;
      const chart = echarts.init(chartElement.current, undefined, { renderer: "canvas" });
      chartRef.current = chart;
      const thresholdY = -Math.log10(response.thresholds.fdr);
      const commonSeries = { type: "scatter" as const, encode: { x: POINT.log2fc, y: POINT.negLog10Fdr }, progressive: 4000, progressiveThreshold: 8000, progressiveChunkMode: "mod" as const, animation: false };
      chart.setOption({
        animation: false,
        aria: { enabled: true, description: `Volcano plot for ${response.gene_symbol} in ${response.contrast.disease_condition}, ${response.contrast.tissue}. ${response.counts.plotted} of ${response.counts.tested} tested genes have finite coordinates.` },
        grid: { top: 28, right: 24, bottom: 62, left: 72, containLabel: true },
        tooltip: {
          trigger: "item", renderMode: "richText", confine: true,
          formatter: (raw: unknown) => {
            const point = (raw as { data?: VolcanoPoint }).data;
            if (!point) return "Gene details unavailable";
            return `${geneName(point)}\nMean expression: ${formatDeNumber(point[POINT.meanExpression])}\nlog2 fold change: ${formatDeNumber(point[POINT.log2fc])}\nFDR: ${formatDeNumber(point[POINT.rawFdr], 5)}\nDirection: ${directionLabel(point[POINT.direction])}\nMembrane protein: ${point[POINT.isMembrane] ? "Yes" : "No"}\nEnsembl: ${point[POINT.ensemblGeneId] || "Not available"}`;
          },
        },
        xAxis: { type: "value", name: "log2 fold change (case vs control)", nameLocation: "middle", nameGap: 40, axisLine: { onZero: true }, splitLine: { lineStyle: { color: "#e2e8f0" } } },
        yAxis: { type: "value", name: "−log10(FDR)", nameLocation: "middle", nameGap: 52, min: 0, splitLine: { lineStyle: { color: "#e2e8f0" } } },
        series: [
          { ...commonSeries, name: "Other genes", data: groups.background, symbol: "circle", symbolSize: 4, itemStyle: { color: "#cbd5e1", opacity: .52 }, emphasis: { itemStyle: { color: "#64748b", opacity: 1 } }, markLine: { silent: true, symbol: "none", label: { color: "#475569", fontSize: 10 }, lineStyle: { color: "#94a3b8", type: "dashed" }, data: [{ xAxis: -response.thresholds.absolute_log2fc, name: `log2FC −${response.thresholds.absolute_log2fc}` }, { xAxis: response.thresholds.absolute_log2fc, name: `log2FC +${response.thresholds.absolute_log2fc}` }, { yAxis: thresholdY, name: `FDR ${response.thresholds.fdr}` }] } },
          { ...commonSeries, name: "Upregulated membrane proteins", data: groups.membraneUp, symbol: "diamond", symbolSize: 9, itemStyle: { color: "#f47254", borderColor: "#7f1d1d", borderWidth: 1.2, opacity: .9 } },
          { ...commonSeries, name: "Downregulated membrane proteins", data: groups.membraneDown, symbol: "diamond", symbolSize: 9, itemStyle: { color: "#7b95c6", borderColor: "#1e3a5f", borderWidth: 1.2, opacity: .9 } },
          { ...commonSeries, name: "Other membrane proteins", data: groups.membraneNeutral, symbol: "diamond", symbolSize: 8, itemStyle: { color: "rgba(255,255,255,.85)", borderColor: "#334155", borderWidth: 1.4 } },
          { ...commonSeries, name: "Current protein", data: groups.target, symbol: "star", symbolSize: 17, z: 10, itemStyle: { color: "#fded95", borderColor: "#0f172a", borderWidth: 2 } },
        ],
      });
      chart.on("mouseover", (raw: unknown) => {
        const point = (raw as { data?: VolcanoPoint }).data;
        if (point && !pinnedRef.current) setReadout(point);
      });
      chart.on("click", (raw: unknown) => {
        const point = (raw as { data?: VolcanoPoint }).data;
        if (!point) return;
        pinnedRef.current = true; setPinned(true); setReadout(point);
      });
      resizeObserver = new ResizeObserver(() => chart.resize());
      resizeObserver.observe(chartElement.current);
    }).catch((error: unknown) => {
      if (!cancelled) setChartError(error instanceof Error ? error.message : "Unable to initialize the volcano plot.");
    });

    return () => {
      cancelled = true;
      resizeObserver?.disconnect();
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, [chartAttempt, groups, response]);

  function selectFromTable(point: VolcanoPoint) {
    pinnedRef.current = true; setPinned(true); setReadout(point);
    const index = response.points.indexOf(point);
    if (index >= 0) chartRef.current?.dispatchAction({ type: "showTip", seriesIndex: point[POINT.isTarget] ? 4 : point[POINT.direction] === "up" ? 1 : point[POINT.direction] === "down" ? 2 : 3, dataIndex: point[POINT.isTarget] ? groups.target.indexOf(point) : point[POINT.direction] === "up" ? groups.membraneUp.indexOf(point) : point[POINT.direction] === "down" ? groups.membraneDown.indexOf(point) : groups.membraneNeutral.indexOf(point) });
  }

  function clearPinned() {
    pinnedRef.current = false; setPinned(false);
    setReadout(response.points.find((point) => point[POINT.isTarget]) ?? null);
    chartRef.current?.dispatchAction({ type: "hideTip" });
  }

  if (response.counts.plotted === 0) return <StatusMessage title="No genes can be plotted">This contrast tested {response.counts.tested.toLocaleString()} genes, but none have finite log2 fold-change and FDR coordinates. Missing statistics were not converted to zero.</StatusMessage>;

  return <div className="volcano-region" onKeyDown={(event) => { if (event.key === "Escape" && pinned) { event.stopPropagation(); clearPinned(); } }}>
    <div className="volcano-summary"><strong>{response.contrast.disease_condition} · {response.contrast.tissue}</strong><span>{response.contrast.case_definition} (n={response.contrast.case_n}) vs {response.contrast.control_definition} (n={response.contrast.control_n})</span><small>{response.counts.plotted.toLocaleString()} plotted of {response.counts.tested.toLocaleString()} tested genes · {response.counts.unplottable.toLocaleString()} without finite coordinates</small></div>
    <div className="volcano-legend" aria-label="Volcano plot legend"><span><i className="legend-other" />Other genes</span><span><i className="legend-up" />Upregulated membrane protein</span><span><i className="legend-down" />Downregulated membrane protein</span><span><i className="legend-neutral" />Other membrane protein</span><span><i className="legend-target" />Current protein</span></div>
    <CurrentProteinVolcanoReadout points={response.points} />
    {chartError ? <div className="volcano-chart-error" role="alert"><strong>Volcano plot unavailable</strong><span>{chartError}</span><button className="quiet-button" type="button" onClick={() => setChartAttempt((value) => value + 1)}><RotateCcw aria-hidden="true" size={16} strokeWidth={1.9} />Retry chart</button></div> : <div ref={chartElement} className="volcano-chart" role="img" tabIndex={0} aria-label={`Volcano plot: ${response.counts.plotted.toLocaleString()} genes with log2 fold change on the horizontal axis and negative log10 FDR on the vertical axis`} />}
    <PointReadout point={readout} pinned={pinned} />
    {pinned && <button className="quiet-button volcano-clear-pin" type="button" onClick={clearPinned}>Clear pinned gene <span className="keyboard-hint">Esc</span></button>}
    <MembraneGeneBrowser points={response.points} onSelect={selectFromTable} />
  </div>;
}

function DatasetCard({ dataset, open, activeContrast, onToggle, onSelect }: { dataset: DifferentialExpressionDataset; open: boolean; activeContrast: string | null; onToggle: () => void; onSelect: (contrast: DifferentialExpressionContrast) => void }) {
  const panelId = `de-dataset-${dataset.dataset_id}`;
  const featuredContrast = dataset.contrasts[0];
  return <article className={`de-dataset-card ${open ? "is-open" : ""}`}>
    <button className="de-dataset-trigger" type="button" aria-expanded={open} aria-controls={panelId} onClick={onToggle}>
      <span className="de-dataset-trigger-heading"><span className="de-dataset-identity"><strong>{dataset.dataset_id}</strong><span>{dataset.dataset_name}</span></span><ChevronRight className="de-chevron" aria-hidden="true" size={24} strokeWidth={2} /></span>
      <span className="de-dataset-context">
        <span className="de-dataset-context-field"><b>Tissues</b><span>{dataset.tissues.length ? dataset.tissues.map(formatTermLabel).join(", ") : "Not reported"}</span></span>
        <span className="de-dataset-context-field is-disease"><b>Diseases</b><span>{dataset.disease_conditions.length ? dataset.disease_conditions.map(formatTermLabel).join(", ") : "Not reported"}</span></span>
        <span className="de-dataset-count"><b>Qualifying contrasts</b><span><strong>{dataset.qualifying_contrast_total}</strong> source-defined {dataset.qualifying_contrast_total === 1 ? "contrast" : "contrasts"}</span></span>
      </span>
      {featuredContrast && <span className="de-dataset-featured"><span className="de-featured-contrast"><b>First displayed qualifying contrast</b><span>{formatTermLabel(featuredContrast.disease_condition)} · {formatTermLabel(featuredContrast.tissue)}</span><small>Display order only; not disease importance. {featuredContrast.case_definition} (n={featuredContrast.case_n}) vs {featuredContrast.control_definition} (n={featuredContrast.control_n})</small></span><CurrentProteinStatistics contrast={featuredContrast} compact /></span>}
    </button>
    {open && <div id={panelId} className="de-dataset-body">
      <SourceContext source="GEN" recordGrain="Source-defined qualifying disease-versus-control contrasts" href={dataset.source_page} linkLabel="Open GEN dataset record" caveat="Only source-defined qualifying contrasts are listed; absence does not establish untested, undetected, or non-significant status." />
      <details className="de-study-metadata"><summary>Study metadata</summary><dl className="de-study-facts"><div><dt>Project</dt><dd>{[dataset.project_id, dataset.bioproject_id].filter(Boolean).join(" · ") || "Not reported"}</dd></div><div><dt>Strategy</dt><dd>{dataset.strategy || "Not reported"}</dd></div><div><dt>Dataset samples</dt><dd>{dataset.sample_count_metadata === null ? "Not reported" : `${dataset.sample_count_metadata.toLocaleString()} metadata`}{dataset.matrix_sample_count === null ? "" : ` · ${dataset.matrix_sample_count.toLocaleString()} matrix`}{dataset.sample_count_reported === null ? "" : ` · ${dataset.sample_count_reported.toLocaleString()} reported`}</dd></div><div><dt>Sample mapping</dt><dd>{dataset.sample_join_valid ? "Validated" : "Not validated"}</dd></div></dl></details>
      <h4 className="de-contrast-heading">Choose a contrast <span>Volcano data loads only after selection</span></h4>
      <div className="de-contrast-list" role="group" aria-label={`${dataset.dataset_id} qualifying differential-expression contrasts`}>{dataset.contrasts.map((contrast) => <article key={contrast.contrast_id} className={activeContrast === contrast.contrast_id ? "is-active" : ""}><button type="button" aria-pressed={activeContrast === contrast.contrast_id} onClick={() => onSelect(contrast)}><span><strong>{formatTermLabel(contrast.disease_condition)}</strong><small>{formatTermLabel(contrast.tissue)} · {contrast.case_n} case / {contrast.control_n} control{contrast.paired ? " · paired" : ""}</small></span><CurrentProteinStatistics contrast={contrast} compact /></button><TargetResultDetails contrast={contrast} /></article>)}</div>
    </div>}
  </article>;
}

export function DifferentialExpression({ accession }: { accession: string }) {
  const [summaryAttempt, setSummaryAttempt] = useState(0);
  const [summaryState, setSummaryState] = useState<{ kind: "loading" | "error" | "ready"; response?: DifferentialExpressionSummaryResponse; error?: string }>({ kind: "loading" });
  const [expandedDataset, setExpandedDataset] = useState<string | null>(null);
  const [activeContrast, setActiveContrast] = useState<string | null>(null);
  const [volcanoState, setVolcanoState] = useState<{ kind: "idle" | "loading" | "error" | "ready"; response?: DifferentialExpressionVolcanoResponse; error?: string }>({ kind: "idle" });
  const [volcanoAttempt, setVolcanoAttempt] = useState(0);
  const cache = useRef(new Map<string, DifferentialExpressionVolcanoResponse>());
  const selectedRef = useRef<{ dataset: DifferentialExpressionDataset; contrast: DifferentialExpressionContrast } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setSummaryState({ kind: "loading" }); setExpandedDataset(null); setActiveContrast(null); setVolcanoState({ kind: "idle" }); cache.current.clear(); selectedRef.current = null;
    getJson<DifferentialExpressionSummaryResponse>(`/proteins/${encodeURIComponent(accession)}/differential-expression/summary`, controller.signal)
      .then((response) => setSummaryState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setSummaryState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load differential-expression study metadata." });
      });
    return () => controller.abort();
  }, [accession, summaryAttempt]);

  useEffect(() => {
    const selected = selectedRef.current;
    if (!activeContrast || !selected || selected.contrast.contrast_id !== activeContrast) return;
    const cached = cache.current.get(activeContrast);
    if (cached) { setVolcanoState({ kind: "ready", response: cached }); return; }
    const controller = new AbortController();
    setVolcanoState({ kind: "loading" });
    void loadEcharts().catch(() => undefined);
    getJson<DifferentialExpressionVolcanoResponse>(`/differential-expression/contrasts/${encodeURIComponent(activeContrast)}/volcano?accession=${encodeURIComponent(accession)}`, controller.signal)
      .then(validateVolcanoResponse)
      .then((response) => { cache.current.set(activeContrast, response); setVolcanoState({ kind: "ready", response }); })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setVolcanoState({ kind: "error", error: error instanceof Error ? error.message : "Unable to load this contrast's volcano points." });
      });
    return () => controller.abort();
  }, [accession, activeContrast, volcanoAttempt]);

  function selectContrast(dataset: DifferentialExpressionDataset, contrast: DifferentialExpressionContrast) {
    selectedRef.current = { dataset, contrast };
    setActiveContrast(contrast.contrast_id); setVolcanoAttempt(0);
    const cached = cache.current.get(contrast.contrast_id);
    setVolcanoState(cached ? { kind: "ready", response: cached } : { kind: "loading" });
  }

  const summary = summaryState.response;
  const orderedDatasets = useMemo(() => summary ? sortDifferentialExpressionDatasets(summary.datasets) : [], [summary]);
  const orderedContrasts = useMemo(() => orderedDatasets.flatMap((dataset) => dataset.contrasts), [orderedDatasets]);
  const summaryCounts = useMemo(() => differentialExpressionCounts(orderedContrasts), [orderedContrasts]);
  const firstContrast = orderedContrasts[0];

  useEffect(() => {
    if (summaryState.kind === "ready") setExpandedDataset(orderedDatasets[0]?.dataset_id ?? null);
  }, [orderedDatasets, summaryState.kind]);

  return <section className="differential-expression" aria-labelledby="differential-expression-heading" onKeyDown={(event) => {
    if (event.key !== "Escape") return;
    if (activeContrast) { setActiveContrast(null); setVolcanoState({ kind: "idle" }); selectedRef.current = null; }
    else if (expandedDataset) setExpandedDataset(null);
  }}>
    <div className="de-heading"><div><p className="eyebrow">GEN studies</p><h3 id="differential-expression-heading">Disease differential expression</h3><p>Source-defined qualifying contrasts for the current protein. Select a contrast only when you need its volcano plot.</p></div>{summary && <span><b>{summary.dataset_total}</b> datasets <i aria-hidden="true">·</i> <b>{summary.contrast_total}</b> qualifying contrasts</span>}</div>
    {summaryState.kind === "loading" && <StatusMessage title="Loading differential-expression studies">Retrieving protein-mapped dataset and contrast metadata. Volcano points are not being loaded.</StatusMessage>}
    {summaryState.kind === "error" && <div className="de-retry-state"><StatusMessage title="Differential-expression studies unavailable" tone="error">{summaryState.error}</StatusMessage><button className="quiet-button" type="button" onClick={() => setSummaryAttempt((value) => value + 1)}><RotateCcw aria-hidden="true" size={16} strokeWidth={1.9} />Retry study metadata</button></div>}
    {summaryState.kind === "ready" && summary && (orderedDatasets.length === 0 ? <StatusMessage title="No source-defined qualifying contrast">No GEN disease-versus-control contrast was returned for {summary.gene_symbol} under the source-defined FDR &lt; {summary.mapping.fdr_threshold} and |log2 fold change| ≥ {summary.mapping.absolute_log2fc_threshold} membership rule. Because this summary contains qualifying contrasts only, absence here does not establish that the protein was tested, untested, undetected, or non-significant in another study.</StatusMessage> : <>
      <div className="de-protein-summary" aria-label="Current protein qualifying contrast summary"><div><p className="eyebrow">Current protein takeaway</p><h4>{summary.gene_symbol} is upregulated in {summaryCounts.up}, downregulated in {summaryCounts.down}, and has mixed Ensembl-row directions in {summaryCounts.mixed} of {summaryCounts.total} source-defined qualifying contrasts.</h4><p>Mixed mapping keeps separate Ensembl rows and does not combine their effects.</p></div>{firstContrast && <div className="de-first-contrast"><span>First displayed qualifying contrast <small>Display order only; not disease importance.</small></span><strong>{formatTermLabel(firstContrast.disease_condition)} · {formatTermLabel(firstContrast.tissue)}</strong><small>{firstContrast.case_definition} (n={firstContrast.case_n}) vs {firstContrast.control_definition} (n={firstContrast.control_n})</small><CurrentProteinStatistics contrast={firstContrast} /></div>}<p className="de-qualifying-scope">Only source-defined qualifying contrasts are listed. A contrast not shown here must not be interpreted as untested, undetected, or non-significant.</p></div>
      <details className="de-method-notes"><summary>Mapping, membership, and display order</summary><p>Exact gene-symbol mapping · source-defined membership · FDR &lt; {summary.mapping.fdr_threshold} · |log2FC| ≥ {summary.mapping.absolute_log2fc_threshold}. Multi-Ensembl matches remain separate. {DE_SORT_RULE}</p></details>
      <div className="de-dataset-list">{orderedDatasets.map((dataset) => <DatasetCard key={dataset.dataset_id} dataset={dataset} open={expandedDataset === dataset.dataset_id} activeContrast={activeContrast} onToggle={() => { const closing = expandedDataset === dataset.dataset_id; setExpandedDataset(closing ? null : dataset.dataset_id); setActiveContrast(null); setVolcanoState({ kind: "idle" }); selectedRef.current = null; }} onSelect={(contrast) => selectContrast(dataset, contrast)} />)}</div>
      {activeContrast && <div className="de-volcano-shell" id={`de-volcano-${activeContrast}`}>
        {volcanoState.kind === "loading" && <StatusMessage title="Loading complete volcano plot">Retrieving all genes with finite differential-expression coordinates for this contrast.</StatusMessage>}
        {volcanoState.kind === "error" && <div className="de-retry-state"><StatusMessage title="Volcano plot unavailable" tone="error">{volcanoState.error}</StatusMessage><button className="quiet-button" type="button" onClick={() => setVolcanoAttempt((value) => value + 1)}><RotateCcw aria-hidden="true" size={16} strokeWidth={1.9} />Retry this contrast</button></div>}
        {volcanoState.kind === "ready" && volcanoState.response && <VolcanoChart response={volcanoState.response} />}
      </div>}
    </>)}
  </section>;
}
