"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { ChevronRight, Layers3, SlidersHorizontal, X } from "lucide-react";
import type { AlphaGenomeContactMapResponse, AlphaGenomeGeneCandidate, AlphaGenomeJunctionResponse, AlphaGenomeSignalResponse, AlphaGenomeSummaryResponse, AlphaGenomeTrack, AlphaGenomeTrackCatalogResponse } from "../lib/api";
import { ALPHAGENOME_MODALITIES, ALPHAGENOME_MODALITY_LABELS, biosampleLabel, catalogCoverage, chooseOverviewPreset, formatLocus, mappingStatus, predictionContext, preferredCandidate, trackDisplayLabel } from "../lib/alphagenome-view";
import { getJson } from "../lib/api-client";
import { useJsonResource } from "../lib/use-json-resource";
import { StatusMessage } from "./status-message";
import { AlphaGenomeJunctions } from "./alphagenome-junctions";
import { SourceContext } from "./ui/source-context";

const SignalChart = dynamic(() => import("./alphagenome-chart").then((module) => module.AlphaGenomeSignalChart), { ssr: false, loading: () => <p className="alphagenome-loading">Preparing comparison chart…</p> });
const ContactChart = dynamic(() => import("./alphagenome-chart").then((module) => module.AlphaGenomeContactChart), { ssr: false, loading: () => <p className="alphagenome-loading">Preparing contact heatmap…</p> });
const COMPARISON_COLORS = ["#7b95c6", "#49c2d9", "#67a583", "#f59c7c", "#c85e62"];
const MAX_TRACKS = 5;
type Modality = typeof ALPHAGENOME_MODALITIES[number];
type PredictionResponse = AlphaGenomeSignalResponse | AlphaGenomeJunctionResponse | AlphaGenomeContactMapResponse;
type LoadState<T> = { kind: "idle" | "loading" } | { kind: "error"; error: string } | { kind: "ready"; response: T };
type ComparisonState = { kind: "idle" | "loading" } | { kind: "error"; error: string } | { kind: "ready"; responses: PredictionResponse[]; errors: string[] };

function comparisonLabel(track: AlphaGenomeTrack) {
  const detail = track.histone_mark || (track.strand && track.strand !== "." ? `${track.strand} strand` : null);
  return `${biosampleLabel(track)}${detail ? ` · ${detail}` : ""}`;
}
function isSignal(response: PredictionResponse): response is AlphaGenomeSignalResponse { return "values" in response && !("matrix_size" in response); }
function isJunction(response: PredictionResponse): response is AlphaGenomeJunctionResponse { return "items" in response; }
function isContact(response: PredictionResponse): response is AlphaGenomeContactMapResponse { return "matrix_size" in response; }
function emptyReason(summary: AlphaGenomeSummaryResponse) {
  return summary.candidates.some((candidate) => candidate.mapping_status === "no_ensembl")
    ? "No stable Ensembl gene mapping is available for this canonical protein."
    : "A stable Ensembl mapping is available, but no local AlphaGenome prediction was generated for it.";
}

function AtAGlance({ summary, candidate, tile }: { summary: AlphaGenomeSummaryResponse; candidate: AlphaGenomeGeneCandidate; tile?: AlphaGenomeGeneCandidate["tiles"][number] }) {
  const status = mappingStatus(candidate);
  const context = predictionContext(summary.prediction_kind, summary.has_variant_effect_scores);
  return <section className="alphagenome-at-a-glance" aria-labelledby="alphagenome-glance-heading">
    <div className="alphagenome-glance-heading"><div><p className="eyebrow">Prediction context</p><h3 id="alphagenome-glance-heading">{context.title}</h3></div><span className="prediction-badge">Predicted</span></div>
    <div className="alphagenome-glance-grid">
      <article><span>Mapping status</span><strong>{status.title}</strong><small>{status.detail}</small></article>
      <article><span>Ensembl gene</span><strong>{candidate.ensembl_gene_id ?? "Not available"}</strong><small>{candidate.gene_symbol ? `${candidate.gene_symbol}${candidate.hgnc_id ? ` · ${candidate.hgnc_id}` : ""}` : "Gene symbol unavailable"}</small></article>
      <article><span>GRCh38 locus and strand</span><strong>{formatLocus(candidate)}</strong><small>Gene coordinates use the displayed 1-based closed interval.</small></article>
      <article><span>Model window</span><strong>{tile ? `${tile.tile_id} · ${(tile.window_start_0based + 1).toLocaleString()}–${tile.window_end_0based.toLocaleString()}` : "No display-ready window"}</strong><small>{tile ? "GRCh38 model window · 1 Mb" : "No bounded display tile is in this release."}</small></article>
    </div>
    <div className="alphagenome-coverage"><div><strong>Local selected-output catalog inventory</strong><small>Counts describe the shared local track catalog, not a gene-specific availability count.</small></div><ul>{catalogCoverage(summary).map((item) => <li key={item.modality}><span>{item.label}</span><b>{item.count}</b></li>)}</ul></div>
    <SourceContext source={summary.source} recordGrain="Bounded regulatory tracks predicted from the GRCh38 reference sequence" caveat={`${context.caveat} ${summary.notice} This release contains local selected outputs, not the complete AlphaGenome output catalog.`} className="alphagenome-source-context" />
  </section>;
}

function Explorer({ accession, summary }: { accession: string; summary: AlphaGenomeSummaryResponse }) {
  const readyCandidates = summary.candidates.filter((candidate) => candidate.display_ready && candidate.ensembl_gene_id);
  const exactCandidate = readyCandidates.find((candidate) => candidate.mapping_status === "exact");
  const [geneId, setGeneId] = useState(() => exactCandidate?.ensembl_gene_id ?? "");
  const candidate = readyCandidates.find((item) => item.ensembl_gene_id === geneId);
  const readyTiles = candidate?.tiles.filter((tile) => tile.display_ready) ?? [];
  const [tileId, setTileId] = useState(() => exactCandidate?.tiles.find((tile) => tile.display_ready)?.tile_id ?? "");
  const tile = readyTiles.find((item) => item.tile_id === tileId) ?? readyTiles[0];
  const [modality, setModality] = useState<Modality>("rna_seq");
  const [biosample, setBiosample] = useState("");
  const [bins, setBins] = useState<256 | 1024 | 4096>(1024);
  const [catalog, setCatalog] = useState<LoadState<AlphaGenomeTrackCatalogResponse>>({ kind: "idle" });
  const [selectedTracks, setSelectedTracks] = useState<AlphaGenomeTrack[]>([]);
  const [data, setData] = useState<ComparisonState>({ kind: "idle" });
  const [sharedContactScale, setSharedContactScale] = useState(false);

  useEffect(() => {
    if (!candidate?.ensembl_gene_id) { setCatalog({ kind: "idle" }); return; }
    const controller = new AbortController();
    setBiosample(""); setCatalog({ kind: "loading" });
    const params = new URLSearchParams({ ensembl_gene_id: candidate.ensembl_gene_id, modality });
    getJson<AlphaGenomeTrackCatalogResponse>(`/proteins/${encodeURIComponent(accession)}/alphagenome/tracks?${params}`, controller.signal)
      .then((response) => setCatalog({ kind: "ready", response }))
      .catch((error: unknown) => { if (!(error instanceof DOMException && error.name === "AbortError")) setCatalog({ kind: "error", error: error instanceof Error ? error.message : "Track catalog unavailable" }); });
    return () => controller.abort();
  }, [accession, candidate?.ensembl_gene_id, modality]);

  const biosamples = useMemo(() => catalog.kind === "ready" ? Array.from(new Set(catalog.response.tracks.map(biosampleLabel))).sort((left, right) => left.localeCompare(right)) : [], [catalog]);
  const visibleTracks = useMemo(() => catalog.kind === "ready" && biosample ? catalog.response.tracks.filter((track) => biosampleLabel(track) === biosample) : [], [biosample, catalog]);
  const selectedTrackIds = useMemo(() => new Set(selectedTracks.map((track) => track.track_id)), [selectedTracks]);
  const comparisonStart = candidate && tile ? Math.max(tile.window_start_0based, (candidate.gene_start_1based ?? tile.core_start_0based + 1) - 1) : null;
  const comparisonEnd = candidate && tile ? Math.min(tile.window_end_0based, candidate.gene_end_1based_inclusive ?? tile.core_end_0based) : null;

  useEffect(() => {
    if (!candidate?.ensembl_gene_id || !tile || comparisonStart === null || comparisonEnd === null || selectedTracks.length === 0) { setData({ kind: "idle" }); return; }
    const controller = new AbortController(); setData({ kind: "loading" });
    const requests = selectedTracks.map((track) => {
      const endpoint = track.modality === "contact_maps" ? "contact-map" : track.modality === "splice_junctions" ? "junctions" : "signals";
      const params = new URLSearchParams({ ensembl_gene_id: candidate.ensembl_gene_id!, tile_id: tile.tile_id, track_id: track.track_id, start: String(comparisonStart), end: String(comparisonEnd) });
      if (endpoint === "signals") params.set("bins", String(bins));
      if (endpoint === "junctions") params.set("limit", "60");
      if (endpoint === "contact-map") params.set("size", "128");
      return getJson<PredictionResponse>(`/proteins/${encodeURIComponent(accession)}/alphagenome/${endpoint}?${params}`, controller.signal);
    });
    void Promise.allSettled(requests).then((results) => {
      if (controller.signal.aborted) return;
      const responses: PredictionResponse[] = []; const errors: string[] = [];
      results.forEach((result, index) => result.status === "fulfilled" ? responses.push(result.value) : errors.push(`${comparisonLabel(selectedTracks[index])}: ${result.reason instanceof Error ? result.reason.message : "unavailable"}`));
      setData(responses.length ? { kind: "ready", responses, errors } : { kind: "error", error: errors.join(" · ") || "Prediction data unavailable" });
    });
    return () => controller.abort();
  }, [accession, bins, candidate?.ensembl_gene_id, comparisonEnd, comparisonStart, selectedTracks, tile]);

  function changeGene(next: string) { setGeneId(next); setSelectedTracks([]); setSharedContactScale(false); setTileId(readyCandidates.find((item) => item.ensembl_gene_id === next)?.tiles.find((item) => item.display_ready)?.tile_id ?? ""); }
  function toggleTrack(track: AlphaGenomeTrack) { setSelectedTracks((current) => current.some((item) => item.track_id === track.track_id) ? current.filter((item) => item.track_id !== track.track_id) : current.length < MAX_TRACKS ? [...current, track] : current); }
  function applyOverviewPreset() { if (catalog.kind !== "ready") return; const preset = chooseOverviewPreset(catalog.response.tracks); if (preset) { setBiosample(biosampleLabel(preset)); setSelectedTracks([preset]); } }

  const signalResponses = data.kind === "ready" ? data.responses.filter(isSignal) : [];
  const junctionResponses = data.kind === "ready" ? data.responses.filter(isJunction) : [];
  const contactResponses = data.kind === "ready" ? data.responses.filter(isContact) : [];
  const contactComparable = contactResponses.length > 1 && contactResponses.every((response) => response.source_resolution_bp === contactResponses[0].source_resolution_bp && response.track.display_unit === contactResponses[0].track.display_unit);
  const contactDomain = contactComparable ? [Math.min(...contactResponses.flatMap((response) => response.values)), Math.max(...contactResponses.flatMap((response) => response.values))] as [number, number] : undefined;
  const selectionFull = selectedTracks.length >= MAX_TRACKS;
  const trackColors = useMemo(() => Object.fromEntries(selectedTracks.map((track, index) => [track.track_id, COMPARISON_COLORS[index]])), [selectedTracks]);

  return <div className="alphagenome-explorer"><details className="alphagenome-advanced"><summary><ChevronRight aria-hidden="true" size={18} strokeWidth={2} /><span><strong>Configure track comparison</strong><small>Choose a mapped gene, local catalog track, and bounded display.</small></span></summary><div className="alphagenome-advanced-body">
      {!candidate && <div className="alphagenome-gene-gate"><strong>Choose an Ensembl gene to compare tracks</strong><span>Multiple mappings are retained; no gene is auto-selected for a comparison.</span><label><span>Mapped gene candidate</span><select value={geneId} onChange={(event) => changeGene(event.currentTarget.value)}><option value="">Select a gene…</option>{readyCandidates.map((item) => <option key={item.ensembl_gene_id} value={item.ensembl_gene_id ?? ""}>{item.gene_symbol ?? item.ensembl_gene_id} · {item.ensembl_gene_id}</option>)}</select></label></div>}
      {candidate && !tile && <StatusMessage title="Prediction display is being prepared">This mapped gene has no bounded display tile in the current release.</StatusMessage>}
      {candidate && tile && <>
        <div className="alphagenome-context-bar">{readyCandidates.length > 1 && <label><span>Mapped gene</span><select value={candidate.ensembl_gene_id ?? ""} onChange={(event) => changeGene(event.currentTarget.value)}>{readyCandidates.map((item) => <option key={item.ensembl_gene_id} value={item.ensembl_gene_id ?? ""}>{item.gene_symbol ?? item.ensembl_gene_id} · {item.ensembl_gene_id}</option>)}</select></label>}{readyTiles.length > 1 && <label><span>Model tile</span><select value={tile.tile_id} onChange={(event) => setTileId(event.currentTarget.value)}>{readyTiles.map((item) => <option key={item.tile_id} value={item.tile_id}>Tile {item.tile_index + 1} · {(item.window_start_0based + 1).toLocaleString()}–{item.window_end_0based.toLocaleString()}</option>)}</select></label>}<div className="alphagenome-locus"><strong>{candidate.gene_symbol ?? candidate.ensembl_gene_id}</strong><span>{formatLocus(candidate)}</span><small>Model window {(tile.window_start_0based + 1).toLocaleString()}–{tile.window_end_0based.toLocaleString()} · 1 Mb</small></div></div>
        <div className="alphagenome-preset"><div><strong>Overview starting configuration</strong><span>One reproducible starting track from the active catalog. It is sorted by modality, biosample label, and track ID—not signal, tissue relevance, or biological importance.</span></div><button type="button" disabled={catalog.kind !== "ready"} onClick={applyOverviewPreset}><SlidersHorizontal aria-hidden="true" size={16} />{catalog.kind === "loading" ? "Loading catalog…" : "Use overview preset"}</button></div>
        <div className="alphagenome-selection-step"><div className="alphagenome-step-heading"><span>1</span><div><strong>Browse a modality</strong><small>Catalog counts below are local catalog inventory, not a per-gene coverage metric.</small></div></div><div className="alphagenome-modality-tabs" role="group" aria-label="AlphaGenome prediction modality">{ALPHAGENOME_MODALITIES.map((item) => <button key={item} type="button" aria-pressed={modality === item} onClick={() => setModality(item)}>{ALPHAGENOME_MODALITY_LABELS[item]} <span>{summary.modality_track_counts[item] ?? 0}</span></button>)}</div></div>
        <div className="alphagenome-selection-grid"><div className="alphagenome-selection-step"><div className="alphagenome-step-heading"><span>2</span><div><strong>Choose a biosample</strong><small>Names and assay context remain visible before a track is added.</small></div></div><label className="alphagenome-biosample-picker"><span>Biosample or tissue</span><select value={biosample} disabled={catalog.kind !== "ready"} onChange={(event) => setBiosample(event.currentTarget.value)}><option value="">Select a biosample…</option>{biosamples.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>{catalog.kind === "loading" && <span className="alphagenome-picker-status">Loading local catalog metadata…</span>}{catalog.kind === "error" && <span className="alphagenome-picker-status" role="alert">{catalog.error}</span>}</div><div className="alphagenome-selection-step"><div className="alphagenome-step-heading"><span>3</span><div><strong>Add tracks to compare</strong><small>Select up to five. Signals use independent y-scales.</small></div></div>{!biosample && <div className="alphagenome-inline-prompt">Choose a biosample to inspect its catalog tracks.</div>}{biosample && <fieldset className="alphagenome-track-options"><legend className="sr-only">Tracks for {biosample}</legend>{visibleTracks.map((track) => { const checked = selectedTrackIds.has(track.track_id); return <label key={track.track_id} className={checked ? "is-selected" : undefined}><input type="checkbox" checked={checked} disabled={!checked && selectionFull} onChange={() => toggleTrack(track)} /><span><strong>{trackDisplayLabel(track)}</strong><small>{track.data_source ?? "Source unavailable"} · {track.display_unit}</small></span></label>; })}</fieldset>}</div></div>
        {selectedTracks.length > 0 && <div className="alphagenome-comparison-selection"><div className="alphagenome-comparison-heading"><div><strong>Selected comparison tracks</strong><span>{selectedTracks.length} / {MAX_TRACKS} tracks · shared genomic axis · independent signal scales</span></div><button type="button" onClick={() => setSelectedTracks([])}><X aria-hidden="true" size={16} />Clear selected tracks</button></div><div className="alphagenome-selected-tracks">{selectedTracks.map((track, index) => <button key={track.track_id} type="button" onClick={() => toggleTrack(track)} aria-label={`Remove ${comparisonLabel(track)} from comparison`}><i style={{ background: COMPARISON_COLORS[index] }} /><span><strong>{biosampleLabel(track)}</strong><small>{ALPHAGENOME_MODALITY_LABELS[track.modality] ?? track.modality} · {trackDisplayLabel(track)}</small></span><X aria-hidden="true" size={16} /></button>)}</div>{selectedTracks.some((track) => track.modality !== "contact_maps" && track.modality !== "splice_junctions") && <label className="alphagenome-resolution"><span>Display resolution</span><select value={bins} onChange={(event) => setBins(Number(event.currentTarget.value) as 256 | 1024 | 4096)}><option value={256}>Overview · 256 bins</option><option value={1024}>Standard · 1,024 bins</option><option value={4096}>Detail · 4,096 bins</option></select></label>}</div>}
        {selectedTracks.length === 0 && catalog.kind === "ready" && <div className="alphagenome-prompt"><strong>Configure a bounded comparison</strong><span>Use the neutral overview starting configuration or choose a biosample and track. No tissue is pre-labelled as most relevant.</span></div>}
        {data.kind === "loading" && <p className="alphagenome-loading">Loading {selectedTracks.length} bounded prediction {selectedTracks.length === 1 ? "track" : "tracks"}…</p>}{data.kind === "error" && <div className="alphagenome-chart-error" role="alert"><strong>Prediction data unavailable</strong><span>{data.error}</span></div>}{data.kind === "ready" && data.errors.length > 0 && <div className="alphagenome-partial-warning" role="status">Some tracks could not be loaded: {data.errors.join(" · ")}</div>}{data.kind === "ready" && data.responses.length > 0 && <div className="alphagenome-axis-banner"><strong>{candidate.gene_symbol ?? candidate.ensembl_gene_id} gene interval</strong><span>{candidate.chromosome}:{(comparisonStart! + 1).toLocaleString()}–{comparisonEnd!.toLocaleString()} · signals retain independent y-scales</span></div>}
        {signalResponses.length > 0 && <SignalChart responses={signalResponses} axisStart={comparisonStart!} axisEnd={comparisonEnd!} trackColors={trackColors} />}{junctionResponses.length > 0 && <div className="alphagenome-multimodal-stack">{junctionResponses.map((response) => <article key={response.track.track_id}><header><i style={{ background: trackColors[response.track.track_id] }} /><div><strong>Junctions · {biosampleLabel(response.track)}</strong><small>{trackDisplayLabel(response.track)}</small></div></header><AlphaGenomeJunctions response={response} tile={tile} axisStart={comparisonStart!} axisEnd={comparisonEnd!} /></article>)}</div>}{contactResponses.length > 0 && <div className="alphagenome-multimodal-stack">{contactResponses.length > 1 && <label className="alphagenome-shared-scale"><input type="checkbox" checked={sharedContactScale} disabled={!contactComparable} onChange={(event) => setSharedContactScale(event.currentTarget.checked)} /> <span>Use one shared contact color scale</span><small>{contactComparable ? "Enabled only because resolution and display unit match; this is a visual comparison setting." : "Unavailable: selected maps have different resolution or display units."}</small></label>}{contactResponses.map((response) => <article key={response.track.track_id}><header><i style={{ background: trackColors[response.track.track_id] }} /><div><strong>3D contact · {biosampleLabel(response.track)}</strong><small>{trackDisplayLabel(response.track)}</small></div></header><ContactChart response={response} colorDomain={sharedContactScale && contactComparable ? contactDomain : undefined} /></article>)}</div>}
      </>}</div></details>
  </div>;
}

function AlphaGenomeReady({ accession, summary }: { accession: string; summary: AlphaGenomeSummaryResponse }) {
  const [open, setOpen] = useState(false); const candidate = preferredCandidate(summary.candidates); const tile = candidate?.tiles.find((item) => item.display_ready);
  if (!candidate) return null;
  const context = predictionContext(summary.prediction_kind, summary.has_variant_effect_scores);
  return <div className="alphagenome-card"><div className="alphagenome-summary-row"><div><Layers3 aria-hidden="true" size={20} strokeWidth={1.9} /><span className="prediction-badge">Predicted</span><strong>{context.title}</strong><small>At-a-glance source, locus, and interpretation scope are shown before any comparison is configured.</small></div><button type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)}>{open ? "Close comparison workspace" : "Explore predicted tracks"}<ChevronRight aria-hidden="true" size={18} strokeWidth={2} /></button></div><AtAGlance summary={summary} candidate={candidate} tile={tile} />{open && <Explorer accession={accession} summary={summary} />}</div>;
}

function AlphaGenomeAvailability({ summary }: { summary: AlphaGenomeSummaryResponse }) {
  const candidate = preferredCandidate(summary.candidates);
  return <div className="alphagenome-card">{candidate && <AtAGlance summary={summary} candidate={candidate} tile={candidate.tiles.find((item) => item.display_ready)} />}<div className="alphagenome-empty"><span className="prediction-badge">Predicted</span><strong>{summary.availability === "preparing" ? "Prediction found; display bundle is being prepared" : "No local AlphaGenome prediction"}</strong><p>{summary.availability === "preparing" ? "The source archive contains a reference-sequence prediction for this protein, but its bounded web tiles are not in the current generated release." : emptyReason(summary)}</p></div></div>;
}

export function AlphaGenomePanel({ accession }: { accession: string }) {
  const state = useJsonResource<AlphaGenomeSummaryResponse>(`/proteins/${encodeURIComponent(accession)}/alphagenome/summary`, "Unable to load AlphaGenome availability.");
  return <section id="alphagenome" className="overview-section" aria-labelledby="alphagenome-heading"><div className="section-heading"><p className="eyebrow">Reference-sequence model prediction</p><h2 id="alphagenome-heading">AlphaGenome regulatory landscape</h2></div>{state.kind === "loading" && <p className="alphagenome-loading">Checking local prediction availability…</p>}{state.kind === "error" && <StatusMessage title="AlphaGenome unavailable" tone="error">{state.error}</StatusMessage>}{state.kind === "ready" && state.response.availability === "available" && <AlphaGenomeReady accession={accession} summary={state.response} />}{state.kind === "ready" && state.response.availability !== "available" && <AlphaGenomeAvailability summary={state.response} />}{state.kind === "ready" && <p className="alphagenome-footnote">Local selected-output subset · GRCh38 · DNase and transcription-factor ChIP are not present · reference-sequence predictions are not experimental measurements, clinical evidence, or variant-effect scores.</p>}</section>;
}
