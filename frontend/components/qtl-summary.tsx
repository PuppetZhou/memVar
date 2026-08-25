"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type { EChartsType } from "echarts";
import { QtlSource, QtlSummaryItem, QtlSummaryResponse } from "../lib/api";
import { useJsonResource } from "../lib/use-json-resource";
import { StatusMessage } from "./status-message";
import { formatTermLabel } from "../lib/display-labels";
import styles from "./qtl-heatmap.module.css";

const SOURCES: QtlSource[] = ["GTEx", "eQTLGen", "QTLbase"];
const GTEX_TYPES = ["apaQTL", "eQTL", "sQTL"] as const;

type GtexHeatmapDatum = {
  value: [number, number, number];
  tissue: string;
  qtlType: string;
  recordCount: number;
  distinctCount: number;
  href: string | null;
};

function cellHref(accession: string, item: QtlSummaryItem) {
  const params = new URLSearchParams({ source: item.source_database, type: item.qtl_type });
  if (item.tissue_or_context) {
    params.set(item.source_database === "eQTLGen" ? "context" : "tissue", item.tissue_or_context);
  }
  if (item.population) params.set("population", item.population);
  return `/protein/${encodeURIComponent(accession)}/qtl?${params}`;
}

function semanticsLabel(source: QtlSource) {
  if (source === "GTEx") return "official significant pairs";
  if (source === "QTLbase") return "associations";
  return "blood meta-analysis";
}

function GtexHeatmap({ accession, items }: { accession: string; items: QtlSummaryItem[] }) {
  const chartElement = useRef<HTMLDivElement>(null);
  const tissues = useMemo(
    () => Array.from(new Set(items.map((item) => item.tissue_or_context).filter((value): value is string => Boolean(value)))).sort((a, b) => a.localeCompare(b)),
    [items],
  );
  const itemByCell = useMemo(
    () => new Map(items.filter((item) => item.tissue_or_context).map((item) => [`${item.tissue_or_context}\u001f${item.qtl_type}`, item])),
    [items],
  );
  const data = useMemo<GtexHeatmapDatum[]>(() => tissues.flatMap((tissue, tissueIndex) => GTEX_TYPES.map((qtlType, typeIndex) => {
    const item = itemByCell.get(`${tissue}\u001f${qtlType}`);
    const recordCount = item?.record_count ?? 0;
    return {
      value: [typeIndex, tissueIndex, Math.log10(recordCount + 1)],
      tissue,
      qtlType,
      recordCount,
      distinctCount: item?.distinct_variant_or_locus_count ?? 0,
      href: item ? cellHref(accession, item) : null,
    };
  })), [accession, itemByCell, tissues]);
  const maximum = Math.max(1, ...data.map((item) => item.value[2]));
  const chartHeight = Math.max(360, tissues.length * 27 + 120);

  useEffect(() => {
    const element = chartElement.current;
    if (!element || tissues.length === 0) return;
    let chart: EChartsType | null = null;
    let cancelled = false;
    const resize = () => chart?.resize();

    void import("echarts").then((echarts) => {
      if (cancelled || !chartElement.current) return;
      chart = echarts.init(chartElement.current, undefined, { renderer: "canvas" });
      chart.setOption({
        animation: false,
        aria: {
          enabled: true,
          description: `GTEx tissue heatmap for ${accession}. Columns are apaQTL, eQTL, and sQTL; color encodes log10 of the exact record count plus one.`,
        },
        grid: { top: 45, right: 100, bottom: 30, left: 245 },
        tooltip: {
          trigger: "item",
          renderMode: "richText",
          formatter: (raw: unknown) => {
            const datum = (raw as { data?: GtexHeatmapDatum }).data;
            if (!datum) return "GTEx record count unavailable";
            return `${formatTermLabel(datum.tissue)}\n${formatTermLabel(datum.qtlType)}\n${datum.recordCount.toLocaleString()} official significant pairs\n${datum.distinctCount.toLocaleString()} distinct variants`;
          },
        },
        xAxis: {
          type: "category",
          data: GTEX_TYPES.map(formatTermLabel),
          position: "top",
          splitArea: { show: true },
          axisTick: { show: false },
        },
        yAxis: {
          type: "category",
          data: tissues.map(formatTermLabel),
          inverse: true,
          axisTick: { show: false },
          axisLabel: { width: 225, overflow: "truncate" },
        },
        visualMap: {
          min: 0,
          max: maximum,
          dimension: 2,
          orient: "vertical",
          right: 8,
          top: 50,
          text: ["Higher", "0"],
          calculable: false,
          inRange: { color: ["#fff8ef", "#ffc1a6", "#f59c7c", "#c85e62"] },
        },
        series: [{
          name: "GTEx official significant pairs",
          type: "heatmap",
          data,
          label: {
            show: true,
            formatter: (raw: unknown) => {
              const datum = (raw as { data?: GtexHeatmapDatum }).data;
              return datum ? datum.recordCount.toLocaleString() : "0";
            },
          },
          itemStyle: { borderColor: "#fffdf8", borderWidth: 2 },
          emphasis: { itemStyle: { borderColor: "#4d1742", borderWidth: 2 } },
        }],
      });
      chart.on("click", (raw: unknown) => {
        const datum = (raw as { data?: GtexHeatmapDatum }).data;
        if (datum?.href) window.location.assign(datum.href);
      });
      window.addEventListener("resize", resize);
    });

    return () => {
      cancelled = true;
      window.removeEventListener("resize", resize);
      chart?.dispose();
    };
  }, [accession, data, maximum, tissues]);

  if (tissues.length === 0) {
    return <StatusMessage title="No GTEx QTL records">No protein-mapped GTEx official significant pairs are present in the current website data release.</StatusMessage>;
  }

  return <div className={styles.heatmapRegion}>
    <div className="qtl-legend"><strong>Cell fill</strong><span className="legend-gradient legend-qtl" aria-hidden="true" /><span>log10(count + 1); labels and tooltips show exact official significant-pair counts</span></div>
    <div className={styles.chartScroller}>
      <div ref={chartElement} className={styles.chart} style={{ height: chartHeight }} role="img" aria-label={`GTEx heatmap with ${tissues.length} tissue rows and three QTL type columns`} />
    </div>
    <details className={styles.tableDisclosure}>
      <summary>View keyboard-accessible GTEx count table</summary>
      <div className={styles.tableScroller}>
        <table className={styles.table}>
          <caption className="sr-only">GTEx official significant-pair counts by tissue and QTL type</caption>
          <thead><tr><th scope="col">Tissue</th>{GTEX_TYPES.map((type) => <th scope="col" key={type}>{formatTermLabel(type)}</th>)}</tr></thead>
          <tbody>{tissues.map((tissue) => <tr key={tissue}>
            <th scope="row">{formatTermLabel(tissue)}</th>
            {GTEX_TYPES.map((type) => {
              const item = itemByCell.get(`${tissue}\u001f${type}`);
              return <td key={type}>{item ? <Link href={cellHref(accession, item)} aria-label={`${formatTermLabel(tissue)} ${formatTermLabel(type)}: ${item.record_count.toLocaleString()} records; open filtered details`}>{item.record_count.toLocaleString()} <span>({item.distinct_variant_or_locus_count.toLocaleString()} distinct)</span></Link> : <span className={styles.zero}>0 · No records</span>}</td>;
            })}
          </tr>)}</tbody>
        </table>
      </div>
    </details>
  </div>;
}

export function QtlSummary({ accession }: { accession: string }) {
  const [activeSource, setActiveSource] = useState<QtlSource>("GTEx");
  const [activeType, setActiveType] = useState("");
  const state = useJsonResource<QtlSummaryResponse>(
    `/proteins/${encodeURIComponent(accession)}/qtl/summary`,
    "Unable to load QTL summary.",
  );

  const response = state.kind === "ready" ? state.response : undefined;
  const sourceItems = useMemo(() => response?.items.filter((item) => item.source_database === activeSource) ?? [], [response, activeSource]);
  const types = useMemo(() => Array.from(new Set(sourceItems.map((item) => item.qtl_type))), [sourceItems]);
  const selectedType = types.includes(activeType) ? activeType : types[0] ?? "";
  const cells = sourceItems.filter((item) => item.qtl_type === selectedType);
  const maxLog = Math.max(1, ...cells.map((item) => Math.log10(item.record_count + 1)));
  const metadata = response?.source_semantics.find((item) => item.source_database === activeSource);

  return <section id="qtl" className="overview-section" aria-labelledby="qtl-heading">
    <div className="section-heading"><p className="eyebrow">M3 molecular QTL evidence</p><h2 id="qtl-heading">QTL summary</h2></div>
    <p className="section-intro">Counts are source records, split by QTL type and source tissue or context. Select a cell to open the bounded, server-paginated detail table with these filters preserved.</p>
    <div className="evidence-panel qtl-summary-panel">
      <div className="source-tabs" role="group" aria-label="QTL source">
        {SOURCES.map((source) => <button key={source} type="button" aria-pressed={activeSource === source} onClick={() => { setActiveSource(source); setActiveType(""); }}>{source}<span>{semanticsLabel(source)}</span></button>)}
      </div>
      <div className="evidence-body" tabIndex={0}>
        {state.kind === "loading" && <p className="inline-loading" role="status">Loading protein-mapped QTL counts…</p>}
        {state.kind === "error" && <p className="inline-error" role="alert">{state.error}</p>}
        {response && <>
          <div className="semantics-banner"><strong>{activeSource}</strong><span>{activeSource === "eQTLGen" ? "blood meta-analysis / GRCh37" : `${metadata?.evidence_semantics ?? semanticsLabel(activeSource)} / ${metadata?.genome_build ?? "build unavailable"}`}</span></div>
          {activeSource === "GTEx" ? <GtexHeatmap accession={accession} items={sourceItems} /> : <>
          {types.length > 0 && <div className="type-tabs" role="group" aria-label={`${activeSource} QTL type`}>{types.map((type) => <button key={type} type="button" aria-pressed={selectedType === type} onClick={() => setActiveType(type)}>{formatTermLabel(type)}</button>)}</div>}
          {cells.length === 0 ? <StatusMessage title={`No ${activeSource} QTL records`}>No protein-mapped records for this source are present in the current website data release.</StatusMessage> : <>
            <div className="qtl-legend"><strong>Cell fill</strong><span className="legend-gradient legend-qtl" aria-hidden="true" /><span>log10(count + 1); labels show raw {activeSource === "QTLbase" ? "associations" : "record counts"}</span></div>
            <div className="qtl-cell-grid" role="list" aria-label={`${activeSource} ${selectedType} summary`}>
              {cells.map((item, index) => {
                const intensity = Math.log10(item.record_count + 1) / maxLog;
                const context = item.tissue_or_context ?? (activeSource === "eQTLGen" ? "blood meta-analysis" : "Context unavailable");
                const grain = activeSource === "QTLbase" ? "associations" : "records";
                const description = `${context}${item.population ? `, ${item.population}` : ""}: ${item.record_count.toLocaleString()} ${grain}; ${item.distinct_variant_or_locus_count.toLocaleString()} distinct variant or locus records`;
                return <Link key={`${context}-${item.population}-${index}`} href={cellHref(accession, item)} className="qtl-cell" role="listitem" style={{ "--cell-intensity": intensity } as React.CSSProperties} title={description} aria-label={`${description}. Open filtered details.`}>
                  <span>{context}</span>{item.population && <small>{item.population}</small>}<strong>{item.record_count.toLocaleString()}</strong><em>{grain}</em>
                </Link>;
              })}
            </div>
          </>}
          </>}
        </>}
      </div>
    </div>
  </section>;
}
