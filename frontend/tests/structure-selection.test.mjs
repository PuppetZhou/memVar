import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const component = (name) => readFile(new URL(`../components/${name}`, import.meta.url), "utf8");
const structureColors = () => readFile(new URL("../lib/structure-colors.ts", import.meta.url), "utf8");
const globalStyles = () => readFile(new URL("../app/globals.css", import.meta.url), "utf8");

function exportedFunction(source, name) {
  const start = source.indexOf(`export function ${name}(`);
  assert.notEqual(start, -1, `${name} must be exported from structure-colors.ts`);
  const bodyStart = source.indexOf("{", start);
  let depth = 0;
  for (let index = bodyStart; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") depth -= 1;
    if (depth === 0) return source.slice(start, index + 1)
      .replace(/^export\s+/, "")
      .replace(/\b(canonicalPosition|fragmentPosition)\s*:\s*number(?=\s*,)/g, "$1")
      .replace(/\bmapping\s*:\s*FragmentResidueMapping(?=\s*,)/g, "mapping")
      .replace(/\)\s*:\s*number\s*\|\s*null\s*\{/, ") {");
  }
  throw new Error(`Could not parse ${name} from structure-colors.ts`);
}

const residueMappings = structureColors().then((source) => new Function(`
  ${exportedFunction(source, "canonicalToFragmentResidue")}
  ${exportedFunction(source, "fragmentToCanonicalResidue")}
  return { canonicalToFragmentResidue, fragmentToCanonicalResidue };
`)());

const mappedFragment = Object.freeze({
  valid: true,
  canonicalStart: 1001,
  canonicalEnd: 1400,
});

test("canonical and AlphaFold fragment positions round-trip at 1-based closed boundaries", async () => {
  const { canonicalToFragmentResidue, fragmentToCanonicalResidue } = await residueMappings;
  assert.equal(canonicalToFragmentResidue(1001, mappedFragment), 1);
  assert.equal(canonicalToFragmentResidue(1200, mappedFragment), 200);
  assert.equal(canonicalToFragmentResidue(1400, mappedFragment), 400);

  assert.equal(fragmentToCanonicalResidue(1, mappedFragment), 1001);
  assert.equal(fragmentToCanonicalResidue(200, mappedFragment), 1200);
  assert.equal(fragmentToCanonicalResidue(400, mappedFragment), 1400);

  for (const position of [1001, 1143, 1400]) {
    const local = canonicalToFragmentResidue(position, mappedFragment);
    assert.notEqual(local, null);
    assert.equal(fragmentToCanonicalResidue(local, mappedFragment), position);
  }
});

test("residue conversion never guesses an invalid, incomplete, fractional, or out-of-range mapping", async () => {
  const { canonicalToFragmentResidue, fragmentToCanonicalResidue } = await residueMappings;
  const invalid = { valid: false, canonicalStart: 1001, canonicalEnd: 1400 };
  const incomplete = { valid: true, canonicalStart: null, canonicalEnd: 1400 };

  for (const mapping of [invalid, incomplete]) {
    assert.equal(canonicalToFragmentResidue(1001, mapping), null);
    assert.equal(fragmentToCanonicalResidue(1, mapping), null);
  }

  assert.equal(canonicalToFragmentResidue(1000, mappedFragment), null);
  assert.equal(canonicalToFragmentResidue(1401, mappedFragment), null);
  assert.equal(canonicalToFragmentResidue(1001.5, mappedFragment), null);
  assert.equal(fragmentToCanonicalResidue(0, mappedFragment), null);
  assert.equal(fragmentToCanonicalResidue(401, mappedFragment), null);
  assert.equal(fragmentToCanonicalResidue(1.5, mappedFragment), null);
});

test("the protein overview carries the shared sequence selection into the structure panel", async () => {
  const source = await component("protein-overview.tsx");
  assert.match(source, /<StructurePanel\s+accession=\{protein\.uniprot_accession\}\s+selection=\{selection\}\s+onSelectionChange=\{handleSelection\}/s);
});

test("sequence navigation distinguishes an exact site from a selected range", async () => {
  const source = await component("sequence-explorer.tsx");
  const css = await readFile(new URL("../app/styles/sequence.css", import.meta.url), "utf8");
  assert.match(source, /function SequenceSelectionOverlay/);
  assert.match(source, /selection\.site !== undefined/);
  assert.match(source, /className="sequence-selection-range"/);
  assert.doesNotMatch(source, /selectedPosition = selection \? \(selection\.start \+ selection\.end\) \/ 2/);
  assert.match(css, /--sequence-selection:\s*#f47254/i);
  assert.match(css, /\.sequence-selection-range\s*\{/);
  assert.match(css, /--sequence-plp:\s*#c85e62/i);
});

test("the structure panel selects a DBREF-covered fragment and makes 3D selection URL-addressable", async () => {
  const source = await component("structure-panel.tsx");
  assert.match(source, /selection\??\.site/);
  assert.match(source, /selectedPosition\s*>=\s*item\.canonical_start/);
  assert.match(source, /selectedPosition\s*<=\s*item\.canonical_end/);
  assert.match(source, /new URLSearchParams\(searchParams\.toString\(\)\)/);
  assert.match(source, /params\.set\(["']site["'],\s*String\(/);
  assert.match(source, /params\.delete\(["']range["']\)/);
  assert.match(source, /router\.replace\(/);
  assert.match(source, /selectedCanonicalPosition=/);
  assert.match(source, /onSelectCanonicalPosition=/);
});

test("the Mol* surface viewer validates DBREF residue mappings and keeps click selection bidirectional", async () => {
  const source = await component("structure-viewer.tsx");
  assert.match(source, /canonicalToFragmentResidue/);
  assert.match(source, /fragmentToCanonicalResidue/);
  assert.match(source, /import\("molstar\/lib\/mol-plugin-ui"\)/);
  assert.match(source, /createPluginUI/);
  assert.match(source, /representationPreset:\s*"coarse-surface"/);
  assert.match(source, /globalName:\s*"plddt-confidence"/);
  assert.match(source, /validateFragmentResidueMapping\(fragment, residues\)/);
  assert.match(source, /StructureProperties\.residue\.auth_seq_id/);
  assert.match(source, /selectionCallbackRef\.current\(selectedPositionRef\.current\s*===\s*canonicalPosition\s*\?\s*null\s*:\s*canonicalPosition\)/);
  assert.match(source, /StructureElement\.Loci\.fromSchema\([\s\S]*selectedElements\(fragmentPosition\)/);
  assert.match(source, /managers\.structure\.focus\.setFromLoci\(loci\)/);
  assert.match(source, /managers\.structure\.focus\.clear\(\)/);
  assert.match(source, /applyStructureInteractivity\(viewer,\s*\{[\s\S]*elements:\s*selectedElements\(fragmentPosition\)[\s\S]*action:\s*"select"/);
  assert.doesNotMatch(source, /3dmol|cartoon:/i);
});

test("the structure surface has mutually exclusive Sequence variant-density and pLDDT color modes", async () => {
  const viewer = await component("structure-viewer.tsx");
  const panel = await component("structure-panel.tsx");
  const colors = await structureColors();
  const css = await globalStyles();
  assert.match(panel, /sequence\/variant-site-density/);
  assert.doesNotMatch(panel, /sequence\/overview\?bins=1/);
  assert.match(panel, /variant_site_density/);
  assert.match(viewer, /type StructureColorMode = "sequence-variants" \| "plddt-confidence"/);
  assert.match(viewer, /useState<StructureColorMode>\("sequence-variants"\)/);
  assert.match(viewer, /sequenceVariantColor\(/);
  assert.match(viewer, /globalName:\s*"plddt-confidence"/);
  assert.match(viewer, /name:\s*"sequence-variant-density"/);
  assert.match(viewer, /dataRevision:\s*variantDensityRevisionRef\.current/);
  assert.match(viewer, /aria-pressed=\{colorMode === "sequence-variants"\}/);
  assert.match(viewer, /aria-pressed=\{colorMode === "plddt-confidence"\}/);
  assert.match(viewer, /Sequence residue variant-count legend/);
  assert.match(viewer, /AlphaFold pLDDT confidence legend/);
  assert.match(viewer, /Clear selected residue/);
  assert.match(colors, /return variantCountBucket\(count\)\.color/);
  assert.match(css, /\.structure-viewer-shell:fullscreen[^}]*grid-template-rows:\s*auto auto auto auto minmax\(0, 1fr\) auto/);
});
