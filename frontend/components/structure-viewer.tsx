"use client";

import { useEffect, useRef, useState } from "react";
import { Crosshair, Download, LocateFixed, Maximize2, Minimize2, RotateCcw, X } from "lucide-react";
import type { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import type { ColorTheme, LocationColor } from "molstar/lib/mol-theme/color";
import type { AlphaFoldStructureFragment, SequenceVariantSiteDensity } from "../lib/api";
import {
  canonicalToFragmentResidue,
  fragmentToCanonicalResidue,
  sequenceVariantColor,
  validateFragmentResidueMapping,
} from "../lib/structure-colors";
import { variantCountBuckets } from "../lib/sequence-track-colors";

type ViewerStatus =
  | { kind: "loading" }
  | { kind: "ready" }
  | { kind: "no-webgl" }
  | { kind: "error"; message: string };

type MolstarRuntime = {
  createPluginUI: typeof import("molstar/lib/mol-plugin-ui").createPluginUI;
};

type StructureRuntime = typeof import("molstar/lib/mol-model/structure");

type StructureColorMode = "sequence-variants" | "plddt-confidence";
type VariantDensityStatus = "loading" | "ready" | "error";

const PLDDT_BANDS = [
  { label: "Very high", range: "> 90", color: "#0053D6" },
  { label: "Confident", range: "70–90", color: "#65CBF3" },
  { label: "Low", range: "50–70", color: "#FFDB13" },
  { label: "Very low", range: "< 50", color: "#FF7D45" },
] as const;

const SEQUENCE_VARIANT_BANDS = variantCountBuckets();

function webGlAvailable(): boolean {
  try {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("webgl2") ?? canvas.getContext("webgl");
    context?.getExtension("WEBGL_lose_context")?.loseContext();
    return context !== null;
  } catch {
    return false;
  }
}

function selectedElements(fragmentPosition: number) {
  return { auth_seq_id: fragmentPosition };
}

function descriptionForColorMode(mode: StructureColorMode): string {
  return mode === "sequence-variants"
    ? "Sequence variant-density molecular surface"
    : "pLDDT molecular surface";
}

export function StructureViewer({
  fragment,
  structureUrl,
  downloadUrl,
  variantDensity,
  variantDensityStatus,
  variantDensityError,
  selectedCanonicalPosition,
  onSelectCanonicalPosition,
}: {
  fragment: AlphaFoldStructureFragment;
  structureUrl: string;
  downloadUrl: string;
  variantDensity: SequenceVariantSiteDensity | null;
  variantDensityStatus: VariantDensityStatus;
  variantDensityError: string | null;
  selectedCanonicalPosition: number | null;
  onSelectCanonicalPosition: (position: number | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<PluginUIContext | null>(null);
  const mappingRef = useRef(validateFragmentResidueMapping(fragment, []));
  const selectedPositionRef = useRef(selectedCanonicalPosition);
  const selectionCallbackRef = useRef(onSelectCanonicalPosition);
  const selectFragmentResidueRef = useRef<(fragmentPosition: number | null) => void>(() => {});
  const applyColorModeRef = useRef<(mode: StructureColorMode) => void>(() => {});
  const variantDensityRef = useRef<SequenceVariantSiteDensity | null>(variantDensity);
  const variantDensityIdentityRef = useRef<SequenceVariantSiteDensity | null>(variantDensity);
  const variantDensityRevisionRef = useRef(0);
  const [status, setStatus] = useState<ViewerStatus>({ kind: "loading" });
  const [colorMode, setColorMode] = useState<StructureColorMode>("sequence-variants");
  const [fullscreen, setFullscreen] = useState(false);
  const [fullscreenSupported, setFullscreenSupported] = useState(false);
  const [fullscreenError, setFullscreenError] = useState<string | null>(null);

  selectedPositionRef.current = selectedCanonicalPosition;
  selectionCallbackRef.current = onSelectCanonicalPosition;
  if (variantDensityIdentityRef.current !== variantDensity) {
    variantDensityIdentityRef.current = variantDensity;
    variantDensityRevisionRef.current += 1;
  }
  variantDensityRef.current = variantDensity;

  useEffect(() => {
    if (status.kind === "ready") applyColorModeRef.current(colorMode);
  }, [colorMode, status.kind, variantDensity]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || status.kind !== "ready") return;
    if (selectedCanonicalPosition === null) {
      selectFragmentResidueRef.current(null);
      return;
    }
    const fragmentPosition = canonicalToFragmentResidue(selectedCanonicalPosition, mappingRef.current);
    if (fragmentPosition === null) {
      selectFragmentResidueRef.current(null);
      return;
    }
    selectFragmentResidueRef.current(fragmentPosition);
  }, [selectedCanonicalPosition, status.kind]);

  useEffect(() => {
    setFullscreenSupported(Boolean(document.fullscreenEnabled && shellRef.current?.requestFullscreen));
    const syncFullscreen = () => {
      setFullscreen(document.fullscreenElement === shellRef.current);
      window.requestAnimationFrame(() => viewerRef.current?.canvas3d?.requestResize());
    };
    document.addEventListener("fullscreenchange", syncFullscreen);
    return () => document.removeEventListener("fullscreenchange", syncFullscreen);
  }, []);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const viewerHost = host;

    let active = true;
    let resizeFrame: number | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let clickSubscription: { unsubscribe(): void } | null = null;
    const controller = new AbortController();

    setStatus({ kind: "loading" });
    mappingRef.current = validateFragmentResidueMapping(fragment, []);

    async function load() {
      if (!webGlAvailable()) {
        setStatus({ kind: "no-webgl" });
        return;
      }

      try {
        const [molstarRuntime, { renderReact18 }, { DefaultPluginUISpec }, { applyStructureInteractivity }, { PLDDTConfidenceColorThemeProvider }, { ungzip }, { SyncRuntimeContext }, structureRuntime, { ColorTheme }, { Color }, { ParamDefinition }] = await Promise.all([
          import("molstar/lib/mol-plugin-ui") as Promise<MolstarRuntime>,
          import("molstar/lib/mol-plugin-ui/react18"),
          import("molstar/lib/mol-plugin-ui/spec"),
          import("molstar/lib/extensions/plugin/interactivity"),
          import("molstar/lib/extensions/model-archive/quality-assessment/color/plddt"),
          import("molstar/lib/mol-util/zip/zip"),
          import("molstar/lib/mol-task/execution/synchronous"),
          import("molstar/lib/mol-model/structure") as Promise<StructureRuntime>,
          import("molstar/lib/mol-theme/color"),
          import("molstar/lib/mol-util/color"),
          import("molstar/lib/mol-util/param-definition"),
        ]);
        if (!active) return;

        const spec = DefaultPluginUISpec();
        spec.layout = {
          ...spec.layout,
          initial: { isExpanded: false, showControls: false, controlsDisplay: "landscape" },
        };
        spec.components = {
          ...spec.components,
          controls: { top: "none", left: "none", right: "none", bottom: "none" },
          remoteState: "none",
          disableDragOverlay: true,
        };
        const viewer = await molstarRuntime.createPluginUI({
          target: viewerHost,
          render: renderReact18,
          spec,
          onBeforeUIRender: (plugin) => {
            plugin.representation.structure.themes.colorThemeRegistry.add(PLDDTConfidenceColorThemeProvider);
            const SequenceVariantDensityColorThemeParams = {
              dataRevision: ParamDefinition.Numeric(0, { min: 0, step: 1 }, { isHidden: true }),
            };
            const SequenceVariantDensityColorThemeProvider: ColorTheme.Provider<typeof SequenceVariantDensityColorThemeParams, "sequence-variant-density", "group"> = {
              name: "sequence-variant-density",
              label: "Sequence variants",
              category: ColorTheme.Category.Misc,
              factory: (context, props) => {
                const missing = Color(Number.parseInt("d8dee8", 16));
                const residueColor = (fragmentPosition: number) => Color(Number.parseInt(
                  sequenceVariantColor(
                    { resi: fragmentPosition },
                    mappingRef.current,
                    variantDensityRef.current,
                  ).slice(1),
                  16,
                ));
                const color: LocationColor = (location) => {
                  if (structureRuntime.StructureElement.Location.is(location)) {
                    if (!structureRuntime.Unit.isAtomic(location.unit)) return missing;
                    return residueColor(structureRuntime.StructureProperties.residue.auth_seq_id(location));
                  }
                  if (structureRuntime.Bond.isLocation(location)) {
                    if (!structureRuntime.Unit.isAtomic(location.aUnit)) return missing;
                    const residueLocation = structureRuntime.StructureElement.Location.create(location.aStructure);
                    residueLocation.unit = location.aUnit;
                    residueLocation.element = location.aUnit.elements[location.aIndex];
                    return residueColor(structureRuntime.StructureProperties.residue.auth_seq_id(residueLocation));
                  }
                  return missing;
                };
                return {
                  factory: SequenceVariantDensityColorThemeProvider.factory,
                  granularity: "group",
                  preferSmoothing: true,
                  color,
                  props,
                  description: "Assigns canonical residues to the Sequence Explorer variant-count buckets.",
                };
              },
              getParams: () => SequenceVariantDensityColorThemeParams,
              defaultValues: ParamDefinition.getDefaultValues(SequenceVariantDensityColorThemeParams),
              isApplicable: (context) => Boolean(context.structure),
            };
            plugin.representation.structure.themes.colorThemeRegistry.add(SequenceVariantDensityColorThemeProvider);
          },
        });
        if (!active) {
          viewer.dispose();
          return;
        }
        viewerRef.current = viewer;
        viewer.canvas3d?.setProps({ illumination: { enabled: true } });
        selectFragmentResidueRef.current = (fragmentPosition) => {
          if (fragmentPosition === null) {
            applyStructureInteractivity(viewer, { action: "select" });
            viewer.managers.structure.focus.clear();
            return;
          }

          const loadedStructure = viewer.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
          if (!loadedStructure) return;
          const loci = structureRuntime.StructureElement.Loci.fromSchema(
            loadedStructure,
            selectedElements(fragmentPosition),
          );
          if (structureRuntime.StructureElement.Loci.isEmpty(loci)) return;

          // Keep the whole-fragment surface for context, then use Mol*'s native
          // focus manager for atom-level target and neighbourhood detail.
          applyStructureInteractivity(viewer, {
            elements: selectedElements(fragmentPosition),
            action: "select",
          });
          viewer.managers.structure.focus.setFromLoci(loci);
          viewer.managers.camera.focusLoci(loci, { minRadius: 8, extraRadius: 4 });
        };

        resizeObserver = new ResizeObserver(() => {
          if (resizeFrame !== null) window.cancelAnimationFrame(resizeFrame);
          resizeFrame = window.requestAnimationFrame(() => viewer.canvas3d?.requestResize());
        });
        resizeObserver.observe(viewerHost);

        const response = await fetch(structureUrl, {
          signal: controller.signal,
          headers: { Accept: "application/gzip, application/octet-stream" },
        });
        if (!response.ok) throw new Error(`Structure download failed (${response.status}).`);
        const compressed = new Uint8Array(await response.arrayBuffer());
        if (compressed.length < 2 || compressed[0] !== 0x1f || compressed[1] !== 0x8b) {
          throw new Error("The structure response is not a valid gzip PDB file.");
        }
        const pdb = new TextDecoder().decode(await ungzip(SyncRuntimeContext, compressed));
        if (!active) return;

        const data = await viewer.builders.data.rawData({
          data: pdb,
          label: `Local AlphaFold ${fragment.fragment_label}`,
        });
        const trajectory = await viewer.builders.structure.parseTrajectory(data, "pdb");
        await viewer.builders.structure.hierarchy.applyPreset(trajectory, "default", {
          representationPreset: "coarse-surface",
          representationPresetParams: {
            ignoreHydrogens: true,
            quality: "medium",
            theme: { globalName: "plddt-confidence" },
          },
        });
        if (!active) return;

        const structure = viewer.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
        if (!structure) throw new Error("Mol* did not create a structure from the local PDB file.");
        const residues: Array<{ resi: number }> = [];
        structureRuntime.Structure.eachAtomicHierarchyElement(structure, {
          residue: (location) => {
            const position = structureRuntime.StructureProperties.residue.auth_seq_id(location);
            if (Number.isInteger(position)) residues.push({ resi: position });
          },
        });
        mappingRef.current = validateFragmentResidueMapping(fragment, residues);

        const applyColorMode = (mode: StructureColorMode) => {
          const components = viewer.managers.structure.hierarchy.current.structures.flatMap((item) => item.components);
          if (!components.length) return;
          void viewer.managers.structure.component.updateRepresentationsTheme(components, {
            color: mode === "sequence-variants" ? "sequence-variant-density" : "plddt-confidence",
            colorParams: mode === "sequence-variants"
              ? { dataRevision: variantDensityRevisionRef.current }
              : undefined,
          } as never);
        };
        applyColorModeRef.current = applyColorMode;
        applyColorMode(colorMode);

        clickSubscription = viewer.behaviors.interaction.click.subscribe(({ current }) => {
          if (!structureRuntime.StructureElement.Loci.is(current.loci)) return;
          const location = structureRuntime.StructureElement.Loci.getFirstLocation(current.loci);
          if (!location) return;
          const fragmentPosition = structureRuntime.StructureProperties.residue.auth_seq_id(location);
          const canonicalPosition = fragmentToCanonicalResidue(fragmentPosition, mappingRef.current);
          if (canonicalPosition === null) return;
          selectionCallbackRef.current(selectedPositionRef.current === canonicalPosition ? null : canonicalPosition);
        });

        const selectedPosition = selectedPositionRef.current;
        if (selectedPosition !== null) {
          const fragmentPosition = canonicalToFragmentResidue(selectedPosition, mappingRef.current);
          if (fragmentPosition !== null) {
            selectFragmentResidueRef.current(fragmentPosition);
          }
        }
        viewer.managers.camera.reset();
        setStatus({ kind: "ready" });
      } catch (error) {
        if (!active || (error instanceof DOMException && error.name === "AbortError")) return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "The structure could not be displayed.",
        });
      }
    }

    void load();

    return () => {
      active = false;
      controller.abort();
      clickSubscription?.unsubscribe();
      resizeObserver?.disconnect();
      if (resizeFrame !== null) window.cancelAnimationFrame(resizeFrame);
      viewerRef.current?.dispose();
      viewerRef.current = null;
      selectFragmentResidueRef.current = () => {};
      applyColorModeRef.current = () => {};
      viewerHost.replaceChildren();
    };
  }, [fragment, structureUrl]);

  function resetView() {
    viewerRef.current?.managers.camera.reset();
  }

  function focusSelected() {
    const viewer = viewerRef.current;
    if (!viewer || selectedCanonicalPosition === null) return;
    const fragmentPosition = canonicalToFragmentResidue(selectedCanonicalPosition, mappingRef.current);
    if (fragmentPosition === null) return;
    selectFragmentResidueRef.current(fragmentPosition);
  }

  async function toggleFullscreen() {
    const shell = shellRef.current;
    if (!shell) return;
    setFullscreenError(null);
    try {
      if (document.fullscreenElement === shell) await document.exitFullscreen();
      else await shell.requestFullscreen();
    } catch {
      setFullscreenError("Fullscreen mode is unavailable in this browser context.");
    }
  }

  const controlsDisabled = status.kind !== "ready";
  const selectedFragmentPosition = selectedCanonicalPosition === null
    ? null
    : canonicalToFragmentResidue(selectedCanonicalPosition, mappingRef.current);
  const rangeLabel = fragment.canonical_start !== null && fragment.canonical_end !== null
    ? `canonical residues ${fragment.canonical_start.toLocaleString()}–${fragment.canonical_end.toLocaleString()}`
    : "canonical range unavailable from DBREF";
  const colorModeLabel = descriptionForColorMode(colorMode);

  return <div ref={shellRef} className="structure-viewer-shell">
    <div className="structure-viewer-toolbar" aria-label={`Controls for AlphaFold ${fragment.fragment_label}`}>
      <div>
        <strong>{fragment.fragment_label}</strong>
        <span>{rangeLabel}</span>
      </div>
      <div className="structure-viewer-actions">
        <button type="button" className="quiet-button structure-action" disabled={controlsDisabled} onClick={resetView}><RotateCcw aria-hidden="true" size={16} />Reset view</button>
        <button type="button" className="quiet-button structure-action" disabled={!fullscreenSupported} aria-pressed={fullscreen} onClick={() => void toggleFullscreen()}>{fullscreen ? <Minimize2 aria-hidden="true" size={16} /> : <Maximize2 aria-hidden="true" size={16} />}{fullscreen ? "Exit fullscreen" : "Fullscreen"}</button>
        <a className="quiet-button structure-download-link structure-action" href={downloadUrl}><Download aria-hidden="true" size={16} />Download PDB</a>
      </div>
      {fullscreenError && <span className="structure-control-error" role="alert">{fullscreenError}</span>}
    </div>

    <div className="structure-color-controls" role="group" aria-label="Molecular surface color mode">
      <span>Color by</span>
      <button type="button" className="quiet-button structure-color-mode" aria-pressed={colorMode === "sequence-variants"} onClick={() => setColorMode("sequence-variants")}>Sequence variants</button>
      <button type="button" className="quiet-button structure-color-mode" aria-pressed={colorMode === "plddt-confidence"} onClick={() => setColorMode("plddt-confidence")}>AlphaFold confidence</button>
    </div>

    <div className="structure-representation-note">
      <strong>AlphaFold-style molecular surface</strong>
      <span>{colorMode === "sequence-variants" ? "Canonical Sequence variant-count colours are shown on a non-ribbon molecular surface; selecting a residue focuses its atomic neighbourhood." : "Local pLDDT confidence colours are shown on a non-ribbon molecular surface; selecting a residue focuses its atomic neighbourhood."}</span>
    </div>

    <div className={`structure-selection-bar ${selectedCanonicalPosition === null ? "is-idle" : selectedFragmentPosition === null ? "is-unmapped" : "is-selected"}`} role="status">
      <Crosshair aria-hidden="true" size={19} />
      <div>
        {selectedCanonicalPosition === null
          ? <><strong>No residue selected</strong><span>Select a site in Sequence, or click the molecular surface, to link the evidence views.</span></>
          : status.kind === "loading"
            ? <><strong>Canonical residue {selectedCanonicalPosition.toLocaleString()}</strong><span>Waiting for the local model before validating its fragment mapping.</span></>
            : status.kind === "no-webgl"
              ? <><strong>Canonical residue {selectedCanonicalPosition.toLocaleString()}</strong><span>The fragment metadata covers this site, but this browser cannot validate or display the 3D mapping without WebGL.</span></>
              : status.kind === "error"
                ? <><strong>Canonical residue {selectedCanonicalPosition.toLocaleString()}</strong><span>The model did not load, so its residue mapping could not be validated.</span></>
                : selectedFragmentPosition === null
                  ? <><strong>Canonical residue {selectedCanonicalPosition.toLocaleString()}</strong><span>This residue is outside the validated mapping for this fragment.</span></>
                  : <><strong>Canonical residue {selectedCanonicalPosition.toLocaleString()} · fragment residue {selectedFragmentPosition.toLocaleString()}</strong><span>Selection is a navigation highlight only; it does not encode evidence or effect.</span></>}
      </div>
      {selectedCanonicalPosition !== null && <div className="structure-selection-actions">
        <button type="button" className="quiet-button structure-action" disabled={controlsDisabled || selectedFragmentPosition === null} onClick={focusSelected}><LocateFixed aria-hidden="true" size={16} />Focus selected</button>
        <button type="button" className="quiet-button structure-action" aria-label="Clear selected residue" onClick={() => onSelectCanonicalPosition(null)}><X aria-hidden="true" size={16} />Clear selection</button>
      </div>}
    </div>

    <div className="structure-viewer-stage">
      <div className="structure-stage-caption" aria-hidden="true">
        <strong>{colorModeLabel}</strong>
        <span>local AlphaFold model · {selectedFragmentPosition !== null ? `canonical ${selectedCanonicalPosition?.toLocaleString()} selected` : "no residue selected"}</span>
      </div>
      <div
        ref={hostRef}
        className="structure-viewer-canvas"
        role="img"
        aria-label={`Interactive AlphaFold predicted molecular surface for ${fragment.fragment_label}, ${rangeLabel}. Use pointer drag to rotate and wheel or pinch to zoom.`}
      />
      {status.kind === "loading" && <div className="structure-viewer-state" role="status"><strong>Loading 3D structure</strong><span>Retrieving and preparing the local compressed PDB model.</span></div>}
      {status.kind === "no-webgl" && <div className="structure-viewer-state structure-viewer-error" role="alert"><strong>3D view unavailable</strong><span>This browser does not provide WebGL. The model can still be downloaded.</span></div>}
      {status.kind === "error" && <div className="structure-viewer-state structure-viewer-error" role="alert"><strong>Structure could not be displayed</strong><span>{status.message} The PDB download remains available.</span></div>}
    </div>

    <div className="structure-viewer-footer">
      {colorMode === "sequence-variants"
        ? <>
            <ul className="structure-confidence-legend" aria-label="Sequence residue variant-count legend">
              {SEQUENCE_VARIANT_BANDS.map((band) => <li key={band.key}><i style={{ backgroundColor: band.color }} /><span><strong>{band.label}</strong></span></li>)}
            </ul>
            {variantDensityStatus === "loading" && <p role="status">Loading the bounded canonical variant-density summary for this surface.</p>}
            {variantDensityStatus === "error" && <p className="structure-colour-warning" role="alert">Canonical variant-density colors are unavailable: {variantDensityError}</p>}
            {variantDensityStatus === "ready" && <p>Uses the same six Sequence Explorer buckets for unique canonical drawable variant records anchored at each record’s minimum canonical start. This surface color does not encode pathogenicity, clinical consensus, or ClinVar P/LP presence.</p>}
          </>
        : <>
            <ul className="structure-confidence-legend" aria-label="AlphaFold pLDDT confidence legend">
              {PLDDT_BANDS.map((band) => <li key={band.label}><i style={{ backgroundColor: band.color }} /><span><strong>{band.label}</strong> {band.range}</span></li>)}
            </ul>
            <p>pLDDT is read from the local AlphaFold PDB B-factor field. Higher values indicate greater confidence in the predicted local geometry; they are not experimental B-factors.</p>
          </>}
      {!mappingRef.current.valid && status.kind === "ready" && <p className="structure-colour-warning" role="alert">This fragment could not be validated against its DBREF canonical range; residue selection is disabled rather than guessed.</p>}
      <p className="structure-pointer-help">Click a residue to select it; click it again to clear · drag to rotate · wheel or pinch to zoom · use Reset view to refit the full fragment.</p>
    </div>
  </div>;
}
