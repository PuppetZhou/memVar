import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { chooseActiveSection, PROTEIN_SECTION_GROUPS, PROTEIN_SECTIONS, PROTEIN_SECTION_OBSERVER_OPTIONS, PROTEIN_SECTION_SCROLL_OFFSET_PX } from "../lib/protein-section-nav.ts";

test("the exact IntersectionObserver rootMargin uses only browser-supported px or percent units", () => {
  const parts = PROTEIN_SECTION_OBSERVER_OPTIONS.rootMargin.trim().split(/\s+/);
  assert.equal(parts.length, 4);
  assert.ok(parts.every((part) => /^-?(?:\d+|\d*\.\d+)(?:px|%)$/.test(part)));
  assert.equal(PROTEIN_SECTION_OBSERVER_OPTIONS.rootMargin, `-${PROTEIN_SECTION_SCROLL_OFFSET_PX}px 0px -58% 0px`);
  assert.equal(PROTEIN_SECTION_SCROLL_OFFSET_PX, 116);
});

test("section descriptors preserve all anchors in research-reading groups", () => {
  assert.deepEqual(PROTEIN_SECTION_GROUPS.map((group) => group.key), ["foundation", "genetic", "molecular", "network"]);
  assert.deepEqual(PROTEIN_SECTION_GROUPS.map((group) => group.label), ["Foundation", "Genetic evidence", "Molecular context", "Network & clinical"]);
  assert.ok(PROTEIN_SECTION_GROUPS.every((group) => group.description.length > 0));
  assert.deepEqual(PROTEIN_SECTIONS.map((section) => section.id), ["overview", "sequence", "structure", "variants", "anatomy", "expression", "qtl", "alphagenome", "interactions", "diseases"]);
});

test("active section prefers the latest section passed by the reading anchor", () => {
  assert.equal(chooseActiveSection([
    { id: "sequence", isIntersecting: true, top: -160, intersectionRatio: .4 },
    { id: "structure", isIntersecting: true, top: 70, intersectionRatio: .1 },
  ]), "structure");
});

test("active section uses the nearest upcoming section and preserves a fallback", () => {
  assert.equal(chooseActiveSection([
    { id: "variants", isIntersecting: true, top: 160, intersectionRatio: .2 },
    { id: "anatomy", isIntersecting: true, top: 390, intersectionRatio: .6 },
  ]), "variants");
  assert.equal(chooseActiveSection([], "qtl"), "qtl");
});

test("the mounted navigator restores an initial deep link after async protein content appears", async () => {
  const source = await readFile(new URL("../components/protein-section-nav.tsx", import.meta.url), "utf8");
  assert.match(source, /document\.getElementById\(initialHash\)\?\.scrollIntoView\(\{ block: "start" \}\)/);
  assert.match(source, /window\.addEventListener\("hashchange", onHashChange\)/);
});
