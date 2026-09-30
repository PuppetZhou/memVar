/** Genomic windows are 0-based and half-open; inspected positions are 1-based. */
export type GenomicView = [start0: number, end0: number];

export type CoordinateProps = {
  view: GenomicView;
  position: number | null;
  hoverPosition: number | null;
  onHover: (position: number | null) => void;
  brush: GenomicView | null;
};

/** All one-dimensional plots reserve the same gutters in a 1,000-unit viewBox. */
export const GENOMIC_PLOT = {
  width: 1000,
  left: 52,
  right: 972,
  span: 920,
} as const;

/** Project a source boundary, without clipping: callers retain their own clip paths. */
export function projectX(
  position0: number,
  view: GenomicView,
  width: number = GENOMIC_PLOT.width
): number {
  const fraction = (position0 - view[0]) / (view[1] - view[0]);
  if (width === GENOMIC_PLOT.width)
    return GENOMIC_PLOT.left + fraction * GENOMIC_PLOT.span;
  return (
    (GENOMIC_PLOT.left / GENOMIC_PLOT.width +
      (fraction * GENOMIC_PLOT.span) / GENOMIC_PLOT.width) *
    width
  );
}

export function positionInView(position1: number, view: GenomicView): boolean {
  return position1 - 1 >= view[0] && position1 - 1 < view[1];
}

/** The input pixel is relative to the content box, after CSS padding is removed. */
export function plotFraction(pixel: number, width: number): number {
  return (
    ((GENOMIC_PLOT.width * pixel) / width - GENOMIC_PLOT.left) /
    GENOMIC_PLOT.span
  );
}

/** Outside gutters do not inspect data; a captured drag can explicitly clamp them. */
export function positionAtPixel(
  pixel: number,
  width: number,
  view: GenomicView,
  clamp = false
): number | null {
  const fraction = plotFraction(pixel, width);
  if (!clamp && (fraction < 0 || fraction > 1)) return null;
  return Math.max(
    view[0] + 1,
    Math.min(view[1], Math.floor(view[0] + fraction * (view[1] - view[0])) + 1)
  );
}

/** Include both touched bases, irrespective of drag direction, inside the origin view. */
export function brushAtPixel(
  anchor0: number,
  pixel: number,
  width: number,
  view: GenomicView
): {
  interval: GenomicView;
  position: number;
} {
  const fraction = Math.max(0, Math.min(1, plotFraction(pixel, width)));
  const point = Math.min(
    view[1] - 1,
    Math.floor(view[0] + fraction * (view[1] - view[0]))
  );
  return {
    interval: [Math.min(anchor0, point), Math.max(anchor0, point) + 1],
    position: point + 1,
  };
}

export function plotBounds(element: Element): { left: number; width: number } {
  const rect = element.getBoundingClientRect(),
    style = getComputedStyle(element);
  const paddingLeft = parseFloat(style.paddingLeft) || 0,
    paddingRight = parseFloat(style.paddingRight) || 0;
  return {
    left: rect.left + paddingLeft,
    width: rect.width - paddingLeft - paddingRight,
  };
}

export function pointerPosition(
  element: Element,
  clientX: number,
  view: GenomicView
): number | null {
  const bounds = plotBounds(element);
  return positionAtPixel(clientX - bounds.left, bounds.width, view);
}

/** Display a source half-open interval as a 1-based inclusive range. */
export function formatInterval(start0: number, end0: number): string {
  return `${Math.floor(start0 + 1).toLocaleString()}–${Math.ceil(end0).toLocaleString()}`;
}
