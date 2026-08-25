"use client";

import dynamic from "next/dynamic";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Crosshair } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlphaFoldStructuresResponse, SequenceVariantSiteDensity, SequenceVariantSiteDensityResponse } from "../lib/api";
import { getJson, resolveApiUrl } from "../lib/api-client";
import type { SiteSelection } from "./sequence-explorer";

const LazyStructureViewer = dynamic(
  () => import("./structure-viewer").then((module) => module.StructureViewer),
  {
    ssr: false,
    loading: () => <div className="structure-viewer-placeholder" role="status"><strong>Preparing 3D viewer</strong><span>Loading the browser visualization tools.</span></div>,
  },
);

type PanelState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: AlphaFoldStructuresResponse };

type VariantDensityState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: SequenceVariantSiteDensity };

function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value < 0) return "Unknown size";
  if (value < 1024) return `${value.toLocaleString()} B`;
  const units = ["KB", "MB", "GB"];
  let size = value / 1024;
  let unit = units[0];
  for (let index = 1; index < units.length && size >= 1024; index += 1) {
    size /= 1024;
    unit = units[index];
  }
  return `${size >= 10 ? size.toFixed(1) : size.toFixed(2)} ${unit}`;
}

function canonicalRange(start: number | null, end: number | null): string {
  if (start === null || end === null) return "Canonical range unavailable from DBREF";
  return `Canonical aa ${start.toLocaleString()}–${end.toLocaleString()}`;
}

export function StructurePanel({
  accession,
  selection,
  onSelectionChange,
}: {
  accession: string;
  selection: SiteSelection;
  onSelectionChange: (selection: SiteSelection) => void;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const sectionRef = useRef<HTMLElement>(null);
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [variantDensity, setVariantDensity] = useState<VariantDensityState>({ kind: "loading" });
  const [activeFragment, setActiveFragment] = useState<string>("");
  const [viewerRequested, setViewerRequested] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    setActiveFragment("");
    setViewerRequested(false);
    getJson<AlphaFoldStructuresResponse>(`/proteins/${encodeURIComponent(accession)}/structures`, controller.signal)
      .then((data) => {
        setState({ kind: "ready", data });
        setActiveFragment(data.fragments[0]?.fragment_label ?? "");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", message: error instanceof Error ? error.message : "Unable to retrieve AlphaFold structure metadata." });
      });
    return () => controller.abort();
  }, [accession]);

  // The structure layer reads only the canonical variant-density projection.
  useEffect(() => {
    const controller = new AbortController();
    setVariantDensity({ kind: "loading" });
    getJson<SequenceVariantSiteDensityResponse>(`/proteins/${encodeURIComponent(accession)}/sequence/variant-site-density`, controller.signal)
      .then((data) => setVariantDensity({ kind: "ready", data: data.variant_site_density }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setVariantDensity({ kind: "error", message: error instanceof Error ? error.message : "Unable to load the canonical variant-density summary." });
      });
    return () => controller.abort();
  }, [accession]);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section || viewerRequested) return;
    if (!("IntersectionObserver" in window)) {
      setViewerRequested(true);
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        setViewerRequested(true);
        observer.disconnect();
      }
    }, { rootMargin: "320px 0px", threshold: 0.01 });
    observer.observe(section);
    return () => observer.disconnect();
  }, [viewerRequested]);

  const structure = state.kind === "ready" ? state.data : null;
  const fragment = useMemo(() => {
    if (!structure) return null;
    return structure.fragments.find((item) => item.fragment_label === activeFragment) ?? structure.fragments[0] ?? null;
  }, [activeFragment, structure]);
  const selectedPosition = selection?.site ?? null;
  const selectedFragment = useMemo(() => {
    if (!structure || selectedPosition === null) return null;
    return structure.fragments.find((item) => (
      item.canonical_start !== null
      && item.canonical_end !== null
      && selectedPosition >= item.canonical_start
      && selectedPosition <= item.canonical_end
    )) ?? null;
  }, [selectedPosition, structure]);

  // A new site selection follows its real AlphaFold fragment. Manual fragment
  // changes remain possible afterwards; fragments are never stitched together.
  useEffect(() => {
    if (!selectedFragment) return;
    setActiveFragment((current) => current === selectedFragment.fragment_label ? current : selectedFragment.fragment_label);
  }, [selectedFragment]);

  const selectCanonicalPosition = useCallback((position: number | null) => {
    const next: SiteSelection = position === null ? null : { start: position, end: position, site: position };
    onSelectionChange(next);
    const params = new URLSearchParams(searchParams.toString());
    params.delete("site");
    params.delete("range");
    if (position !== null) params.set("site", String(position));
    router.replace(`${pathname}${params.size ? `?${params}` : ""}`, { scroll: false });
  }, [onSelectionChange, pathname, router, searchParams]);

  return <section ref={sectionRef} id="structure" className="overview-section structure-section" aria-labelledby="structure-heading">
    <div className="section-heading split-heading">
      <div><p className="eyebrow">AlphaFold predicted model</p><h2 id="structure-heading">Protein structure</h2></div>
      {structure?.availability === "available" && <span className="structure-availability">{structure.fragment_total.toLocaleString()} fragment{structure.fragment_total === 1 ? "" : "s"} · v{structure.model_version}</span>}
    </div>
    <p className="section-intro">Explore the local AlphaFold prediction in a molecular surface view. Switch independently between canonical Sequence variant density and pLDDT confidence; selecting a canonical residue focuses its atomic neighbourhood.</p>

    {state.kind === "loading" && <div className="structure-panel-state" role="status"><strong>Checking structure availability</strong><span>Reading the local AlphaFold v6 model index.</span></div>}
    {state.kind === "error" && <div className="structure-panel-state structure-panel-error" role="alert"><strong>Structure metadata unavailable</strong><span>{state.message}</span></div>}

    {structure?.availability === "unavailable" && <div className="structure-panel-state structure-panel-empty">
      <strong>No local AlphaFold v6 model</strong>
      <span>This canonical protein is not represented in the supplied human AlphaFold archive. No structure is inferred or fetched from an external service.</span>
    </div>}

    {structure?.availability === "available" && fragment && <div className="structure-panel-card">
      {selectedPosition !== null && <div className={`structure-crosslink-status ${selectedFragment ? "is-covered" : "is-uncovered"}`} role="status">
        <Crosshair aria-hidden="true" size={19} />
        <span>
          <strong>Canonical residue {selectedPosition.toLocaleString()}</strong>
          {selectedFragment
            ? <> is covered by {selectedFragment.fragment_label}; the loaded model will validate the mapping before showing a navigation highlight.</>
            : <> is not covered by a validated local AlphaFold fragment; no 3D location is inferred.</>}
        </span>
        {selectedFragment && <button type="button" className="quiet-button" onClick={() => {
          setActiveFragment(selectedFragment.fragment_label);
          setViewerRequested(true);
        }}>Show in 3D</button>}
      </div>}
      <div className="structure-fragment-bar">
        <label>
          <span>Structure fragment</span>
          <select value={fragment.fragment_label} onChange={(event) => setActiveFragment(event.currentTarget.value)}>
            {structure.fragments.map((item) => <option key={item.fragment_number} value={item.fragment_label}>{item.fragment_label} · {canonicalRange(item.canonical_start, item.canonical_end)}</option>)}
          </select>
        </label>
        <dl className="structure-fragment-facts">
          <div><dt>Canonical coverage</dt><dd>{canonicalRange(fragment.canonical_start, fragment.canonical_end)}</dd></div>
          <div><dt>Compressed PDB</dt><dd>{formatBytes(fragment.compressed_bytes)}</dd></div>
          <div><dt>Uncompressed</dt><dd>{formatBytes(fragment.uncompressed_bytes)}</dd></div>
          <div><dt>Source</dt><dd>{structure.source} · model v{structure.model_version}</dd></div>
        </dl>
      </div>

      {structure.fragments.length > 1 && <p className="structure-fragment-note">Fragments are separate AlphaFold predictions for portions of the same canonical protein. They are viewed independently and are never stitched into a synthetic model.</p>}

      {viewerRequested
        ? <LazyStructureViewer
            key={fragment.fragment_number}
            fragment={fragment}
            structureUrl={resolveApiUrl(fragment.content_url)}
            downloadUrl={resolveApiUrl(fragment.download_url)}
            variantDensity={variantDensity.kind === "ready" ? variantDensity.data : null}
            variantDensityStatus={variantDensity.kind}
            variantDensityError={variantDensity.kind === "error" ? variantDensity.message : null}
            selectedCanonicalPosition={selectedPosition}
            onSelectCanonicalPosition={selectCanonicalPosition}
          />
        : <div className="structure-viewer-placeholder">
            <strong>3D viewer is paused</strong>
            <span>Load the interactive view when needed. The viewer will also initialize as this panel enters the viewport.</span>
            <div className="structure-placeholder-actions">
              <button type="button" className="primary-button" onClick={() => setViewerRequested(true)}>Load 3D structure</button>
              <a className="quiet-button structure-download-link" href={resolveApiUrl(fragment.download_url)}>Download PDB</a>
            </div>
          </div>}
    </div>}
  </section>;
}
