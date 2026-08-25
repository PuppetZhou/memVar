export type AnatomyViewBox = { x: number; y: number; width: number; height: number };

/** Must match the display frame exported by anatomy-geometry.ts. */
export const ANATOMY_MAP_WIDTH = 200;
export const ANATOMY_MAP_HEIGHT = 350;
export const ANATOMY_MIN_VIEW_WIDTH = ANATOMY_MAP_WIDTH / 4;
export const FULL_ANATOMY_VIEW: AnatomyViewBox = {
  x: 0,
  y: 0,
  width: ANATOMY_MAP_WIDTH,
  height: ANATOMY_MAP_HEIGHT,
};

export function clampAnatomyView(view: AnatomyViewBox): AnatomyViewBox {
  const width = Math.max(ANATOMY_MIN_VIEW_WIDTH, Math.min(ANATOMY_MAP_WIDTH, view.width));
  const height = width * ANATOMY_MAP_HEIGHT / ANATOMY_MAP_WIDTH;
  return {
    x: Math.max(0, Math.min(ANATOMY_MAP_WIDTH - width, view.x)),
    y: Math.max(0, Math.min(ANATOMY_MAP_HEIGHT - height, view.y)),
    width,
    height,
  };
}

export function zoomAnatomyView(
  view: AnatomyViewBox,
  factor: number,
  ratioX = .5,
  ratioY = .5,
): AnatomyViewBox {
  const nextWidth = Math.max(ANATOMY_MIN_VIEW_WIDTH, Math.min(ANATOMY_MAP_WIDTH, view.width / factor));
  const nextHeight = nextWidth * ANATOMY_MAP_HEIGHT / ANATOMY_MAP_WIDTH;
  const anchorX = view.x + view.width * ratioX;
  const anchorY = view.y + view.height * ratioY;
  return clampAnatomyView({
    x: anchorX - nextWidth * ratioX,
    y: anchorY - nextHeight * ratioY,
    width: nextWidth,
    height: nextHeight,
  });
}
