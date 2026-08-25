import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const identifiers = readFileSync(new URL("../components/identifiers-panel.tsx", import.meta.url), "utf8");
const selectedSite = readFileSync(new URL("../components/selected-site-evidence.tsx", import.meta.url), "utf8");
const differentialExpression = readFileSync(new URL("../components/expression/differential-expression.tsx", import.meta.url), "utf8");
const expressionCss = readFileSync(new URL("../app/styles/expression.css", import.meta.url), "utf8");
const tokens = readFileSync(new URL("../app/styles/tokens.css", import.meta.url), "utf8");
const sectionThemes = readFileSync(new URL("../app/styles/section-themes.css", import.meta.url), "utf8");
const homePage = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
const globalCss = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
const proteinNav = readFileSync(new URL("../components/protein-section-nav.tsx", import.meta.url), "utf8");
const alphaGenomeCss = readFileSync(new URL("../app/styles/alphagenome.css", import.meta.url), "utf8");

test("public identifier and site panels do not expose clipboard controls", () => {
  for (const source of [identifiers, selectedSite]) {
    assert.doesNotMatch(source, /navigator\.clipboard/);
    assert.doesNotMatch(source, />Copy(?: link)?</);
    assert.doesNotMatch(source, /aria-label={`Copy/);
  }
});

test("GEN tissue and disease values are explicit wrapping field modules", () => {
  assert.match(differentialExpression, /className="de-dataset-context-field"/);
  assert.match(differentialExpression, /className="de-dataset-context-field is-disease"/);
  assert.match(differentialExpression, /className="de-dataset-count"/);
  assert.match(expressionCss, /\.de-dataset-context \{[\s\S]*?grid-template-columns: minmax\(180px, \.8fr\) minmax\(0, 1\.45fr\) minmax\(190px, \.75fr\)/);
  assert.match(expressionCss, /\.de-dataset-context > \.de-dataset-context-field[\s\S]*?grid-template-columns: minmax\(0, 1fr\)/);
  assert.match(expressionCss, /\.de-dataset-context > \.de-dataset-context-field > span[\s\S]*?overflow-wrap: anywhere/);
  assert.match(expressionCss, /@media \(max-width: 1024px\)[\s\S]*?\.de-dataset-context \{ grid-template-columns: repeat\(2, minmax\(0, 1fr\)\); \}/);
  assert.match(expressionCss, /@media \(max-width: 768px\)[\s\S]*?\.de-dataset-context \{ grid-template-columns: minmax\(0, 1fr\); \}/);
});

test("interface keeps source palette tokens while using a warm-neutral canvas and saturated navigation framing", () => {
  assert.match(tokens, /--ui-ink-black: #001219/);
  assert.match(tokens, /--palette-blue: #7b95c6/);
  assert.match(tokens, /--palette-green: #67a583/);
  assert.match(tokens, /--palette-salmon: #f59c7c/);
  assert.match(tokens, /--palette-orange: var\(--palette-salmon\)/);
  assert.match(tokens, /--ui-oxford-navy: #293241/);
  assert.match(tokens, /--ui-cerulean: #3d5a80/);
  assert.match(tokens, /--ui-verdigris: #2a9d8f/);
  assert.match(tokens, /--color-canvas: #f2f0ea/);
  assert.match(tokens, /--color-ink: var\(--ui-ink-black\)/);
});

test("each protein section has a distinct UI theme without replacing scientific source tokens", () => {
  const sectionAccents = {
    overview: "#264653",
    sequence: "#0a9396",
    structure: "#ee9b00",
    variants: "#e76f51",
    anatomy: "#588157",
    expression: "#c85e62",
    qtl: "#ca6702",
    alphagenome: "#457b9d",
    interactions: "#6b6256",
    diseases: "#ae2012",
  };
  assert.equal(new Set(Object.values(sectionAccents)).size, Object.keys(sectionAccents).length);
  for (const [section, accent] of Object.entries(sectionAccents)) {
    assert.match(tokens, new RegExp(`--section-${section}-600: ${accent}`));
    assert.match(sectionThemes, new RegExp(`#${section} \\{[^}]*--section-600: var\\(--section-${section}-600\\)`));
    assert.match(sectionThemes, new RegExp(`a\\[href="#${section}"\\] \\{ --nav-accent: var\\(--section-${section}-600\\); --nav-deep: var\\(--section-${section}-800\\); \\}`));
  }
  assert.match(tokens, /--source-clinvar: #3f51b5/);
  assert.match(tokens, /--source-cosmic: #6d4aa2/);
  assert.doesNotMatch(tokens, /--section-(?:foundation|molecular|overview|structure)-(?:400|600|800): #(4f46e5|7c3aed|5b21b6|a78bfa)/);
  assert.match(sectionThemes, /\.protein-section-nav a\.is-active \{ border-color: var\(--nav-deep\); background: var\(--nav-deep\); color: white;/);
  assert.match(globalCss, /\.overview-section > \.section-heading \{[\s\S]*?border-top-color: var\(--section-accent\);[\s\S]*?background: white;/);
  assert.match(globalCss, /\.protein-section-nav a\.is-active \{[\s\S]*?background: var\(--nav-deep\); color: white;/);
  assert.match(globalCss, /\.journey-icon \{[\s\S]*?background: var\(--journey-deep\); color: white;/);
  assert.match(alphaGenomeCss, /alphagenome-modality-tabs button\[aria-pressed="true"\][\s\S]*?background: var\(--section-alphagenome-800\)/);
});

test("the homepage replaces the abstract compass with one attributed BioRender figure", () => {
  assert.match(homePage, /import Image from "next\/image"/);
  assert.match(homePage, /src="\/assets\/biorender-memvar-overview\.jpg"/);
  assert.match(homePage, /alt="Membrane protein centered among canonical sequence and paired sites, protein variants, tissue expression, regulatory genomics, protein interactions, and independent disease evidence records\."/);
  assert.match(homePage, />Created with BioRender\.com</);
  assert.match(homePage, /Source-specific evidence stays separate, and predictions are not clinical conclusions\./);
  assert.doesNotMatch(homePage, /evidence-compass-diagram|compass-core|compass-node|compass-spoke/);
  assert.doesNotMatch(globalCss, /\.evidence-compass-diagram|\.compass-core|\.compass-node|\.compass-spoke/);
});

test("homepage and protein navigation share semantic task-group icons", () => {
  for (const icon of ["Fingerprint", "Dna", "Activity", "Network"]) {
    assert.match(homePage, new RegExp(`\\b${icon}\\b`));
    assert.match(proteinNav, new RegExp(`\\b${icon}\\b`));
  }
  assert.match(homePage, /journey-icon/);
  assert.match(proteinNav, /protein-nav-group-icon/);
});
