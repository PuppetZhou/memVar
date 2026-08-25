import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const explorer = readFileSync(new URL("../components/sequence-explorer.tsx", import.meta.url), "utf8");
const css = readFileSync(new URL("../app/styles/sequence.css", import.meta.url), "utf8");

test("sequence selection toggles the same canonical site or range off and clears URL state", () => {
  assert.match(explorer, /const resolved = sameSelection\(selection, next\) \? null : next/);
  assert.match(explorer, /params\.delete\("site"\);/);
  assert.match(explorer, /params\.delete\("range"\);/);
  assert.match(explorer, /sameSelection\(selection, next\)/);
});

test("hover inspection is separate from pinned selection and Escape clears both", () => {
  assert.match(explorer, /const \[pinnedKey, setPinnedKey\] = useState<string \| null>\(null\)/);
  assert.match(explorer, /onPointerLeave=\{\(\) => setActiveKey\(pinnedKey\)\}/);
  assert.match(explorer, /setPinnedKey\(null\); setActiveKey\(null\); onSelect\(null\)/);
});

test("residue hover is frame-coalesced inside the virtualized grid", () => {
  const explorerBody = explorer.slice(explorer.indexOf("export function SequenceExplorer"));
  assert.match(explorer, /const ResidueGrid = memo\(function ResidueGrid/);
  assert.match(explorer, /const pointerFrame = useRef<number \| null>\(null\)/);
  assert.match(explorer, /window\.requestAnimationFrame\(\(\) => \{/);
  assert.match(explorer, /window\.cancelAnimationFrame\(pointerFrame\.current\)/);
  assert.match(explorer, /onPointerMove=\{\(event\) => \{ const position = positionAt\(event\.clientX, event\.clientY\); if \(position\) schedulePointerFocus\(position\); \}\}/);
  assert.doesNotMatch(explorerBody, /\[focusedPosition, setFocusedPosition\]/);
  assert.doesNotMatch(explorer, /onFocus=\{setFocusedPosition\}/);
});

test("canvas adapters and their selection callbacks remain stable while tracks are enabled", () => {
  assert.match(explorer, /const PtmTrack = memo\(function PtmTrack/);
  assert.match(explorer, /const VariantBars = memo\(function VariantBars/);
  assert.match(explorer, /const StabilityTrack = memo\(function StabilityTrack/);
  assert.match(explorer, /const updateViewport = useCallback/);
  assert.match(explorer, /const writeSelection = useCallback/);
  assert.match(explorer, /const selectOverviewRange = useCallback/);
  for (const track of ["topology", "pfam", "functional", "secondaryStructure", "conservation", "ptm", "variant", "stability", "covalent"]) {
    assert.match(explorer, new RegExp(`enabled\\.includes\\("${track}"\\)`));
  }
});

test("JSD offers exact hover or focus values and the sequence visual families are distinct", () => {
  assert.match(explorer, /JSD \{detailed\.length \? active\.mean\.toFixed\(4\)/);
  assert.ok(explorer.includes("Range {active.min.toFixed(4)}–{active.max.toFixed(4)}"));
  assert.match(explorer, /VARIANT_ALL_COLOR = "#7B95C6"/);
  assert.match(explorer, /VARIANT_PLP_COLOR = "#B42352"/);
  assert.match(css, /secondary-helix-shape \{ fill: #7b95c6/);
  assert.match(css, /secondary-beta-shape \{ fill: #67a583/);
  assert.match(css, /secondary-turn-shape \{ fill: none; stroke: #f59c7c/);
});
