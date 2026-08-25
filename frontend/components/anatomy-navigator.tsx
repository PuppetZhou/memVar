"use client";

import { KeyboardEvent, PointerEvent as ReactPointerEvent, WheelEvent as ReactWheelEvent, useState } from "react";
import { RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AnatomyEvidenceSummary, AnatomyRegionSummary, AnatomySummaryResponse } from "../lib/api";
import { ANATOMY_MAP_WIDTH, AnatomyViewBox, FULL_ANATOMY_VIEW, clampAnatomyView, zoomAnatomyView } from "../lib/anatomy-map";
import { ANATOMY_IMAGE } from "../lib/anatomy-geometry";
import { groupRegionsByTissueSystem, tissueVisualForRegion } from "../lib/tissue-visuals";
import { useJsonResource } from "../lib/use-json-resource";
import { formatTermLabel } from "../lib/display-labels";
import { StatusMessage } from "./status-message";
import { TissueSystemIcon } from "./tissue-system-icon";

type AnatomyLayer = "all" | "expression" | "gen" | "qtl";

const LAYERS: Array<{ id: AnatomyLayer; label: string; color: string }> = [
  { id: "all", label: "All sources", color: "#52606D" },
  { id: "expression", label: "Expression", color: "#1B75BC" },
  { id: "gen", label: "GEN", color: "#D94949" },
  { id: "qtl", label: "QTL", color: "#AA77E9" },
];

type AnatomyPan = { pointerId: number; clientX: number; clientY: number; origin: AnatomyViewBox };

function layerLabel(layer: "expression" | "gen" | "qtl") {
  return layer === "gen" ? "GEN differential expression" : layer === "qtl" ? "QTL" : "Expression";
}

function destination(layer: "expression" | "gen" | "qtl") {
  return layer === "qtl" ? "qtl" : "expression";
}

function evidenceFor(region: AnatomyRegionSummary, layer: AnatomyLayer): AnatomyEvidenceSummary[] {
  return layer === "all" ? region.evidence : region.evidence.filter((item) => item.layer === layer);
}

export function AnatomyNavigator({ accession }: { accession: string }) {
  const state = useJsonResource<AnatomySummaryResponse>(
    `/proteins/${encodeURIComponent(accession)}/anatomy/summary`,
    "Unable to load anatomy availability.",
  );
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selectedId = searchParams.get("anatomy");
  const layerParam = searchParams.get("anatomy_layer");
  const activeLayer: AnatomyLayer = layerParam === "expression" || layerParam === "gen" || layerParam === "qtl" ? layerParam : "all";
  const regions = state.kind === "ready" ? state.response.regions : [];
  const selected = regions.find((item) => item.body_region_id === selectedId) ?? null;
  const selectedVisual = selected ? tissueVisualForRegion(selected.body_region_id) : null;
  const selectedEvidence = selected ? evidenceFor(selected, activeLayer) : [];
  const groupedRegions = groupRegionsByTissueSystem(regions);
  const [viewBox, setViewBox] = useState<AnatomyViewBox>(FULL_ANATOMY_VIEW);
  const [pan, setPan] = useState<AnatomyPan | null>(null);
  const zoom = ANATOMY_MAP_WIDTH / viewBox.width;

  function updateUrl(region: AnatomyRegionSummary | null, layer: AnatomyLayer = activeLayer) {
    const params = new URLSearchParams(searchParams.toString());
    if (region) params.set("anatomy", region.body_region_id); else params.delete("anatomy");
    if (layer === "all") params.delete("anatomy_layer"); else params.set("anatomy_layer", layer);
    router.replace(`${pathname}${params.size ? `?${params}` : ""}`, { scroll: false });
  }

  function zoomAt(factor: number, ratioX = .5, ratioY = .5) {
    setViewBox((current) => zoomAnatomyView(current, factor, ratioX, ratioY));
  }

  function wheel(event: ReactWheelEvent<SVGSVGElement>) {
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
    zoomAt(event.deltaY < 0 ? 1.2 : 1 / 1.2, (event.clientX - rect.left) / rect.width, (event.clientY - rect.top) / rect.height);
  }

  function pointerDown(event: ReactPointerEvent<SVGSVGElement>) {
    if (zoom <= 1) return;
    setPan({ pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY, origin: viewBox });
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function pointerMove(event: ReactPointerEvent<SVGSVGElement>) {
    if (!pan || pan.pointerId !== event.pointerId) return;
    const rect = event.currentTarget.getBoundingClientRect();
    setViewBox(clampAnatomyView({
      ...pan.origin,
      x: pan.origin.x - (event.clientX - pan.clientX) / rect.width * pan.origin.width,
      y: pan.origin.y - (event.clientY - pan.clientY) / rect.height * pan.origin.height,
    }));
  }

  function finishPan(event: ReactPointerEvent<SVGSVGElement>) {
    if (!pan || pan.pointerId !== event.pointerId) return;
    setPan(null);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  }

  function mapKeyDown(event: KeyboardEvent<SVGSVGElement>) {
    if (event.key === "+" || event.key === "=") { event.preventDefault(); zoomAt(1.25); }
    else if (event.key === "-" || event.key === "_") { event.preventDefault(); zoomAt(1 / 1.25); }
    else if (event.key === "Home") { event.preventDefault(); setViewBox(FULL_ANATOMY_VIEW); }
    else if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key) && zoom > 1) {
      event.preventDefault();
      const stepX = viewBox.width * .1;
      const stepY = viewBox.height * .1;
      setViewBox(clampAnatomyView({ ...viewBox, x: viewBox.x + (event.key === "ArrowRight" ? stepX : event.key === "ArrowLeft" ? -stepX : 0), y: viewBox.y + (event.key === "ArrowDown" ? stepY : event.key === "ArrowUp" ? -stepY : 0) }));
    }
  }

  return <section id="anatomy" className="overview-section anatomy-section" aria-labelledby="anatomy-heading">
    <div className="section-heading split-heading"><div><p className="eyebrow">Cross-evidence navigation</p><h2 id="anatomy-heading">Anatomy navigator</h2></div>{selected && <button type="button" className="quiet-button" onClick={() => updateUrl(null)}>Clear {selected.display_label}</button>}</div>
    <p className="section-intro">Choose a standard body region from the tissue index, then inspect Expression, GEN differential expression, or QTL independently. The illustration is an orientation background only; it does not claim precise tissue coordinates. Colors indicate source availability only, and values and units are never combined.</p>
    <div className="anatomy-layer-switch" role="group" aria-label="Anatomy evidence layer">{LAYERS.map((layer) => <button key={layer.id} type="button" aria-pressed={activeLayer === layer.id} onClick={() => updateUrl(selected, layer.id)}><i style={{ backgroundColor: layer.color }} />{layer.label}</button>)}</div>
    {state.kind === "loading" && <StatusMessage title="Loading anatomy availability">Reading protein-scoped source counts through the explicit tissue crosswalk.</StatusMessage>}
    {state.kind === "error" && <StatusMessage title="Anatomy navigator unavailable" tone="error">{state.error}</StatusMessage>}
    {state.kind === "ready" && <div className="anatomy-layout">
      <div className="anatomy-map-card">
        <div className="anatomy-map-toolbar" aria-label="Anatomy map zoom controls"><button type="button" onClick={() => zoomAt(1.3)} aria-label="Zoom anatomy map in"><ZoomIn aria-hidden="true" /></button><button type="button" onClick={() => zoomAt(1 / 1.3)} aria-label="Zoom anatomy map out"><ZoomOut aria-hidden="true" /></button><button type="button" onClick={() => setViewBox(FULL_ANATOMY_VIEW)}><RotateCcw aria-hidden="true" />Reset</button><span>{Math.round(zoom * 100)}%</span></div>
        <div className="anatomy-map-shell"><svg className={`anatomy-map ${pan ? "is-panning" : ""}`} viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`} role="img" tabIndex={0} aria-label="BioRender human anatomy orientation background. Tissue positions are not marked. Use the tissue index to select evidence; use the mouse wheel or plus and minus to zoom, and drag to pan." onWheel={wheel} onPointerDown={pointerDown} onPointerMove={pointerMove} onPointerUp={finishPan} onPointerCancel={finishPan} onDoubleClick={() => setViewBox(FULL_ANATOMY_VIEW)} onKeyDown={mapKeyDown}>
          <image className="anatomy-biorender-base" href={ANATOMY_IMAGE.href} x="0" y="0" width={ANATOMY_IMAGE.displayWidth} height={ANATOMY_IMAGE.displayHeight} preserveAspectRatio={ANATOMY_IMAGE.preserveAspectRatio} />
        </svg></div>
        <div className="anatomy-map-notice"><strong>Orientation background</strong><span>No tissue markers are shown. Select a named region from the tissue index.</span></div>
        <p className="anatomy-map-help">Scroll to zoom · drag to pan · double-click or press Home to reset</p>
        <p className="anatomy-attribution">Anatomy illustration · Created with BioRender.com · <a href="https://app.biorender.com/illustrations/6191fd4843d685255a905b95?slideId=dfb438b2-5e43-5e13-589a-25b10c97a925" target="_blank" rel="noreferrer">View figure record</a></p>
      </div>
      <div className="anatomy-region-list" aria-label="Standard anatomy regions grouped by body system">
        {groupedRegions.map(({ system, regions: systemRegions }) => <section className="anatomy-system-group" key={system.id} aria-labelledby={`anatomy-system-${system.id}`}><header>{system.iconKey !== "other" && <span className="anatomy-system-icon"><TissueSystemIcon systemId={system.id} /></span>}<span><strong id={`anatomy-system-${system.id}`}>{system.label}</strong><small>{systemRegions.length} standard region{systemRegions.length === 1 ? "" : "s"}</small></span></header><div role="list">{systemRegions.map((region) => { const evidence = evidenceFor(region, activeLayer); const count = evidence.reduce((sum, item) => sum + item.record_count, 0); return <button key={region.body_region_id} type="button" role="listitem" data-layer={activeLayer} data-system={system.id} aria-pressed={selectedId === region.body_region_id} onClick={() => updateUrl(region)}><span>{region.display_label}</span><strong>{count.toLocaleString()}</strong><small>{evidence.length ? `${activeLayer === "all" ? "source" : activeLayer} records` : `No ${activeLayer === "all" ? "mapped" : activeLayer} records`}</small></button>; })}</div></section>)}
      </div>
      <div className="anatomy-evidence">
        {!selected && <StatusMessage title="Select a body region">The source cards retain raw tissue/context terms and keep Expression, GEN and QTL counts separate.</StatusMessage>}
        {selected && <><div className="anatomy-selection-heading"><div className="anatomy-selected-region">{selectedVisual!.iconKey !== "other" && <span className="anatomy-system-icon is-selected"><TissueSystemIcon systemId={selectedVisual!.id} selected /></span>}<div><p className="eyebrow">Selected region · {selectedVisual!.label}</p><h3>{selected.display_label}</h3></div></div>{selected.ontology_id && <span>{selected.ontology_id}</span>}</div>{selectedEvidence.length ? <div className="anatomy-source-cards">{selectedEvidence.map((item) => <button className={`layer-${item.layer}`} key={`${item.layer}-${item.source_database}-${item.modality_or_type}`} type="button" onClick={() => document.getElementById(destination(item.layer))?.scrollIntoView({ behavior: "smooth", block: "start" })}><span>{layerLabel(item.layer)} · {item.source_database}</span><strong>{item.record_count.toLocaleString()}</strong><small>{formatTermLabel(item.modality_or_type)} · {item.distinct_context_count} raw context{item.distinct_context_count === 1 ? "" : "s"}</small><em>{item.raw_filter_terms.join(" · ")}</em></button>)}</div> : <StatusMessage title={`No ${activeLayer === "all" ? "mapped" : activeLayer} ${selected.display_label} records`}>This is an explicit empty state in the current website release.</StatusMessage>}</>}
      </div>
    </div>}
  </section>;
}
