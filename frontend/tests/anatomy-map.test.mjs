import assert from "node:assert/strict";
import test from "node:test";

import {
  FULL_ANATOMY_VIEW,
  clampAnatomyView,
  zoomAnatomyView,
} from "../lib/anatomy-map.ts";
import { ANATOMY_IMAGE } from "../lib/anatomy-geometry.ts";

test("anatomy zoom preserves the cursor anchor", () => {
  const ratioX = .25;
  const ratioY = .7;
  const beforeX = FULL_ANATOMY_VIEW.x + FULL_ANATOMY_VIEW.width * ratioX;
  const beforeY = FULL_ANATOMY_VIEW.y + FULL_ANATOMY_VIEW.height * ratioY;
  const zoomed = zoomAnatomyView(FULL_ANATOMY_VIEW, 2, ratioX, ratioY);

  assert.equal(zoomed.x + zoomed.width * ratioX, beforeX);
  assert.equal(zoomed.y + zoomed.height * ratioY, beforeY);
  assert.equal(zoomed.width, 100);
});

test("anatomy view can always return to the complete image", () => {
  const zoomed = zoomAnatomyView(FULL_ANATOMY_VIEW, 4, .8, .8);
  assert.deepEqual(zoomAnatomyView(zoomed, 10 ** -3), FULL_ANATOMY_VIEW);
});

test("anatomy pan is clamped to the image boundary", () => {
  assert.deepEqual(
    clampAnatomyView({ x: -500, y: 900, width: 100, height: 175 }),
    { x: 0, y: 175, width: 100, height: 175 },
  );
});

test("anatomy background retains the complete local illustration contract", () => {
  assert.equal(ANATOMY_IMAGE.sourceWidth, 2752);
  assert.equal(ANATOMY_IMAGE.sourceHeight, 1536);
  assert.equal(ANATOMY_IMAGE.displayWidth, 200);
  assert.equal(ANATOMY_IMAGE.displayHeight, 350);
  assert.equal(ANATOMY_IMAGE.preserveAspectRatio, "xMidYMid slice");
  assert.equal(ANATOMY_IMAGE.href, "/assets/biorender-human-anatomy.svg");
});
