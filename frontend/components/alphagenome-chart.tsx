"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import type { EChartsType } from "echarts";
import type { AlphaGenomeContactMapResponse, AlphaGenomeSignalResponse } from "../lib/api";
import { signalRowDescriptor } from "../lib/alphagenome-view";

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

function compact(value: number) {
  if (value !== 0 && Math.abs(value) < .001) return value.toExponential(2);
  return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

const COMPARISON_COLORS = ["#7b95c6", "#49c2d9", "#67a583", "#f59c7c", "#c85e62"];
const MODALITY_LABELS: Record<string, string> = {
  rna_seq: "RNA-seq", cage: "CAGE", procap: "PRO-cap", atac: "ATAC-seq",
  chip_histone: "Histone ChIP", splice_sites: "Splice sites", splice_site_usage: "Splice usage",
};

function comparisonLabel(response: AlphaGenomeSignalResponse) {
  const track = response.track;
  const biosample = track.biosample_name || track.gtex_tissue || track.ontology_curie || "Unspecified biosample";
  const detail = track.histone_mark || (track.strand && track.strand !== "." ? `${track.strand} strand` : null);
  return `${biosample}${detail ? ` · ${detail}` : ""}`;
}

export function AlphaGenomeSignalChart({ responses, axisStart, axisEnd, trackColors }: { responses: AlphaGenomeSignalResponse[]; axisStart: number; axisEnd: number; trackColors: Record<string, string> }) {
  const element = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const datasets = useMemo(() => responses.map((response, responseIndex) => {
    const width = response.window_end_0based - response.window_start_0based;
    const points = response.values.map(([mean, maximum], offset) => {
      const index = response.returned_bin_start + offset;
      const coordinate = response.window_start_0based + ((index + .5) * width / response.level_bins);
      return [coordinate, mean, maximum] as [number, number, number];
    });
    return { response, points, label: comparisonLabel(response), modality: response.track.modality, color: trackColors[response.track.track_id] ?? COMPARISON_COLORS[responseIndex % COMPARISON_COLORS.length], descriptor: signalRowDescriptor(response.track) };
  }), [responses, trackColors]);
  const primary = responses[0];
  // Each selected signal gets its own row and y-axis. Shared x coordinates are
  // useful for comparison; shared y domains would incorrectly imply comparable
  // magnitude across assays, biosamples, or display units.
  const groups = useMemo(() => datasets.map((dataset) => ({ modality: dataset.modality, items: [dataset] })), [datasets]);

  useEffect(() => {
    if (!element.current) return;
    let chart: EChartsType | null = null;
    let cancelled = false;
    const resize = () => chart?.resize();
    setError(null);
    void loadEcharts().then((echarts) => {
      if (cancelled || !element.current) return;
      chart = echarts.init(element.current, undefined, { renderer: "canvas" });
      const grids = groups.map((_, index) => ({ left: 118, right: 24, top: 24 + index * 188, height: 132, containLabel: false }));
      const xAxes = groups.map((_, index) => ({
        type: "value" as const, gridIndex: index, min: axisStart, max: axisEnd,
        name: index === groups.length - 1 ? `${primary.genome_build} gene position` : "",
        nameLocation: "middle" as const, nameGap: 38,
        axisLabel: { show: index === groups.length - 1, formatter: (value: number) => Math.round(value).toLocaleString() },
        axisTick: { show: index === groups.length - 1 },
        axisLine: { lineStyle: { color: "#94a3b8" } }, splitLine: { show: false },
      }));
      const yAxes = groups.map((group, index) => ({
        type: "value" as const, gridIndex: index, min: 0,
        name: `${MODALITY_LABELS[group.modality] ?? group.modality}\n${group.items[0].response.track.display_unit}`,
        nameLocation: "middle" as const, nameGap: 72, nameTextStyle: { color: "#475569", fontSize: 10, lineHeight: 14 },
        axisLabel: { color: "#64748b", fontSize: 10 }, splitLine: { lineStyle: { color: "#e2e8f0" } },
      }));
      const series = groups.flatMap((group, groupIndex) => group.items.flatMap((dataset, itemIndex) => {
        const color = dataset.color;
        const meanSeries = {
          name: dataset.label, type: "line" as const, xAxisIndex: groupIndex, yAxisIndex: groupIndex,
          data: dataset.points.map((point) => [point[0], point[1], point[1], point[2], dataset.response.track.display_unit]),
          showSymbol: false, lineStyle: { color, width: group.items.length === 1 ? 2.1 : 1.7 }, itemStyle: { color },
          emphasis: { focus: "series" as const },
        };
        if (group.items.length !== 1) return [meanSeries];
        return [{
          name: `${dataset.label} maximum`, type: "line" as const, xAxisIndex: groupIndex, yAxisIndex: groupIndex,
          data: dataset.points.map((point) => [point[0], point[2], point[1], point[2], dataset.response.track.display_unit]),
          showSymbol: false, silent: true, lineStyle: { color, width: 1, opacity: .45 },
          areaStyle: { color, opacity: .1 }, emphasis: { disabled: true },
        }, meanSeries];
      }));
      chart.setOption({
        animation: false,
        color: COMPARISON_COLORS,
        aria: { enabled: true, description: `AlphaGenome reference-sequence multimodal comparison for ${primary.ensembl_gene_id}, showing ${responses.length} selected tracks in ${groups.length} vertically aligned modalities.` },
        grid: grids, xAxis: xAxes, yAxis: yAxes,
        tooltip: {
          trigger: "axis", confine: true, renderMode: "richText",
          formatter: (raw: unknown) => {
            const entries = (raw as { seriesName?: string; data?: [number, number, number, number, string] }[]).filter((item) => item.data && !item.seriesName?.endsWith(" maximum"));
            const point = entries[0]?.data;
            if (!point) return "Prediction value unavailable";
            const values = entries.map((item) => `${item.seriesName ?? "Track"}\n  Mean: ${compact(item.data![2])} · max ${compact(item.data![3])} ${item.data![4]}`).join("\n");
            return `GRCh38 position ${Math.round(point[0]).toLocaleString()}\n${values}`;
          },
        },
        dataZoom: [
          { type: "inside", xAxisIndex: groups.map((_, index) => index), filterMode: "none" },
          { type: "slider", xAxisIndex: groups.map((_, index) => index), height: 18, bottom: 8, filterMode: "none" },
        ],
        series,
      });
      window.addEventListener("resize", resize);
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to initialize the prediction chart."));
    return () => { cancelled = true; window.removeEventListener("resize", resize); chart?.dispose(); };
  }, [axisEnd, axisStart, datasets, groups, primary.genome_build, primary.ensembl_gene_id, responses.length, trackColors]);

  if (error) return <div className="alphagenome-chart-error" role="alert"><strong>Prediction chart unavailable</strong><span>{error}</span></div>;
  const samples = datasets.flatMap((dataset) => {
    const sampleStep = Math.max(1, Math.floor(dataset.points.length / 8));
    return dataset.points.filter((_, index) => index % sampleStep === 0).slice(0, 8).map((point) => ({ label: dataset.label, point }));
  });
  return <div className="alphagenome-figure alphagenome-multimodal-figure">
    <div className="alphagenome-figure-heading"><div><strong>Reference-sequence signal comparison</strong><span>All selected tracks share genomic coordinates; every row retains its own y-axis and source unit.</span></div><span>{responses.length} selected track{responses.length === 1 ? "" : "s"}</span></div>
    <ol className="alphagenome-signal-row-keys" aria-label="Signal row keys">{datasets.map((dataset, index) => <li key={dataset.response.track.track_id}><i style={{ background: dataset.color }} /><span><b>Row {index + 1} · {dataset.descriptor.modality}</b><strong>{dataset.descriptor.biosample} · {dataset.descriptor.track}</strong><small>{dataset.descriptor.unit} · independent y-scale</small></span></li>)}</ol>
    <div ref={element} className="alphagenome-signal-chart" style={{ height: `${groups.length * 188 + 86}px` }} role="img" aria-label={`Multimodal prediction comparison with ${responses.length} tracks across ${groups.length} aligned rows`} />
    <details className="alphagenome-data-alternative"><summary><ChevronRight aria-hidden="true" size={16} strokeWidth={2} />View representative prediction bins</summary><div className="table-scroll"><table><thead><tr><th>Modality</th><th>Biosample / track</th><th>GRCh38 position</th><th>Mean</th><th>Maximum</th></tr></thead><tbody>{samples.map(({ label, point }, index) => { const modality = datasets.find((dataset) => dataset.label === label)?.modality ?? ""; return <tr key={`${label}-${point[0]}-${index}`}><td>{MODALITY_LABELS[modality] ?? modality}</td><td>{label}</td><td>{Math.round(point[0]).toLocaleString()}</td><td>{compact(point[1])}</td><td>{compact(point[2])}</td></tr>; })}</tbody></table></div></details>
  </div>;
}

export function AlphaGenomeContactChart({ response, colorDomain }: { response: AlphaGenomeContactMapResponse; colorDomain?: [number, number] }) {
  const element = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const localDomain = useMemo(() => [Math.min(0, ...response.values), Math.max(0, ...response.values)] as [number, number], [response.values]);
  const domain = colorDomain ?? localDomain;

  useEffect(() => {
    if (!element.current) return;
    let chart: EChartsType | null = null;
    let cancelled = false;
    const resize = () => chart?.resize();
    setError(null);
    void loadEcharts().then((echarts) => {
      if (cancelled || !element.current) return;
      chart = echarts.init(element.current, undefined, { renderer: "canvas" });
      const data: [number, number, number][] = [];
      for (let row = 0; row < response.matrix_size; row += 1) for (let column = 0; column < response.matrix_size; column += 1) data.push([column, row, response.values[row * response.matrix_size + column]]);
      const position = (index: number) => response.window_start_0based + Math.round((index + .5) * (response.window_end_0based - response.window_start_0based) / response.matrix_size);
      chart.setOption({
        animation: false,
        aria: { enabled: true, description: `${response.matrix_size} by ${response.matrix_size} AlphaGenome predicted contact matrix for ${response.ensembl_gene_id}.` },
        grid: { top: 28, right: 92, bottom: 48, left: 68 },
        tooltip: { trigger: "item", confine: true, formatter: (raw: unknown) => { const point = (raw as { data?: [number, number, number] }).data; return point ? `Bin A: ${position(point[0]).toLocaleString()}\nBin B: ${position(point[1]).toLocaleString()}\nPredicted contact: ${compact(point[2])}` : "Contact value unavailable"; } },
        xAxis: { type: "category", data: Array.from({ length: response.matrix_size }, (_, index) => index), axisLabel: { interval: 31, formatter: (value: string) => position(Number(value)).toLocaleString() }, axisTick: { show: false } },
        yAxis: { type: "category", data: Array.from({ length: response.matrix_size }, (_, index) => index), inverse: true, axisLabel: { interval: 31, formatter: (value: string) => position(Number(value)).toLocaleString() }, axisTick: { show: false } },
        visualMap: { min: domain[0], max: Math.max(domain[1], domain[0] + .0001), orient: "vertical", right: 8, top: 36, text: ["Higher", compact(domain[0])], inRange: { color: ["#f7fbfc", "#a1d8e8", "#49c2d9", "#7b95c6", "#c85e62"] } },
        series: [{ type: "heatmap", data, progressive: 4000, animation: false, emphasis: { itemStyle: { borderColor: "#0f172a", borderWidth: 1 } } }],
      });
      window.addEventListener("resize", resize);
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to initialize the contact map."));
    return () => { cancelled = true; window.removeEventListener("resize", resize); chart?.dispose(); };
  }, [domain, response]);

  if (error) return <div className="alphagenome-chart-error" role="alert"><strong>Contact map unavailable</strong><span>{error}</span></div>;
  return <div className="alphagenome-figure"><div className="alphagenome-figure-heading"><div><strong>Reference-sequence 3D contact prediction</strong><span>A sequential color scale describes this predicted contact map only{colorDomain ? "; the selected compatible maps share this display scale." : "."}</span></div><span>{response.matrix_size} × {response.matrix_size} bins</span></div><div ref={element} className="alphagenome-contact-chart" role="img" aria-label={`${response.matrix_size} by ${response.matrix_size} predicted contact map; numeric range ${compact(domain[0])} to ${compact(domain[1])}`} /><dl className="alphagenome-matrix-summary"><div><dt>Matrix</dt><dd>{response.matrix_size} × {response.matrix_size}</dd></div><div><dt>Source resolution</dt><dd>{response.source_resolution_bp.toLocaleString()} bp</dd></div><div><dt>Color range</dt><dd>{compact(domain[0])}–{compact(domain[1])}{colorDomain ? " · shared" : " · this map"}</dd></div></dl></div>;
}
