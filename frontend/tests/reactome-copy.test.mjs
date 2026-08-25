import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const hierarchy = readFileSync(new URL("../components/reactome-hierarchy.tsx", import.meta.url), "utf8");

test("Reactome keeps the hierarchy semantics without user-facing direct-child jargon", () => {
  assert.match(hierarchy, /Curated pathway hierarchy/);
  assert.match(hierarchy, /immediate subpathway/);
  assert.doesNotMatch(hierarchy, /direct child|Direct parent–child/);
});
