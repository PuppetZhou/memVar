import assert from 'node:assert/strict';
import test from 'node:test';
import {
  GENOMIC_PLOT,
  brushAtPixel,
  formatInterval,
  plotBounds,
  pointerPosition,
  positionAtPixel,
  positionInView,
  projectX,
} from '../src/components/genomic-coordinates.ts';

test('a half-open source window exposes exactly its 1-based positions', () => {
  const view = [55_019_277, 55_019_365];
  assert.equal(positionInView(55_019_277, view), false);
  assert.equal(positionInView(55_019_278, view), true);
  assert.equal(positionInView(55_019_365, view), true);
  assert.equal(positionInView(55_019_366, view), false);
  assert.equal(formatInterval(...view), '55,019,278–55,019,365');
  assert.equal(formatInterval(0, 1), '1–1');
});

test('SVG and responsive canvas share the same genomic gutters', () => {
  const view = [55_019_222, 55_019_422];
  assert.equal(projectX(view[0], view), GENOMIC_PLOT.left);
  assert.equal(projectX(view[1], view), GENOMIC_PLOT.right);
  assert.equal(projectX((view[0] + view[1]) / 2, view), 512);
  assert.ok(projectX(view[0] - 1, view) < GENOMIC_PLOT.left, 'source boundaries stay unclipped');
  for (const width of [320, 777, 1000, 1433]) {
    for (const position0 of [view[0], view[0] + 87, view[1]]) {
      const oldCanvas = (.052 + (position0 - view[0]) / (view[1] - view[0]) * .92) * width;
      assert.ok(Math.abs(projectX(position0, view, width) - oldCanvas) < 1e-10);
    }
  }
});

test('pointer inspection excludes gutters and includes both endpoint bases', () => {
  const view = [100, 110];
  assert.equal(positionAtPixel(52, 1000, view), 101);
  assert.equal(positionAtPixel(972, 1000, view), 110);
  assert.equal(positionAtPixel(512, 1000, view), 106);
  assert.equal(positionAtPixel(51, 1000, view), null);
  assert.equal(positionAtPixel(973, 1000, view), null);
  assert.equal(positionAtPixel(-500, 1000, view, true), 101);
  assert.equal(positionAtPixel(1500, 1000, view, true), 110);
  assert.equal(positionAtPixel(972, 1000, [100, 101]), 101);
  assert.equal(positionAtPixel(689.28, 800, [100, 200]), 189, 'fractional pixel at a base boundary uses the shared axis convention');
});

test('base centers round-trip at multiple canvas widths and genomic scales', () => {
  for (const view of [[0, 1], [100, 132], [55_019_222, 55_019_422], [55_003_394, 55_227_053]]) {
    const bases = [view[0], Math.floor((view[0] + view[1]) / 2), view[1] - 1];
    for (const width of [320, 777, 1000, 1433]) {
      for (const position0 of bases) {
        const pixel = projectX(position0 + .5, view, width);
        assert.equal(positionAtPixel(pixel, width, view), position0 + 1);
      }
    }
  }
});

test('captured brushing includes anchor and touched bases in either direction', () => {
  const view = [100, 110];
  const pixelOf = position0 => projectX(position0 + .5, view);
  assert.deepEqual(brushAtPixel(102, pixelOf(107), 1000, view), { interval: [102, 108], position: 108 });
  assert.deepEqual(brushAtPixel(107, pixelOf(102), 1000, view), { interval: [102, 108], position: 103 });
  assert.deepEqual(brushAtPixel(102, pixelOf(102), 1000, view), { interval: [102, 103], position: 103 });
  assert.deepEqual(brushAtPixel(102, -500, 1000, view), { interval: [100, 103], position: 101 });
  assert.deepEqual(brushAtPixel(102, 1500, 1000, view), { interval: [102, 110], position: 110 });
});

test('CSS padding is excluded before converting viewport pointer coordinates', () => {
  const original = globalThis.getComputedStyle;
  globalThis.getComputedStyle = () => ({ paddingLeft: '12px', paddingRight: '12px' });
  try {
    const element = { getBoundingClientRect: () => ({ left: 200, width: 1024 }) };
    assert.deepEqual(plotBounds(element), { left: 212, width: 1000 });
    assert.equal(pointerPosition(element, 212 + 52, [100, 110]), 101);
    assert.equal(pointerPosition(element, 212 + 972, [100, 110]), 110);
    assert.equal(pointerPosition(element, 212 + 51, [100, 110]), null);
  } finally {
    if (original === undefined) delete globalThis.getComputedStyle;
    else globalThis.getComputedStyle = original;
  }
});
