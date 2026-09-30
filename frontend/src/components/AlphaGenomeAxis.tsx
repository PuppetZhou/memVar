import { useEffect, useRef } from 'react';
import { palette } from '../lib/palette';
import type { Gene, ManeModel, TranscriptFeature } from './alphagenome-model';
import { CoordinateOverlay } from './GenomicOverlay';
import {
  GENOMIC_PLOT,
  formatInterval as location,
  plotBounds,
  pointerPosition,
  positionInView,
  projectX,
  type CoordinateProps,
  type GenomicView as View,
} from './genomic-coordinates';

/** Versioned MANE feature geometry, keyboard inspection and wheel navigation. */
export function GenomicAxis({
  view,
  gene,
  chromosome,
  position,
  hoverPosition,
  onHover,
  brush,
  cds,
  canPan,
  onPan,
  onFocusFeature,
}: CoordinateProps & {
  gene: Gene;
  chromosome: string;
  cds?: ManeModel;
  canPan: boolean;
  onPan: (fraction: number) => void;
  onFocusFeature: (block: TranscriptFeature) => void;
}) {
  const axisRef = useRef<SVGSVGElement>(null);
  useEffect(() => {
    const axis = axisRef.current;
    if (!axis) return;
    let pending = 0,
      frame = 0;
    const wheel = (event: WheelEvent) => {
      if (!canPan || brush || event.ctrlKey || event.metaKey || event.buttons)
        return;
      const delta =
        Math.abs(event.deltaX) > Math.abs(event.deltaY)
          ? event.deltaX
          : event.deltaY;
      if (!delta) return;
      event.preventDefault();
      const width = plotBounds(axis).width;
      pending +=
        (delta *
          (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? width : 1)) /
        width;
      if (!frame)
        frame = requestAnimationFrame(() => {
          const fraction = pending;
          pending = 0;
          frame = 0;
          onPan(fraction);
        });
    };
    axis.addEventListener('wheel', wheel, { passive: false });
    return () => {
      axis.removeEventListener('wheel', wheel);
      cancelAnimationFrame(frame);
    };
  }, [canPan, brush, onPan]);
  const hasStructure = Boolean(cds?.exons?.length);
  const modelStart = hasStructure
    ? (cds!.transcript_start_0based ??
      Math.min(...cds!.exons!.map((b) => b.start_0based)))
    : gene.gene_start_1based - 1;
  const modelEnd = hasStructure
    ? (cds!.transcript_end_0based ??
      Math.max(...cds!.exons!.map((b) => b.end_0based)))
    : gene.gene_end_1based_inclusive;
  const left = Math.max(view[0], modelStart),
    right = Math.min(view[1], modelEnd);
  const visible = (b: TranscriptFeature) =>
    b.start_0based < view[1] && b.end_0based > view[0];
  const exons = [...(cds?.exons ?? [])].sort(
    (a, b) => a.start_0based - b.start_0based
  );
  const gaps = hasStructure
    ? exons
        .slice(1)
        .map((b, i) => [exons[i].end_0based, b.start_0based] as View)
    : [[left, right] as View];
  const arrows = gaps.flatMap(([start, end]) => {
    const a = projectX(Math.max(view[0], start), view),
      b = projectX(Math.min(view[1], end), view),
      count = Math.floor((b - a) / 45);
    return Array.from(
      { length: Math.max(0, count) },
      (_, i) => a + ((i + 1) * (b - a)) / (count + 1)
    );
  });
  const strand = cds?.strand ?? gene.gene_strand;
  const features = [
    ...exons.filter(visible),
    ...(cds?.utrs?.filter(visible) ?? []),
    ...(cds?.segments.filter(visible) ?? []),
  ];
  const current = hoverPosition ?? position,
    within = current !== null && positionInView(current, view);
  const currentFeature =
    current === null
      ? null
      : (features.find(
          (b) =>
            b.feature === 'stop_codon' &&
            current - 1 >= b.start_0based &&
            current - 1 < b.end_0based
        ) ??
        features.find(
          (b) =>
            b.feature === 'CDS' &&
            current - 1 >= b.start_0based &&
            current - 1 < b.end_0based
        ) ??
        features.find(
          (b) =>
            b.feature === 'UTR' &&
            current - 1 >= b.start_0based &&
            current - 1 < b.end_0based
        ) ??
        features.find(
          (b) => current - 1 >= b.start_0based && current - 1 < b.end_0based
        ));
  const featureLabel = (b: TranscriptFeature) =>
    b.feature === 'stop_codon'
      ? 'Stop codon'
      : b.feature === 'exon'
        ? 'Exon'
        : b.feature;
  const hoverLabel = currentFeature
    ? ` · ${featureLabel(currentFeature)} · exon ${currentFeature.exon_number}`
    : hasStructure &&
        current !== null &&
        current - 1 >= modelStart &&
        current - 1 < modelEnd
      ? ' · Intron'
      : '';
  return (
    <div className="agx-axis-row">
      <div className="agx-axis-label">
        <strong className="agx-gene-name">{gene.gene_symbol}</strong>
        {(cds?.status === 'available' || hasStructure) && cds ? (
          <>
            <span>MANE Select · {strand} strand</span>
            <span
              className="agx-transcript"
              title={`${cds.transcript_id} · ${cds.cds_segments} coding segments`}
            >
              {cds.transcript_id}
            </span>
            <div className="agx-cds-guide">
              {cds.cds_segments > 0 && (
                <b className="agx-cds-key">
                  <i />
                  CDS
                </b>
              )}
              {Boolean(cds.utrs?.length) && (
                <b className="agx-cds-key">
                  <i className="agx-utr-key" />
                  UTR
                </b>
              )}
            </div>
            {cds.status !== 'available' && <span>CDS not available</span>}
          </>
        ) : (
          <span>
            {cds
              ? `MANE CDS: ${cds.status.replaceAll('_', ' ')}`
              : 'Loading MANE model…'}
          </span>
        )}
      </div>
      <svg
        ref={axisRef}
        className="agx-axis"
        viewBox="0 0 1000 112"
        preserveAspectRatio="none"
        role="img"
        tabIndex={0}
        aria-label="Shared genomic coordinates and MANE transcript structure. Wheel to pan; drag to zoom; arrow keys inspect positions."
        onPointerMove={(e) =>
          onHover(pointerPosition(e.currentTarget, e.clientX, view))
        }
        onPointerLeave={() => onHover(null)}
        onBlur={() => onHover(null)}
        onFocus={(e) => {
          if (e.currentTarget.matches(':focus-visible'))
            onHover(Math.floor((view[0] + view[1]) / 2) + 1);
        }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            e.preventDefault();
            onHover(
              Math.max(
                view[0] + 1,
                Math.min(
                  view[1],
                  (current ?? view[0] + 1) + (e.key === 'ArrowRight' ? 1 : -1)
                )
              )
            );
          }
        }}
      >
        {[0, 0.25, 0.5, 0.75, 1].map((r) => (
          <g key={r}>
            <line
              x1={GENOMIC_PLOT.left + r * GENOMIC_PLOT.span}
              x2={GENOMIC_PLOT.left + r * GENOMIC_PLOT.span}
              y1="20"
              y2="37"
              stroke="#a0a5aa"
            />
            <text
              x={GENOMIC_PLOT.left + r * GENOMIC_PLOT.span}
              y="14"
              textAnchor={r === 0 ? 'start' : r === 1 ? 'end' : 'middle'}
            >
              {Math.round(
                view[0] + r * (view[1] - view[0]) + (r === 1 ? 0 : 1)
              ).toLocaleString()}
            </text>
          </g>
        ))}
        {left < right && (
          <g
            className="agx-transcript-line"
            stroke="#303438"
            fill="none"
            strokeWidth="1.5"
          >
            <line
              x1={projectX(left, view)}
              x2={projectX(right, view)}
              y1="66"
              y2="66"
            />
            {arrows.map((x, i) => (
              <path
                key={i}
                d={
                  strand === '-'
                    ? `M${x + 3} 62 L${x - 2} 66 L${x + 3} 70`
                    : `M${x - 3} 62 L${x + 2} 66 L${x - 3} 70`
                }
              />
            ))}
          </g>
        )}
        {features.map((b, i) => {
          const x = projectX(Math.max(view[0], b.start_0based), view),
            width = Math.max(
              0.8,
              projectX(Math.min(view[1], b.end_0based), view) - x
            );
          const coding = b.feature === 'CDS' || b.feature === 'stop_codon',
            height = coding ? 24 : 14;
          const color =
            b.feature === 'CDS'
              ? '#3784b5'
              : b.feature === 'stop_codon'
                ? palette.rose
                : '#797e84';
          const name = `MANE ${featureLabel(b)} · exon ${b.exon_number} · ${chromosome}:${location(b.start_0based, b.end_0based)} · ${b.strand} strand`;
          return (
            <g key={`${b.feature}:${b.start_0based}:${i}`}>
              <rect
                className="agx-cds-block"
                data-feature={b.feature}
                data-exon={b.exon_number}
                data-start={b.start_0based + 1}
                data-end={b.end_0based}
                x={x}
                y={66 - height / 2}
                width={width}
                height={height}
                fill={b.feature === 'exon' ? '#fff' : color}
                stroke={color}
                strokeWidth={b.feature === 'exon' ? 1 : 0.5}
                role="button"
                tabIndex={0}
                aria-label={`Zoom to ${name}`}
                onClick={() => onFocusFeature(b)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    e.stopPropagation();
                    onFocusFeature(b);
                  }
                }}
              >
                <title>{name} · click to zoom</title>
              </rect>
              {width > 28 && b.feature === 'CDS' && (
                <text
                  className="agx-cds-exon-number"
                  x={x + width / 2}
                  y={70}
                  textAnchor="middle"
                  pointerEvents="none"
                >
                  {b.exon_number}
                </text>
              )}
            </g>
          );
        })}
        <CoordinateOverlay
          view={view}
          position={position}
          hoverPosition={hoverPosition}
          brush={brush}
          height={112}
        />
        {within && current !== null && (
          <text
            className="agx-hover-coordinate"
            x={Math.max(55, Math.min(965, projectX(current - 1, view)))}
            y="106"
            textAnchor={projectX(current - 1, view) > 720 ? 'end' : 'start'}
          >
            {chromosome}:{current.toLocaleString()}
            {hoverLabel}
          </text>
        )}
        {brush && (
          <text
            className="agx-hover-coordinate"
            x="510"
            y="73"
            textAnchor="middle"
          >
            {location(brush[0], brush[1])} · release to zoom
          </text>
        )}
      </svg>
    </div>
  );
}
