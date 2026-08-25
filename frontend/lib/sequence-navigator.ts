export type SequenceViewport = { start: number; end: number };

export function fullLengthPosition(clientX: number, left: number, width: number, length: number) {
  const ratio = Math.max(0, Math.min(1, (clientX - left) / Math.max(1, width)));
  return Math.max(1, Math.min(length, Math.floor(ratio * length) + 1));
}

export function navigatorGeometry(viewport: SequenceViewport, length: number) {
  return {
    leftPercent: (viewport.start - 1) / length * 100,
    widthPercent: (viewport.end - viewport.start + 1) / length * 100,
  };
}

export function resizeViewport(
  viewport: SequenceViewport,
  edge: "start" | "end",
  position: number,
  length: number,
  minimumSpan: number,
): SequenceViewport {
  if (edge === "start") {
    return { start: Math.max(1, Math.min(position, viewport.end - minimumSpan + 1)), end: viewport.end };
  }
  return { start: viewport.start, end: Math.min(length, Math.max(position, viewport.start + minimumSpan - 1)) };
}

export function panViewport(
  viewport: SequenceViewport,
  delta: number,
  length: number,
): SequenceViewport {
  const span = viewport.end - viewport.start + 1;
  const start = Math.max(1, Math.min(viewport.start + delta, length - span + 1));
  return { start, end: start + span - 1 };
}
