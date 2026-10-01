import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Check,
  Dna,
  Plus,
  RotateCcw,
  Trash2,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { api, number, params } from '../api';
import { HelpButton } from './HelpGuide';
import { AviTrack } from './AlphaGenomeAvi';
import { QtlPicker, QtlTrack, type QtlDataset } from './AlphaGenomeQtl';
import { GenomicAxis } from './AlphaGenomeAxis';
import { TrackCard, SignalGroupCard } from './AlphaGenomeReferenceTracks';
import {
  modes,
  contextName,
  sceneKey,
  details,
  colorStyle,
  modeInfo,
  signalModality,
  type Track,
  type Gene,
  type Tile,
  type Catalog,
  type ManeModel,
  type TranscriptFeature,
} from './alphagenome-model';
import {
  brushAtPixel,
  formatInterval as location,
  plotBounds,
  pointerPosition,
  type GenomicView as View,
} from './genomic-coordinates';
import './alphagenome-expression.css';

const normalized = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
const counted = (count: number, singular: string, plural = singular + 's') =>
  `${count.toLocaleString()} ${count === 1 ? singular : plural}`;

function AlphaGenomeGuide({ snapshot }: { snapshot?: string }) {
  return (
    <>
      <div className="help-sections">
        <section>
          <h3>Compare a biosample across modalities</h3>
          <p>
            Choose a biosample first, then a modality and a specific assay
            track. Add more tracks without losing that biosample. Splice-site
            predictions are shared and have a separate entry.
          </p>
        </section>
        <section>
          <h3>Two kinds of prediction</h3>
          <p>
            AVI shows variant impact scores for current gene-associated project
            SNVs. It is independent of the selected biosample, and PHRED is not
            a pathogenicity probability. The other tracks predict the reference
            sequence; they are not measurements or alternate-allele effects.
          </p>
        </section>
        <section>
          <h3>Coordinates and resolution</h3>
          <p>
            All tracks use GRCh38 and the same visible interval. Coordinates
            shown here are 1-based. Wheel over the coordinate axis or drag the
            Pan slider to browse while keeping the current zoom. Click a
            transcript block to focus its source interval, or choose a CDS exon
            to focus its coding interval. Zoom requests finer data down to the
            source resolution. Means and maxima describe display bins; axes and
            units remain independent between assays. Missing values are not
            zero.
          </p>
        </section>
        <section>
          <h3>MANE Select transcript structure</h3>
          <p>
            Blue blocks mark coding sequence (CDS), gray blocks mark
            source-annotated UTR, and rose marks the separately annotated stop
            codon. Exon outlines share one line; arrows in the connecting
            introns show transcription direction. All features come from the
            same versioned MANE Select representative in MANE 1.5. Source UTR
            and stop-codon annotations can overlap; the stop codon is drawn on
            top. The versioned transcript is shown beside the axis. Missing MANE
            models are labelled explicitly. A gene-linked CDS does not establish
            an exact match to this UniProt protein or isoform.
          </p>
        </section>
        <section>
          <h3>Overlay signals</h3>
          <p>
            Selected one-dimensional tracks from the same biosample and modality
            share a panel and an original-value axis. Each assay or strand keeps
            its own curve, color and inspected values. Use the legend to hide or
            show a curve, or turn off Overlay same modality for separate panels.
            Signals are not summed, normalized or strand-flipped; differences
            between assays can affect their scales.
          </p>
        </section>
        <section>
          <h3>GTEx QTL tracks</h3>
          <p>
            GTEx v11 tissues are selected independently of AlphaGenome
            biosamples; samples are not matched. Tracks show variant–phenotype
            associations in the current model window. QTLs may occur outside
            this window. The vertical axis is −log₁₀(P), not effect size;
            original P, slope and phenotype remain in each track’s details.
            Coordinates are 1-based on screen; track scales are independent.
          </p>
        </section>
        <section>
          <h3>Coverage and interpretation</h3>
          <p>
            Blank AVI positions are not evidence of low impact. Same-position
            alternate alleles remain separate records. Feature contributions are
            displayed with their original sign and are not summed to reconstruct
            AVI. Overlapping model windows are inspected separately. Contact
            colors are centered on zero; splice junctions use explicit pages
            rather than a highest-score subset.
          </p>
        </section>
      </div>
      <h3>Modalities</h3>
      <div className="help-modality-grid">
        {Object.entries(modes).map(([id, m]) => (
          <section key={id} style={colorStyle(m.color)}>
            <h3>{m.label}</h3>
            <p>{m.help}</p>
          </section>
        ))}
      </div>
      <div className="help-sources">
        <a
          href="https://www.alphagenomedocs.com/exploring_model_metadata.html"
          target="_blank"
          rel="noreferrer"
        >
          Official modality definitions ↗
        </a>
      </div>
      {snapshot && <p>Reference snapshot: {snapshot}</p>}
    </>
  );
}
const retainedStart = (tile: Tile) => tile.retention_start_0based ?? tile.window_start_0based;
const retainedEnd = (tile: Tile) => tile.retention_end_0based ?? tile.window_end_0based;
function initialView(gene: Gene, tile: Tile): View {
  if (retainedStart(tile) !== tile.window_start_0based || retainedEnd(tile) !== tile.window_end_0based) {
    return [retainedStart(tile), retainedEnd(tile)];
  }
  const pad = Math.max(
    1000,
    (gene.gene_end_1based_inclusive - gene.gene_start_1based) * 0.08
  );
  const start = Math.max(
      retainedStart(tile),
      Math.floor(gene.gene_start_1based - 1 - pad)
    ),
    end = Math.min(
      retainedEnd(tile),
      Math.ceil(gene.gene_end_1based_inclusive + pad)
    );
  return start < end
    ? [start, end]
    : [retainedStart(tile), retainedEnd(tile)];
}

/** A slider draft stays local; tracks and their shared axis use one committed view. */
function GenomicNavigator({ tile, view, windowCds, onCommit, onFocusFeature }: {
  tile: Tile;
  view: View;
  windowCds: TranscriptFeature[];
  onCommit: (view: View) => void;
  onFocusFeature: (feature: TranscriptFeature) => void;
}) {
  const [previewStart, setPreviewStart] = useState<number | null>(null);
  const draft = useRef<number | null>(null);
  const viewSpan = view[1] - view[0];
  const windowSpan = retainedEnd(tile) - retainedStart(tile);
  const cropped = retainedStart(tile) !== tile.window_start_0based || retainedEnd(tile) !== tile.window_end_0based;
  const fullRangeLabel = cropped ? 'Full saved range' : 'Full window';
  const cancel = () => {
    draft.current = null;
    setPreviewStart(null);
  };
  useEffect(cancel, [tile.tile_id, view[0], view[1]]);
  const commit = () => {
    const start = draft.current;
    cancel();
    if (start !== null && start !== view[0]) onCommit([start, start + viewSpan]);
  };
  return (
    <div className="agx-region-nav">
      {windowCds.length > 0 && (
        <label className="agx-exon-picker">
          <span className="agx-cds-nav-label">Explore CDS</span>
          <select
            aria-label="Jump to MANE CDS exon"
            value=""
            onChange={(e) => {
              const block = windowCds[Number(e.target.value)];
              if (block) onFocusFeature(block);
            }}
          >
            <option value="" disabled>
              Jump to coding region…
            </option>
            {windowCds.map((b, i) => (
              <option key={b.start_0based} value={i}>
                Exon {b.exon_number} ·{' '}
                {location(b.start_0based, b.end_0based)}
              </option>
            ))}
          </select>
        </label>
      )}
      <label className="agx-pan-picker">
        <span>Pan</span>
        <input
          type="range"
          aria-label={cropped ? 'Pan genomic region within saved range' : 'Pan genomic region within model window'}
          aria-valuetext={`${tile.chromosome}:${location(previewStart ?? view[0], (previewStart ?? view[0]) + viewSpan)}`}
          title={cropped ? 'Drag to browse the saved range while keeping this zoom level' : 'Drag to browse the model window while keeping this zoom level'}
          min={retainedStart(tile)}
          max={retainedEnd(tile) - viewSpan}
          step={1}
          value={previewStart ?? view[0]}
          disabled={viewSpan >= windowSpan}
          onChange={(e) => {
            const start = Number(e.target.value);
            draft.current = start;
            setPreviewStart(start);
          }}
          onPointerDown={(e) => e.currentTarget.setPointerCapture(e.pointerId)}
          onPointerUp={commit}
          onKeyUp={commit}
          onBlur={commit}
          onPointerCancel={cancel}
        />
        <span className="agx-pan-hint">
          {viewSpan >= windowSpan ? fullRangeLabel : 'Drag to browse'}
        </span>
      </label>
      <output className="agx-pan-preview" aria-live="off">
        {previewStart !== null
          ? `Preview ${tile.chromosome}:${location(previewStart, previewStart + viewSpan)} · release to apply`
          : `${tile.chromosome}:${location(view[0], view[1])}`}
      </output>
    </div>
  );
}
function Workspace({
  catalog,
  accession,
  expressionContext,
}: {
  catalog: Catalog;
  accession: string;
  expressionContext: string;
}) {
  const initial = catalog.genes.find((g) => g.tiles.length > 0)!;
  const [geneId, setGeneId] = useState(initial.ensembl_gene_id),
    [tileId, setTileId] = useState(initial.tiles[0].tile_id),
    [selected, setSelected] = useState<string[]>([]),
    [scene, setScene] = useState(''),
    [mode, setMode] = useState(''),
    [search, setSearch] = useState(''),
    [library, setLibrary] = useState(true),
    [view, setView] = useState<View>(initialView(initial, initial.tiles[0])),
    [position, setPosition] = useState<number | null>(null);
  const gene =
      catalog.genes.find((g) => g.ensembl_gene_id === geneId) ?? initial,
    tile = gene.tiles.find((t) => t.tile_id === tileId) ?? gene.tiles[0];
  const [overlay, setOverlay] = useState(true);
  const [qtlLibrary, setQtlLibrary] = useState(false),
    [qtlSelected, setQtlSelected] = useState<QtlDataset[]>([]);
  useEffect(() => {
    setQtlSelected([]);
  }, [geneId]);
  const cdsQuery = useQuery({
    queryKey: ['alphagenome-mane-cds', accession, geneId],
    queryFn: ({ signal }) =>
      api<ManeModel>(
        `/proteins/${accession}/expression/alphagenome/cds?${params({ gene: geneId })}`,
        signal
      ),
    staleTime: 300000,
    retry: 1,
  });
  const [hoverPosition, setHoverPosition] = useState<number | null>(null),
    [brush, setBrush] = useState<View | null>(null);
  const drag = useRef<{
      pointer: number;
      startX: number;
      left: number;
      width: number;
      origin: View;
      anchor: number;
      active: boolean;
      element: Element;
    } | null>(null),
    suppressClick = useRef(false);
  useEffect(() => {
    setHoverPosition(null);
    setBrush(null);
    const current = drag.current;
    drag.current = null;
    if (current?.element.hasPointerCapture(current.pointer))
      current.element.releasePointerCapture(current.pointer);
  }, [geneId, tileId, view[0], view[1]]);
  const cancelBrush = () => {
    const current = drag.current;
    drag.current = null;
    if (current?.element.hasPointerCapture(current.pointer))
      current.element.releasePointerCapture(current.pointer);
    setBrush(null);
    setHoverPosition(null);
  };
  const beginBrush = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0 || !event.isPrimary) return;
    const plot = (event.target as Element).closest(
      'svg.agx-axis, svg.agx-signal, canvas.agx-avi-canvas, svg.agx-junctions'
    );
    if (!plot) return;
    const anchor = pointerPosition(plot, event.clientX, view);
    if (anchor === null) return;
    const bounds = plotBounds(plot);
    suppressClick.current = false;
    drag.current = {
      pointer: event.pointerId,
      startX: event.clientX,
      left: bounds.left,
      width: bounds.width,
      origin: [...view],
      anchor: anchor - 1,
      active: false,
      element: plot,
    };
  };
  const moveBrush = (event: ReactPointerEvent<HTMLDivElement>) => {
    const current = drag.current;
    if (!current || current.pointer !== event.pointerId) return;
    if (!(event.buttons & 1)) {
      cancelBrush();
      return;
    }
    if (!current.active && Math.abs(event.clientX - current.startX) < 6) return;
    if (!current.active) {
      current.active = true;
      current.element.setPointerCapture(event.pointerId);
    }
    const selection = brushAtPixel(
      current.anchor,
      event.clientX - current.left,
      current.width,
      current.origin
    );
    setBrush(selection.interval);
    setHoverPosition(selection.position);
    event.preventDefault();
  };
  const endBrush = (event: ReactPointerEvent<HTMLDivElement>) => {
    const current = drag.current;
    if (!current || current.pointer !== event.pointerId) return;
    drag.current = null;
    if (current.active) {
      const {
        interval: [low, high],
      } = brushAtPixel(
        current.anchor,
        event.clientX - current.left,
        current.width,
        current.origin
      );
      const span = Math.min(
        retainedEnd(tile) - retainedStart(tile),
        Math.max(32, high - low)
      );
      const start = Math.max(
        retainedStart(tile),
        Math.min(
          retainedEnd(tile) - span,
          Math.floor((low + high - span) / 2)
        )
      );
      suppressClick.current = true;
      setView([start, start + span]);
      setHoverPosition(null);
      event.preventDefault();
    }
    setBrush(null);
    if (current.element.hasPointerCapture(event.pointerId))
      current.element.releasePointerCapture(event.pointerId);
  };
  const resetTracks = () => {
    setSelected([]);
    setScene('');
    setMode('');
    setSearch('');
    setLibrary(true);
  };

  const shared = (t: Track) =>
    (catalog.shared_modalities ?? ['splice_sites']).includes(t.modality);
  const biosamples = [
    ...new Map(
      catalog.tracks
        .filter((t) => !shared(t) && sceneKey(t))
        .map((t) => [
          sceneKey(t),
          { id: sceneKey(t), name: contextName(t), type: t.biosample_type },
        ])
    ).values(),
  ].sort((a, b) => a.name.localeCompare(b.name));
  const contextTracks = catalog.tracks.filter((t) =>
      scene === 'shared' ? shared(t) : !shared(t) && sceneKey(t) === scene
    ),
    availableModes = [...new Set(contextTracks.map((t) => t.modality))],
    activeMode = availableModes.includes(mode)
      ? mode
      : (availableModes[0] ?? '');
  const available = contextTracks.filter(
    (t) =>
      t.modality === activeMode &&
      normalized(
        [contextName(t), details(t), t.name, t.ontology_curie].join(' ')
      ).includes(normalized(search))
  );
  const panels = useMemo(() => {
    const groups: { key: string; tracks: Track[] }[] = [];
    for (const id of selected) {
      const t = catalog.tracks.find((t) => t.track_id === id);
      if (!t) continue;
      const key =
        overlay && signalModality(t)
          ? `${sceneKey(t)}:${t.modality}:${t.display_unit}`
          : t.track_id;
      const existing = groups.find((g) => g.key === key);
      if (existing) existing.tracks.push(t);
      else groups.push({ key, tracks: [t] });
    }
    return groups;
  }, [selected, catalog.tracks, overlay]);
  const removeIds = (ids: string[]) =>
    setSelected((current) => current.filter((id) => !ids.includes(id)));
  const movePanel = (index: number, delta: number) => {
    const next = [...panels];
    [next[index], next[index + delta]] = [next[index + delta], next[index]];
    setSelected(next.flatMap((p) => p.tracks.map((t) => t.track_id)));
  };
  const matches = catalog.tracks.filter(
    (t) =>
      !shared(t) &&
      expressionContext &&
      [t.gtex_tissue, t.biosample_name].some(
        (name) => name && normalized(name) === normalized(expressionContext)
      )
  );
  const add = (id: string) =>
    setSelected((current) =>
      current.includes(id) ? current.filter((v) => v !== id) : [...current, id]
    );
  const changeScene = (id: string) => {
    setScene(id);
    setMode('');
    setSearch('');
  };
  const changeGene = (id: string) => {
    const g = catalog.genes.find((g) => g.ensembl_gene_id === id)!;
    setGeneId(id);
    setTileId(g.tiles[0].tile_id);
    setView(initialView(g, g.tiles[0]));
    setPosition(null);
  };
  const panFraction = useCallback(
    (fraction: number) => {
      setHoverPosition(null);
      setView((current) => {
        const span = current[1] - current[0],
          left = Math.round(
            Math.max(
              retainedStart(tile),
              Math.min(
                retainedEnd(tile) - span,
                current[0] + fraction * span
              )
            )
          );
        return left === current[0] ? current : [left, left + span];
      });
    },
    [retainedStart(tile), retainedEnd(tile)]
  );
  const focusFeature = (block: TranscriptFeature) => {
    const span = Math.min(
      retainedEnd(tile) - retainedStart(tile),
      Math.max(200, Math.ceil((block.end_0based - block.start_0based) * 1.6))
    );
    const left = Math.max(
      retainedStart(tile),
      Math.min(
        retainedEnd(tile) - span,
        Math.floor((block.start_0based + block.end_0based - span) / 2)
      )
    );
    setHoverPosition(null);
    setView([left, left + span]);
  };
  const cropped = retainedStart(tile) !== tile.window_start_0based || retainedEnd(tile) !== tile.window_end_0based;
  const fullRangeLabel = cropped ? 'Full saved range' : 'Full window';
  const windowSpan = retainedEnd(tile) - retainedStart(tile),
    viewSpan = view[1] - view[0];
  const windowCds =
    cdsQuery.data?.segments
      .filter(
        (b) =>
          b.feature === 'CDS' &&
          b.start_0based < retainedEnd(tile) &&
          b.end_0based > retainedStart(tile)
      )
      .sort((a, b) => a.exon_number - b.exon_number) ?? [];
  const zoom = (factor: number) => {
    const span = Math.round(
        Math.min(
          retainedEnd(tile) - retainedStart(tile),
          Math.max(32, (view[1] - view[0]) * factor)
        )
      ),
      left = Math.round(
        Math.max(
          retainedStart(tile),
          Math.min(
            retainedEnd(tile) - span,
            (view[0] + view[1] - span) / 2
          )
        )
      );
    setView([left, left + span]);
  };
  const focusVariant = (position1: number) => {
    const span = Math.min(
        200,
        retainedEnd(tile) - retainedStart(tile)
      ),
      start = Math.round(
        Math.max(
          retainedStart(tile),
          Math.min(retainedEnd(tile) - span, position1 - 1 - span / 2)
        )
      );
    setView([start, start + span]);
  };
  const pan = (direction: number) => {
    const span = view[1] - view[0],
      left = Math.round(
        Math.max(
          retainedStart(tile),
          Math.min(
            retainedEnd(tile) - span,
            view[0] + direction * span * 0.5
          )
        )
      );
    setView([left, left + span]);
  };
  return (
    <>
      {expressionContext && (
        <div className="agx-context-link">
          <Activity size={16} />
          <span>
            Measured context: <strong>{expressionContext}</strong> ·{' '}
            {matches.length
              ? 'Matching source label; samples are not matched.'
              : 'No matching prediction label.'}
          </span>
          {matches.length > 0 && (
            <button
              onClick={() => {
                changeScene(sceneKey(matches[0]));
                setLibrary(true);
              }}
            >
              Use this biosample
            </button>
          )}
        </div>
      )}
      <div className="agx-toolbar">
        <div className="agx-fixed-gene">
          {catalog.genes.filter((g) => g.tiles.length).length > 1 ? (
            <label>
              Linked gene
              <select
                aria-label="AlphaGenome linked gene"
                value={geneId}
                onChange={(e) => changeGene(e.target.value)}
              >
                {catalog.genes
                  .filter((g) => g.tiles.length)
                  .map((g) => (
                    <option key={g.ensembl_gene_id} value={g.ensembl_gene_id}>
                      {g.gene_symbol} · {g.ensembl_gene_id}
                    </option>
                  ))}
              </select>
            </label>
          ) : (
            <>
              <Dna size={18} />
              <strong>{gene.gene_symbol}</strong>
              <span>{gene.ensembl_gene_id} · GRCh38</span>
            </>
          )}
          {gene.tiles.length > 1 && (
            <label>
              Model window
              <select
                aria-label="AlphaGenome model window"
                value={tile.tile_id}
                onChange={(e) => {
                  const next = gene.tiles.find(
                    (t) => t.tile_id === e.target.value
                  )!;
                  setTileId(next.tile_id);
                  setView(initialView(gene, next));
                }}
              >
                {gene.tiles.map((t, i) => (
                  <option key={t.tile_id} value={t.tile_id}>
                    {i + 1} / {gene.tiles.length} ·{' '}
                    {location(retainedStart(t), retainedEnd(t))}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        {(retainedStart(tile) !== tile.window_start_0based || retainedEnd(tile) !== tile.window_end_0based) && (
          <span title={`Original model input: ${location(tile.window_start_0based, tile.window_end_0based)}`}>
            Saved range: {location(retainedStart(tile), retainedEnd(tile))}. Outside this range is not stored.
          </span>
        )}
        <div className="agx-toolbar-actions">
          <button
            className="agx-icon-reset"
            title="Reset reference tracks and choose again"
            aria-label="Reset reference tracks and choose again"
            onClick={resetTracks}
          >
            <RotateCcw size={16} />
          </button>
          <button
            className="agx-primary"
            aria-expanded={library}
            onClick={() => setLibrary(!library)}
          >
            <Plus size={16} />
            Add tracks
          </button>
        </div>
      </div>
      {library && (
        <div className="agx-library">
          <div className="agx-library-heading">
            <h4>Add reference tracks</h4>
            <button
              aria-label="Close track library"
              onClick={() => setLibrary(false)}
            >
              <X size={17} />
            </button>
          </div>
          <div className="agx-picker-controls">
            <label className="agx-selector">
              <span>Biosample</span>
              <select
                aria-label="AlphaGenome biosample"
                data-selected={Boolean(scene)}
                value={scene}
                onChange={(e) => changeScene(e.target.value)}
              >
                <option value="" disabled>
                  Select tissue or cell…
                </option>
                {biosamples.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
                <option value="shared">
                  Shared predictions · no biosample
                </option>
              </select>
            </label>
            <label className="agx-selector">
              <span>Modality</span>
              <select
                aria-label="AlphaGenome modality"
                disabled={!scene}
                data-selected={Boolean(activeMode)}
                value={activeMode}
                onChange={(e) => {
                  setMode(e.target.value);
                  setSearch('');
                }}
              >
                {!scene && <option value="">Select biosample first</option>}
                {availableModes.map((id) => (
                  <option key={id} value={id}>
                    {modeInfo(id).label} ·{' '}
                    {counted(
                      contextTracks.filter((t) => t.modality === id).length,
                      'track'
                    )}
                  </option>
                ))}
              </select>
            </label>
            <label className="agx-track-search">
              <span>Find signal</span>
              <input
                aria-label="Search AlphaGenome tracks"
                disabled={!scene}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Assay, mark or strand"
              />
            </label>
          </div>
          {scene ? (
            <div className="agx-library-results">
              {available.map((t) => (
                <div key={t.track_id} className="agx-candidate">
                  <div>
                    <strong>{details(t) || t.name}</strong>
                    <span>{t.data_source || 'Reference prediction'}</span>
                  </div>
                  <button
                    className="agx-track-toggle"
                    aria-pressed={selected.includes(t.track_id)}
                    onClick={() => add(t.track_id)}
                    aria-label={`${selected.includes(t.track_id) ? 'Remove' : 'Add'} ${t.track_id}`}
                  >
                    {selected.includes(t.track_id) ? (
                      <Check size={15} />
                    ) : (
                      <Plus size={15} />
                    )}{' '}
                    {selected.includes(t.track_id) ? 'Added' : 'Add'}
                  </button>
                </div>
              ))}
              {!available.length && <p>No matching signal.</p>}
            </div>
          ) : (
            <p className="agx-selection-prompt">
              Select a biosample to browse its prediction tracks.
            </p>
          )}
        </div>
      )}

      <div className="agx-qtl-entry">
        <button
          aria-expanded={qtlLibrary}
          onClick={() => setQtlLibrary(!qtlLibrary)}
        >
          <Plus size={16} />
          Add QTL
        </button>
        <span>GTEx associations</span>
      </div>
      {qtlLibrary && (
        <QtlPicker
          key={geneId}
          accession={accession}
          gene={geneId}
          selected={qtlSelected}
          onChange={setQtlSelected}
          onClose={() => setQtlLibrary(false)}
        />
      )}
      <div className="agx-locus">
        <div>
          <strong>
            {tile.chromosome}:{location(view[0], view[1])}
          </strong>
          <span>{number(view[1] - view[0], 0)} bp · GRCh38</span>
        </div>
        <div className="agx-viewport">
          <button
            className="agx-icon-reset"
            aria-label="Reset genomic view to gene region"
            title="Reset view to gene region"
            onClick={() => {
              cancelBrush();
              setView(initialView(gene, tile));
            }}
          >
            <RotateCcw size={15} />
          </button>
          <button onClick={() => setView(initialView(gene, tile))}>
            Gene region
          </button>
          <button
            aria-label="Pan genomic window left"
            disabled={view[0] <= retainedStart(tile)}
            onClick={() => pan(-1)}
          >
            ←
          </button>
          <button
            aria-label="Zoom in genomic window"
            onClick={() => zoom(0.5)}
            disabled={view[1] - view[0] <= 32}
          >
            <ZoomIn size={15} />
          </button>
          <button
            aria-label="Zoom out genomic window"
            onClick={() => zoom(2)}
            disabled={
              view[1] - view[0] >=
              retainedEnd(tile) - retainedStart(tile)
            }
          >
            <ZoomOut size={15} />
          </button>
          <button
            aria-label="Pan genomic window right"
            disabled={view[1] >= retainedEnd(tile)}
            onClick={() => pan(1)}
          >
            →
          </button>
          <button
            onClick={() =>
              setView([retainedStart(tile), retainedEnd(tile)])
            }
          >
            {fullRangeLabel}
          </button>
        </div>
      </div>
      {cropped && (
        <p className="agx-axis-hint">
          Saved range: full Ensembl gene + 10 kb each side, within this window.
          {' '}Structure: MANE Select transcript.
        </p>
      )}
      <p className="agx-axis-hint">
        Drag to zoom · scroll axis to pan · click an exon to focus
      </p>
      <div
        className="agx-stack"
        onPointerDownCapture={beginBrush}
        onPointerMoveCapture={moveBrush}
        onPointerUpCapture={endBrush}
        onPointerCancel={cancelBrush}
        onLostPointerCapture={() => {
          if (drag.current) cancelBrush();
        }}
        onClickCapture={(e) => {
          if (suppressClick.current) {
            suppressClick.current = false;
            e.preventDefault();
            e.stopPropagation();
          }
        }}
        onKeyDownCapture={(e) => {
          if (e.key === 'Escape') {
            cancelBrush();
            e.preventDefault();
          }
        }}
      >
        {cdsQuery.error && (
          <div className="agx-error">
            MANE CDS could not be loaded.
            <button onClick={() => cdsQuery.refetch()}>Retry CDS</button>
          </div>
        )}
        <GenomicAxis
          view={view}
          gene={gene}
          chromosome={tile.chromosome}
          position={position}
          hoverPosition={hoverPosition}
          onHover={setHoverPosition}
          brush={brush}
          cds={cdsQuery.data}
          canPan={viewSpan < windowSpan}
          onPan={panFraction}
          onFocusFeature={focusFeature}
        />
        <GenomicNavigator
          tile={tile}
          view={view}
          windowCds={windowCds}
          onCommit={setView}
          onFocusFeature={focusFeature}
        />
        <AviTrack
          accession={accession}
          gene={gene}
          tile={tile}
          view={view}
          position={position}
          hoverPosition={hoverPosition}
          onHover={setHoverPosition}
          brush={brush}
          onPosition={setPosition}
          onFocusVariant={focusVariant}
        />
        {qtlSelected.map((d) => (
          <QtlTrack
            key={`${geneId}:${d.dataset_id}:${view.join(':')}`}
            accession={accession}
            gene={geneId}
            dataset={d}
            chromosome={tile.chromosome}
            view={view}
            hoverPosition={hoverPosition ?? position}
            onHover={setHoverPosition}
            onRemove={() => {
              setHoverPosition(null);
              setQtlSelected((items) =>
                items.filter((i) => i.dataset_id !== d.dataset_id)
              );
            }}
          />
        ))}
        {panels.map((panel, index) => {
          const t = panel.tracks[0],
            common = {
              accession,
              gene,
              tile,
              view,
              position,
              hoverPosition,
              onHover: setHoverPosition,
              brush,
              index,
              total: panels.length,
              onRemove: () => removeIds(panel.tracks.map((t) => t.track_id)),
              onMove: (delta: number) => movePanel(index, delta),
            };
          return signalModality(t) ? (
            <SignalGroupCard
              key={`${geneId}:${tileId}:${panel.key}`}
              {...common}
              tracks={panel.tracks}
              catalogTracks={catalog.tracks}
              onRemoveSeries={(id) => removeIds([id])}
            />
          ) : (
            <TrackCard
              key={`${geneId}:${tileId}:${panel.key}`}
              {...common}
              track={t}
            />
          );
        })}
      </div>
      <div className="agx-stack-heading">
        <span>
          {counted(selected.length, 'signal')} ·{' '}
          {counted(panels.length, 'reference panel')} ·{' '}
          {counted(qtlSelected.length, 'QTL track')}
        </span>
        <button aria-pressed={overlay} onClick={() => setOverlay(!overlay)}>
          Overlay same modality
        </button>
        {selected.length > 0 && (
          <button onClick={() => setSelected([])}>
            <Trash2 size={13} />
            Clear reference tracks
          </button>
        )}
        <button onClick={() => setLibrary(true)}>
          <Plus size={14} />
          Add track
        </button>
      </div>
      <p className="agx-footnote">GRCh38 · independent track scales</p>
    </>
  );
}
export function AlphaGenomeExpression({
  accession,
  expressionContext = '',
}: {
  accession: string;
  expressionContext?: string;
}) {
  const query = useQuery({
      queryKey: ['expression-alphagenome', accession],
      queryFn: ({ signal }) =>
        api<Catalog>(`/proteins/${accession}/expression/alphagenome`, signal),
      staleTime: 300000,
      retry: 1,
    }),
    data = query.data;
  return (
    <section
      id="alphagenome"
      className="agx"
      aria-label="AlphaGenome and AVI genomic tracks"
    >
      <span
        id="expression-predictions"
        className="agx-legacy-anchor"
        aria-hidden="true"
      />
      <header className="agx-heading">
        <div>
          <h2>
            AlphaGenome <span>& AVI</span>{' '}
            <HelpButton title="AlphaGenome & AVI guide" label="Guide">
              <AlphaGenomeGuide snapshot={data?.snapshot} />
            </HelpButton>
          </h2>
          <p>Reference predictions, variant scores and GTEx associations.</p>
        </div>
      </header>
      {data && (
        <div className="agx-stats">
          <span>
            <b>
              {
                new Set(
                  data.tracks.map((t) => t.ontology_curie).filter(Boolean)
                ).size
              }
            </b>{' '}
            biosamples
          </span>
          <span>
            <b>{new Set(data.tracks.map((t) => t.modality)).size}</b>{' '}
            {new Set(data.tracks.map((t) => t.modality)).size === 1
              ? 'modality'
              : 'modalities'}
          </span>
          <span>
            <b>{data.tracks.length.toLocaleString()}</b> reference{' '}
            {data.tracks.length === 1 ? 'track' : 'tracks'}
          </span>
        </div>
      )}
      {query.error ? (
        <div className="agx-error" role="alert">
          {query.error.message}
          <button onClick={() => query.refetch()}>Retry predictions</button>
        </div>
      ) : !data ? (
        <div className="agx-loading">Loading prediction contexts…</div>
      ) : !data.available || !data.genes.some((g) => g.tiles.length) ? (
        <div className="agx-empty">
          <strong>No reference prediction available for this gene.</strong>
          {data.genes.map((g) => (
            <span key={g.ensembl_gene_id}>
              {g.gene_symbol} ·{' '}
              {(g.prediction_status ?? g.status ?? 'not available').replaceAll(
                '_',
                ' '
              )}
            </span>
          ))}
        </div>
      ) : (
        <Workspace
          key={`${accession}:${data.snapshot}`}
          accession={accession}
          catalog={data}
          expressionContext={expressionContext}
        />
      )}
    </section>
  );
}
