import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { useQueries, useQuery } from '@tanstack/react-query';
import { Activity, ChevronDown, ChevronUp, Plus, X } from 'lucide-react';
import { api, number, params } from '../api';
import { palette, predictionTextColor } from '../lib/palette';
import { GenomeInspector } from './AlphaGenomeInspect';
import { CoordinateOverlay } from './GenomicOverlay';
import {
  contextName,
  details,
  colorStyle,
  modeInfo,
  sceneKey,
  type Track,
  type Gene,
  type Tile,
  type Signal,
  type Contacts,
  type Junction,
  type Junctions,
  type TrackData,
} from './alphagenome-model';
import {
  GENOMIC_PLOT,
  formatInterval as location,
  pointerPosition,
  projectX,
  type CoordinateProps,
} from './genomic-coordinates';

const finite = (values: (number | null)[]) =>
  values.filter((v): v is number => v !== null && Number.isFinite(v));
const num = (value: number | null | undefined) =>
  value === null || value === undefined ? 'Not available' : number(value, 5);
const tick = (value: number) =>
  value !== 0 && (Math.abs(value) < 0.01 || Math.abs(value) >= 10000)
    ? value.toExponential(1)
    : number(value, 3);

type TrackRequest = {
  accession: string;
  gene: Gene;
  tile: Tile;
  track: Track;
  view: CoordinateProps['view'];
  offset: number;
  enabled: boolean;
};
function referenceTrackQuery<T extends TrackData>({
  accession,
  gene,
  tile,
  track,
  view,
  offset,
  enabled,
}: TrackRequest) {
  return {
    queryKey: [
      'expression-alphagenome-track',
      accession,
      gene.ensembl_gene_id,
      tile.tile_id,
      track.track_id,
      view[0],
      view[1],
      offset,
    ],
    queryFn: ({ signal }: { signal: AbortSignal }) =>
      api<T>(
        `/proteins/${accession}/expression/alphagenome/track?${params({ gene: gene.ensembl_gene_id, tile: tile.tile_id, track_id: track.track_id, start: view[0], end: view[1], bins: 1024, offset, limit: 500 })}`,
        signal
      ),
    enabled,
    staleTime: 300000,
    gcTime: 120000,
    retry: 1,
  };
}
function useTrackVisibility() {
  const ref = useRef<HTMLElement>(null),
    [visible, setVisible] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => setVisible(entries.some((e) => e.isIntersecting)),
      { rootMargin: '500px' }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return { ref, visible };
}

type SignalSeries = { track: Track; data: Signal; color: string };
function SignalPlot({
  data,
  view,
  color,
  stat,
  position,
  hoverPosition,
  onHover,
  brush,
  series,
}: CoordinateProps & {
  data: Signal;
  color: string;
  stat: 'mean' | 'maximum';
  series?: SignalSeries[];
}) {
  const [localHover, setLocalHover] = useState(false),
    clipId = useId();
  const lines = series?.map((s) => ({
    ...s,
    label: details(s.track) || s.track.name,
    id: s.track.track_id,
  })) ?? [{ data, color, label: 'Signal', id: 'signal' }];
  const good = lines.flatMap((l) => finite(l.data[stat])),
    low = good.reduce((n, v) => Math.min(n, v), 0),
    high = good.reduce((n, v) => Math.max(n, v), 0),
    span = high - low || 1;
  const edge = (d: Signal, i: number) =>
    d.bin_edges?.[i] ?? d.start + (i * (d.end - d.start)) / d.mean.length;
  const current = hoverPosition ?? position,
    cx = current === null ? GENOMIC_PLOT.left : projectX(current - 1, view),
    y = (v: number) => 105 - ((v - low) / span) * 83;
  const inspected = lines.map((l) => ({
    ...l,
    index:
      current === null
        ? -1
        : l.data.mean.findIndex(
            (_, i) =>
              current - 1 >= edge(l.data, i) &&
              current - 1 < edge(l.data, i + 1)
          ),
  }));
  const pathFor = (d: Signal) => {
    let path = '',
      previous = false;
    for (let i = 0; i < d[stat].length; i++) {
      const v = d[stat][i];
      if (v === null) {
        previous = false;
        continue;
      }
      path += `${previous ? 'L' : 'M'}${projectX(edge(d, i), view).toFixed(2)},${y(v).toFixed(2)} H${projectX(edge(d, i + 1), view).toFixed(2)} `;
      previous = true;
    }
    return path;
  };
  const active = inspected.find((l) => l.index >= 0);
  return (
    <>
      <div className="agx-plot-frame">
        <svg
          className="agx-signal"
          viewBox="0 0 1000 118"
          preserveAspectRatio="none"
          role="img"
          tabIndex={0}
          aria-label={`Predicted ${stat} signal. ${lines.length} separate series. Drag to zoom; arrow keys inspect bins.`}
          onPointerMove={(e) => {
            setLocalHover(true);
            onHover(pointerPosition(e.currentTarget, e.clientX, view));
          }}
          onPointerLeave={() => {
            setLocalHover(false);
            onHover(null);
          }}
          onFocus={(e) => {
            if (e.currentTarget.matches(':focus-visible')) {
              setLocalHover(true);
              onHover(Math.max(view[0] + 1, Math.floor(edge(data, 0)) + 1));
            }
          }}
          onBlur={() => {
            setLocalHover(false);
            onHover(null);
          }}
          onKeyDown={(e) => {
            if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
              e.preventDefault();
              const next = Math.max(
                0,
                Math.min(
                  data.mean.length - 1,
                  (active?.index ?? 0) + (e.key === 'ArrowRight' ? 1 : -1)
                )
              );
              onHover(
                Math.max(
                  view[0] + 1,
                  Math.min(
                    view[1],
                    Math.floor((edge(data, next) + edge(data, next + 1)) / 2) +
                      1
                  )
                )
              );
            }
          }}
        >
          {[0, 0.5, 1].map((r) => (
            <g key={r}>
              <line
                x1={GENOMIC_PLOT.left}
                x2={GENOMIC_PLOT.right}
                y1={22 + r * 83}
                y2={22 + r * 83}
                stroke="#d9dcdf"
              />
              <text x="44" y={26 + r * 83} textAnchor="end">
                {tick(high - r * (high - low))}
              </text>
            </g>
          ))}
          <defs>
            <clipPath id={clipId}>
              <rect
                x={GENOMIC_PLOT.left}
                y="0"
                width={GENOMIC_PLOT.span}
                height="118"
              />
            </clipPath>
          </defs>
          {lines.map((l, i) => (
            <path
              key={l.id}
              data-series={l.id}
              d={pathFor(l.data)}
              clipPath={`url(#${clipId})`}
              fill="none"
              stroke={l.color}
              strokeWidth="1.6"
              vectorEffect="non-scaling-stroke"
              strokeDasharray={i >= 11 ? '5 3' : undefined}
            />
          ))}
          <CoordinateOverlay
            view={view}
            position={position}
            hoverPosition={hoverPosition}
            brush={brush}
            height={118}
          />
          {inspected
            .filter((l) => l.index >= 0 && l.data[stat][l.index] !== null)
            .map((l) => (
              <g key={l.id} pointerEvents="none">
                <line
                  className="agx-crosshair agx-crosshair-horizontal"
                  x1={GENOMIC_PLOT.left}
                  x2={GENOMIC_PLOT.right}
                  y1={y(l.data[stat][l.index]!)}
                  y2={y(l.data[stat][l.index]!)}
                />
                <circle
                  cx={cx}
                  cy={y(l.data[stat][l.index]!)}
                  r="3.5"
                  fill={l.color}
                  stroke="white"
                  strokeWidth="1.5"
                />
              </g>
            ))}
        </svg>
        {localHover && active && current !== null && !brush && (
          <GenomeInspector
            title={
              series?.length
                ? modeInfo(series[0].track.modality).label
                : 'Reference signal'
            }
            coordinate={`${data.chromosome}:${current.toLocaleString()}`}
            left={Math.max(6, Math.min(60, cx / 10 + 1))}
          >
            {inspected.map((l) => (
              <section key={l.id}>
                <div className="agx-inspector-series">
                  <i style={{ background: l.color }} />
                  {l.label}
                </div>
                {l.index < 0 ? (
                  <p>No data at this coordinate</p>
                ) : (
                  <>
                    <span className="agx-inspector-bin">
                      Bin{' '}
                      {location(
                        edge(l.data, l.index),
                        edge(l.data, l.index + 1)
                      )}
                    </span>
                    <dl>
                      <div>
                        <dt>Mean</dt>
                        <dd>{num(l.data.mean[l.index])}</dd>
                      </div>
                      <div>
                        <dt>Maximum</dt>
                        <dd>{num(l.data.maximum[l.index])}</dd>
                      </div>
                    </dl>
                  </>
                )}
              </section>
            ))}
          </GenomeInspector>
        )}
      </div>
      <div className="agx-inspect">
        {!active ? (
          <>
            <Activity size={12} />
            <span
              title={`Source resolution: ${number(data.source_resolution_bp ?? data.bin_width, 2)} bp`}
            >
              {number(data.bin_width, 2)} bp/bin
            </span>
            <span>Hover for values</span>
          </>
        ) : (
          <>
            <strong>
              {data.chromosome}:{current!.toLocaleString()}
            </strong>
            {inspected
              .filter((l) => l.index >= 0)
              .map((l) => (
                <span key={l.id}>
                  <i
                    className="agx-inline-swatch"
                    style={{ background: l.color }}
                  />
                  {lines.length > 1 ? l.label + ' · ' : ''}
                  {stat === 'mean' ? 'Mean' : 'Maximum'}{' '}
                  <b>{num(l.data[stat][l.index])}</b>
                </span>
              ))}
          </>
        )}
      </div>
      {!good.length && <p>No finite signal is available in this range.</p>}
    </>
  );
}
function ContactPlot({
  data,
  position,
  hoverPosition,
  onHover,
}: {
  data: Contacts;
  position: number | null;
  hoverPosition: number | null;
  onHover: (position: number | null) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null),
    [hover, setHover] = useState<[number, number] | null>(null);
  const peak = useMemo(
    () => finite(data.values).reduce((n, v) => Math.max(n, Math.abs(v)), 0),
    [data.values]
  );
  useEffect(() => {
    const ctx = canvas.current?.getContext('2d');
    if (!ctx) return;
    const pixels = ctx.createImageData(data.size, data.size);
    for (let y = 0; y < data.size; y++)
      for (let x = 0; x < data.size; x++) {
        const v = data.values[y * data.size + x],
          strength = v === null ? 0 : Math.min(1, Math.abs(v) / (peak || 1)),
          target = v !== null && v < 0 ? [123, 149, 198] : [200, 94, 98],
          i = (y * data.size + x) * 4;
        for (let c = 0; c < 3; c++)
          pixels.data[i + c] =
            v === null
              ? [218, 225, 235][c]
              : Math.round(250 + (target[c] - 250) * strength);
        pixels.data[i + 3] = 255;
      }
    ctx.putImageData(pixels, 0, 0);
  }, [data, peak]);
  const edge = (i: number) =>
    data.bin_edges?.[i] ?? data.start + i * data.bin_width;
  const coord = (i: number) => location(edge(i), edge(i + 1));
  const inspect = (x: number, y: number) => {
    setHover([x, y]);
    onHover(Math.floor((edge(x) + edge(x + 1)) / 2) + 1);
  };
  const current = hoverPosition ?? position,
    sharedIndex =
      current === null
        ? -1
        : Array.from({ length: data.size }, (_, i) => i).findIndex(
            (i) => current - 1 >= edge(i) && current - 1 < edge(i + 1)
          );
  return (
    <div className="agx-contact">
      <div>
        <div className="agx-contact-plot">
          <canvas
            ref={canvas}
            width={data.size}
            height={data.size}
            role="img"
            tabIndex={0}
            aria-label="Contact matrix. Arrow keys inspect both genomic axes."
            onFocus={(e) => {
              if (e.currentTarget.matches(':focus-visible')) inspect(0, 0);
            }}
            onBlur={() => {
              setHover(null);
              onHover(null);
            }}
            onKeyDown={(e) => {
              if (
                !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(
                  e.key
                )
              )
                return;
              e.preventDefault();
              const [x, y] = hover ?? [0, 0];
              inspect(
                Math.max(
                  0,
                  Math.min(
                    data.size - 1,
                    x +
                      (e.key === 'ArrowRight'
                        ? 1
                        : e.key === 'ArrowLeft'
                          ? -1
                          : 0)
                  )
                ),
                Math.max(
                  0,
                  Math.min(
                    data.size - 1,
                    y +
                      (e.key === 'ArrowDown' ? 1 : e.key === 'ArrowUp' ? -1 : 0)
                  )
                )
              );
            }}
            onPointerMove={(e) => {
              const r = e.currentTarget.getBoundingClientRect();
              inspect(
                Math.max(
                  0,
                  Math.min(
                    data.size - 1,
                    Math.floor(((e.clientX - r.left) / r.width) * data.size)
                  )
                ),
                Math.max(
                  0,
                  Math.min(
                    data.size - 1,
                    Math.floor(((e.clientY - r.top) / r.height) * data.size)
                  )
                )
              );
            }}
            onPointerLeave={() => {
              setHover(null);
              onHover(null);
            }}
          />
          <svg
            viewBox="0 0 100 100"
            className="agx-contact-crosshair"
            aria-hidden="true"
          >
            {sharedIndex >= 0 && (
              <line
                className="agx-crosshair"
                x1={((sharedIndex + 0.5) / data.size) * 100}
                x2={((sharedIndex + 0.5) / data.size) * 100}
                y1={0}
                y2={100}
              />
            )}{' '}
            {hover && (
              <line
                className="agx-crosshair agx-crosshair-horizontal"
                x1={0}
                x2={100}
                y1={((hover[1] + 0.5) / data.size) * 100}
                y2={((hover[1] + 0.5) / data.size) * 100}
              />
            )}
          </svg>
        </div>
        <p>
          Both axes · {data.chromosome}:{location(data.start, data.end)}
        </p>
      </div>
      <div>
        <strong>Relative contact signal</strong>
        <div className="agx-contact-legend" />
        <p>
          −{num(peak)} · 0 · +{num(peak)}
        </p>
        <p>Log-fold over expectation · gray = missing</p>
        <p>
          {data.size} × {data.size} · {number(data.bin_width, 0)} bp per cell
          axis
        </p>
        {hover && (
          <div className="agx-inspect">
            X {data.chromosome}:{coord(hover[0])}
            <br />Y {data.chromosome}:{coord(hover[1])}
            <br />
            <b>{num(data.values[hover[1] * data.size + hover[0]])}</b>
          </div>
        )}
      </div>
    </div>
  );
}
function JunctionPlot({
  data,
  view,
  color,
  position,
  hoverPosition,
  onHover,
  brush,
}: CoordinateProps & { data: Junctions; color: string }) {
  const [active, setActive] = useState<Junction | null>(null);
  const peak = data.items.reduce(
      (n, j) => (j.value === null ? n : Math.max(n, Math.abs(j.value))),
      1
    ),
    x = (p: number) => projectX(Math.max(view[0], Math.min(view[1], p)), view);
  return (
    <>
      <div className="agx-plot-frame">
        <svg
          className="agx-junctions"
          preserveAspectRatio="none"
          viewBox="0 0 1000 150"
          aria-label="Predicted splice junction connections. Drag to zoom."
          onPointerMove={(e) =>
            onHover(pointerPosition(e.currentTarget, e.clientX, view))
          }
          onPointerLeave={() => {
            setActive(null);
            onHover(null);
          }}
        >
          <line
            x1={GENOMIC_PLOT.left}
            x2={GENOMIC_PLOT.right}
            y1="130"
            y2="130"
            stroke="#d3d8de"
          />
          {data.items
            .filter((j): j is Junction & { value: number } => j.value !== null)
            .map((j) => (
              <path
                key={`${j.source_event_index ?? j.rank}:${j.strand}`}
                d={`M${x(j.start_0based)},130 Q${(x(j.start_0based) + x(j.end_0based)) / 2},${120 - Math.sqrt(Math.abs(j.value) / peak) * 110} ${x(j.end_0based)},130`}
                tabIndex={0}
                aria-label={`Junction ${location(j.start_0based, j.end_0based)}, ${j.strand} strand, value ${num(j.value)}`}
                onFocus={() => setActive(j)}
                onBlur={() => setActive(null)}
                onPointerEnter={() => setActive(j)}
                onPointerLeave={() => setActive(null)}
                stroke={color}
                strokeOpacity={
                  active === j ? 1 : 0.2 + (0.8 * Math.abs(j.value)) / peak
                }
                strokeWidth={active === j ? 3 : 1.4}
                fill="none"
              ></path>
            ))}
          <CoordinateOverlay
            view={view}
            position={position}
            hoverPosition={hoverPosition}
            brush={brush}
            height={145}
          />
        </svg>
        {active && !brush && (
          <GenomeInspector
            title="Splice junctions"
            coordinate={`${data.chromosome}:${location(active.start_0based, active.end_0based)}`}
            left={7}
          >
            <dl>
              <div>
                <dt>Strand</dt>
                <dd>{active.strand === '+' ? '+ · forward' : '− · reverse'}</dd>
              </div>
              <div>
                <dt>Junction signal</dt>
                <dd>{num(active.value)}</dd>
              </div>
            </dl>
            <p className="agx-inspector-note">
              Coordinates show the complete source interval. Arc height is a
              visual guide.
            </p>
          </GenomeInspector>
        )}
      </div>
      <details>
        <summary>
          Junction coordinates and values · {data.items.length.toLocaleString()}{' '}
          shown
        </summary>
        <div className="agx-junction-table">
          <table>
            <thead>
              <tr>
                <th>Interval (1-based)</th>
                <th>Strand</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((j) => (
                <tr key={`${j.source_event_index ?? j.rank}:${j.strand}`}>
                  <td>{location(j.start_0based, j.end_0based)}</td>
                  <td>{j.strand}</td>
                  <td>{num(j.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
export function TrackCard({
  accession,
  gene,
  tile,
  track,
  view,
  position,
  hoverPosition,
  onHover,
  brush,
  onRemove,
  onMove,
  index,
  total,
}: CoordinateProps & {
  accession: string;
  gene: Gene;
  tile: Tile;
  track: Track;
  onRemove: () => void;
  onMove: (delta: number) => void;
  index: number;
  total: number;
}) {
  const { ref, visible } = useTrackVisibility();
  const [collapsed, setCollapsed] = useState(false),
    [stat, setStat] = useState<'mean' | 'maximum'>('mean'),
    [offset, setOffset] = useState(0);
  useEffect(() => setOffset(0), [view[0], view[1], tile.tile_id]);
  const query = useQuery(
    referenceTrackQuery<TrackData>({
      accession,
      gene,
      tile,
      track,
      view,
      offset,
      enabled: visible && !collapsed,
    })
  );
  const meta = modeInfo(track.modality),
    d = query.data;
  return (
    <article
      ref={ref}
      className={`agx-track${collapsed ? ' is-collapsed' : ''}`}
      style={colorStyle(meta.color)}
    >
      <header>
        <div className="agx-track-title">
          <span className="agx-track-kind">{meta.label}</span>
          <strong>{contextName(track)}</strong>
          <span>{details(track)}</span>
          {track.modality === 'splice_sites' && (
            <small>Shared · not biosample-specific</small>
          )}
        </div>
        <div className="agx-track-actions">
          <button
            title="Move track up"
            aria-label={`Move ${track.track_id} up`}
            disabled={index === 0}
            onClick={() => onMove(-1)}
          >
            <ChevronUp size={15} />
          </button>
          <button
            title="Move track down"
            aria-label={`Move ${track.track_id} down`}
            disabled={index === total - 1}
            onClick={() => onMove(1)}
          >
            <ChevronDown size={15} />
          </button>
          <button
            aria-label={`${collapsed ? 'Expand' : 'Collapse'} ${track.track_id}`}
            aria-expanded={!collapsed}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <Plus size={15} /> : <ChevronUp size={15} />}
          </button>
          <button aria-label={`Remove ${track.track_id}`} onClick={onRemove}>
            <X size={15} />
          </button>
        </div>
      </header>
      <div className="agx-track-body">
        {collapsed ? (
          <span className="agx-collapsed-label">Track collapsed</span>
        ) : (
          <>
            <div className="agx-track-meta">
              <span>
                Reference prediction · {track.display_unit || 'Source scale'}
              </span>
              {d?.kind === 'signal' && (
                <div
                  className="agx-segment"
                  aria-label={`Statistic for ${track.track_id}`}
                >
                  <button
                    aria-pressed={stat === 'mean'}
                    onClick={() => setStat('mean')}
                  >
                    Mean
                  </button>
                  <button
                    aria-pressed={stat === 'maximum'}
                    onClick={() => setStat('maximum')}
                  >
                    Maximum
                  </button>
                </div>
              )}
            </div>
            {query.error ? (
              <div className="agx-error" role="alert">
                {query.error.message}
                <button onClick={() => query.refetch()}>Retry track</button>
              </div>
            ) : d?.kind === 'signal' ? (
              <SignalPlot
                data={d}
                view={view}
                color={predictionTextColor(meta.color)}
                stat={stat}
                position={position}
                hoverPosition={hoverPosition}
                onHover={onHover}
                brush={brush}
              />
            ) : d?.kind === 'contacts' ? (
              <ContactPlot
                data={d}
                position={position}
                hoverPosition={hoverPosition}
                onHover={onHover}
              />
            ) : d?.kind === 'junctions' ? (
              <>
                <JunctionPlot
                  data={d}
                  view={view}
                  color={meta.color}
                  position={position}
                  hoverPosition={hoverPosition}
                  onHover={onHover}
                  brush={brush}
                />
                <div className="agx-pagination">
                  <span>
                    {d.items.length ? offset + 1 : 0}–{offset + d.items.length}{' '}
                    of {number(d.total, 0)} events · source order
                  </span>
                  <button
                    disabled={!offset}
                    onClick={() => setOffset(Math.max(0, offset - 500))}
                  >
                    Previous
                  </button>
                  <button
                    disabled={!d.has_more}
                    onClick={() => setOffset(offset + 500)}
                  >
                    Next
                  </button>
                </div>
              </>
            ) : (
              <div className="agx-loading">
                {visible
                  ? 'Loading reference prediction…'
                  : 'Track loads when scrolled into view.'}
              </div>
            )}
          </>
        )}
      </div>
    </article>
  );
}
const seriesColors = [
  palette.blue,
  palette.coral,
  palette.sage,
  palette.cyan,
  palette.rose,
  palette.apricot,
  palette.leaf,
  palette.ice,
  palette.peach,
  palette.butter,
  palette.mist,
];
export function SignalGroupCard({
  accession,
  gene,
  tile,
  tracks,
  catalogTracks,
  view,
  position,
  hoverPosition,
  onHover,
  brush,
  onRemove,
  onRemoveSeries,
  onMove,
  index,
  total,
}: CoordinateProps & {
  accession: string;
  gene: Gene;
  tile: Tile;
  tracks: Track[];
  catalogTracks: Track[];
  onRemove: () => void;
  onRemoveSeries: (id: string) => void;
  onMove: (delta: number) => void;
  index: number;
  total: number;
}) {
  const { ref, visible } = useTrackVisibility();
  const [collapsed, setCollapsed] = useState(false),
    [stat, setStat] = useState<'mean' | 'maximum'>('mean'),
    [hidden, setHidden] = useState<string[]>([]);
  const queries = useQueries({
    queries: tracks.map((track) =>
      referenceTrackQuery<Signal>({
        accession,
        gene,
        tile,
        track,
        view,
        offset: 0,
        enabled: visible && !collapsed,
      })
    ),
  });
  const catalogColors = catalogTracks
    .filter(
      (t) =>
        sceneKey(t) === sceneKey(tracks[0]) &&
        t.modality === tracks[0].modality &&
        t.display_unit === tracks[0].display_unit
    )
    .sort((a, b) => a.track_id.localeCompare(b.track_id));
  const color = (t: Track) =>
    predictionTextColor(
      catalogColors.length === 1
        ? modeInfo(t.modality).color
        : seriesColors[
            catalogColors.findIndex((x) => x.track_id === t.track_id) %
              seriesColors.length
          ]
    );
  const lines = tracks.flatMap((track, i) =>
      queries[i].data && !hidden.includes(track.track_id)
        ? [{ track, data: queries[i].data!, color: color(track) }]
        : []
    ),
    meta = modeInfo(tracks[0].modality),
    groupId = tracks.map((t) => t.track_id).join(',');
  return (
    <article
      ref={ref}
      className={`agx-track agx-signal-track${collapsed ? ' is-collapsed' : ''}`}
      style={colorStyle(meta.color)}
    >
      <header>
        <div className="agx-track-title">
          <span className="agx-track-kind">{meta.label}</span>
          <strong>{contextName(tracks[0])}</strong>
          <span>
            {tracks.length > 1
              ? `${tracks.length} separate signals`
              : details(tracks[0])}
          </span>
        </div>
        <div className="agx-track-actions">
          <button
            aria-label={`Move ${groupId} up`}
            disabled={index === 0}
            onClick={() => onMove(-1)}
          >
            <ChevronUp size={14} />
          </button>
          <button
            aria-label={`Move ${groupId} down`}
            disabled={index === total - 1}
            onClick={() => onMove(1)}
          >
            <ChevronDown size={14} />
          </button>
          <button
            aria-label={`${collapsed ? 'Expand' : 'Collapse'} ${groupId}`}
            aria-expanded={!collapsed}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <Plus size={14} /> : <ChevronUp size={14} />}
          </button>
          <button
            aria-label={`Remove track panel ${groupId}`}
            onClick={onRemove}
          >
            <X size={14} />
          </button>
        </div>
      </header>
      <div className="agx-track-body">
        {collapsed ? (
          <span className="agx-collapsed-label">Track collapsed</span>
        ) : (
          <>
            <div className="agx-track-meta">
              <span>
                {tracks.length > 1
                  ? 'Overlay · original shared scale'
                  : tracks[0].display_unit}
              </span>
              <div className="agx-segment">
                <button
                  aria-pressed={stat === 'mean'}
                  onClick={() => setStat('mean')}
                >
                  Mean
                </button>
                <button
                  aria-pressed={stat === 'maximum'}
                  onClick={() => setStat('maximum')}
                >
                  Maximum
                </button>
              </div>
            </div>
            {tracks.length > 1 && (
              <div
                className="agx-series-legend"
                aria-label={`${meta.label} signals`}
              >
                {tracks.map((t) => (
                  <span key={t.track_id}>
                    <button
                      aria-pressed={!hidden.includes(t.track_id)}
                      onClick={() =>
                        setHidden((h) =>
                          h.includes(t.track_id)
                            ? h.filter((id) => id !== t.track_id)
                            : [...h, t.track_id]
                        )
                      }
                    >
                      <i style={{ background: color(t) }} />
                      {details(t) || t.name}
                    </button>
                    <button
                      aria-label={`Remove ${t.track_id} from overlay`}
                      onClick={() => onRemoveSeries(t.track_id)}
                    >
                      <X size={11} />
                    </button>
                  </span>
                ))}
              </div>
            )}
            {lines.length > 0 && queries.some((q) => q.isPending) && (
              <span className="agx-track-notice">
                Loading {queries.filter((q) => q.isPending).length} signal(s)…
              </span>
            )}
            {queries.map(
              (q, i) =>
                q.error && (
                  <div key={tracks[i].track_id} className="agx-error">
                    {details(tracks[i])}: {q.error.message}
                    <button onClick={() => q.refetch()}>Retry</button>
                  </div>
                )
            )}
            {lines.length ? (
              <SignalPlot
                data={lines[0].data}
                color={lines[0].color}
                series={lines}
                view={view}
                stat={stat}
                position={position}
                hoverPosition={hoverPosition}
                onHover={onHover}
                brush={brush}
              />
            ) : queries.some((q) => q.isPending) ? (
              <div className="agx-loading">Loading reference signals…</div>
            ) : (
              <div className="agx-loading">
                {tracks.every((t) => hidden.includes(t.track_id))
                  ? 'All signals hidden. Select a legend item to show it.'
                  : 'No signal is available. Retry the failed request above.'}
              </div>
            )}
          </>
        )}
      </div>
    </article>
  );
}
