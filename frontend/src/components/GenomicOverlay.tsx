import {
  projectX,
  positionInView,
  type GenomicView as View,
} from './genomic-coordinates';

function PositionLine({
  position,
  view,
  height = 120,
}: {
  position: number | null;
  view: View;
  height?: number;
}) {
  if (position === null || !positionInView(position, view)) return null;
  const x = projectX(position - 1, view);
  return (
    <line x1={x} x2={x} y1="0" y2={height} stroke="#2656c9" strokeWidth="1.2" />
  );
}
export function CoordinateOverlay({
  view,
  position,
  hoverPosition,
  brush,
  height = 125,
}: {
  view: View;
  position: number | null;
  hoverPosition: number | null;
  brush: View | null;
  height?: number;
}) {
  const visible = hoverPosition !== null && positionInView(hoverPosition, view);
  return (
    <g pointerEvents="none">
      {brush && (
        <rect
          className="agx-brush-selection"
          x={projectX(brush[0], view)}
          y={0}
          width={Math.max(
            0,
            projectX(brush[1], view) - projectX(brush[0], view)
          )}
          height={height}
        />
      )}
      <PositionLine position={position} view={view} height={height} />
      {visible && (
        <line
          className="agx-crosshair"
          x1={projectX(hoverPosition! - 1, view)}
          x2={projectX(hoverPosition! - 1, view)}
          y1={0}
          y2={height}
        />
      )}
    </g>
  );
}
