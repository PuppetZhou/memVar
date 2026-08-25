import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const css = readFileSync(new URL("../app/styles/m18-go-variant.css", import.meta.url), "utf8");
const globalCss = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

function declarations(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return css.match(new RegExp(`${escaped}\\s*\\{([^}]+)\\}`))?.[1] ?? "";
}

test("M18 GO and Variant public text never falls below 13px", () => {
  const sizes = [...css.matchAll(/font-size:\s*(\d*\.?\d+)(rem|px)/g)].map((match) => ({
    raw: match[0],
    pixels: match[2] === "rem" ? Number(match[1]) * 16 : Number(match[1]),
  }));

  assert.ok(sizes.length > 0, "expected explicit M18 typography declarations");
  assert.deepEqual(sizes.filter((size) => size.pixels < 13), []);
});

test("M18 GO layout selectors are card-scoped so later legacy rules cannot override them", () => {
  const goSelectorLines = css.split("\n").map((line) => line.trim()).filter((line) => line.startsWith(".go-"));
  assert.ok(goSelectorLines.length > 0);
  assert.ok(goSelectorLines.every((line) => line.startsWith(".go-evidence-card ")));
  assert.match(declarations(".go-evidence-card .go-evidence-intro"), /font-size:\s*\.9375rem/);
  assert.match(declarations(".go-evidence-card .go-term-list > li"), /grid-template-columns:\s*minmax\(0, 1fr\)/);
  assert.match(declarations(".go-evidence-card .go-term-evidence"), /min-width:\s*0/);
  assert.match(declarations(".go-evidence-card .go-evidence-records"), /grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\)/);
});

test("shared source-tab secondary labels use the readable metadata size", () => {
  assert.match(globalCss, /\.source-tabs button span\s*\{[^}]*font-size:\s*var\(--font-size-meta\)/);
});
