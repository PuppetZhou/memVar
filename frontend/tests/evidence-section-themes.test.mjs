import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

const model = readFileSync(new URL("../components/expression/model.ts", import.meta.url), "utf8");
const overview = readFileSync(new URL("../components/expression/expression-overview.tsx", import.meta.url), "utf8");
const icon = readFileSync(new URL("../components/expression/modality-icon.tsx", import.meta.url), "utf8");
const qtl = readFileSync(new URL("../components/qtl-summary.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../app/styles/evidence-section-themes.css", import.meta.url), "utf8");

test("expression keeps modality scales independent while exposing high-contrast states", () => {
  assert.match(model, /numericScaleMaximum/);
  assert.match(model, /95th percentile/);
  assert.match(overview, /expression-scale-key/);
  assert.match(overview, /Hatched cells are missing source measurements; bordered pale cells are measured zero/);
  assert.match(icon, /hpa_rna: Dna/);
  assert.match(icon, /hpa_ms: ScanLine/);
  assert.match(icon, /hpa_ihc: Microscope/);
  assert.match(icon, /paxdb: Database/);
});

test("QTL, expression, and interaction retain scoped framing without a second green section theme", () => {
  assert.match(qtl, /#fff8ef", "#ffc1a6", "#f59c7c", "#c85e62/);
  assert.match(styles, /#qtl, \.qtl-detail-page \{ --qtl-plum/);
  assert.match(styles, /#interactions, \.interaction-detail-page \{ --interaction-olive/);
  assert.match(styles, /--qtl-plum: #c85e62/);
  assert.match(styles, /#expression \.expression-overview-grid \{ background: #fff8fb; \}/);
  assert.match(styles, /--interaction-olive: #526b7a/);
  assert.match(styles, /#interactions \.source-tabs, \.interaction-detail-page \.source-tabs \{ background: #f1f5f9; \}/);
  assert.match(styles, /category-genetic[\s\S]*?repeating-linear-gradient/);
  assert.match(styles, /interaction-detail-page \.interaction-table thead th/);
  assert.match(styles, /qtl-detail-page \.qtl-table thead th/);
});
