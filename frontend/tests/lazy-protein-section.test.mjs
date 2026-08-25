import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { LAZY_PROTEIN_SECTION_OBSERVER_OPTIONS, shouldMountLazyProteinSection } from "../lib/lazy-protein-section.ts";

test("dense protein sections remain unmounted until nearby unless their hash is targeted", () => {
  assert.equal(shouldMountLazyProteinSection("alphagenome", "", false), false);
  assert.equal(shouldMountLazyProteinSection("alphagenome", "#alphagenome", false), true);
  assert.equal(shouldMountLazyProteinSection("alphagenome", "#variants", true), true);
  assert.equal(LAZY_PROTEIN_SECTION_OBSERVER_OPTIONS.rootMargin, "600px 0px");
});

test("lazy section keeps one real anchor and mounts dense children only after the trigger", async () => {
  const [overview, lazySection] = await Promise.all([
    readFile(new URL("../components/protein-overview.tsx", import.meta.url), "utf8"),
    readFile(new URL("../components/lazy-protein-section.tsx", import.meta.url), "utf8"),
  ]);
  for (const id of ["sequence", "structure", "variants", "anatomy", "expression", "qtl", "alphagenome", "interactions", "diseases"]) {
    assert.match(overview, new RegExp(`<LazyProteinSection id="${id}"`));
  }
  assert.match(overview, /<LazyProteinSection label="Structured annotations">/);
  assert.match(lazySection, /new IntersectionObserver/);
  assert.match(lazySection, /window\.addEventListener\("hashchange", mountForHash\)/);
  assert.match(lazySection, /if \(mounted\) return <>\{children\}<\/>/);
  assert.match(lazySection, /<section id=\{id\} ref=\{placeholderRef\}/);
  assert.match(lazySection, /className="overview-section lazy-protein-section"/);
  assert.doesNotMatch(lazySection, /setMounted\(false\)/);
});
