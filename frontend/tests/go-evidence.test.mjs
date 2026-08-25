import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { applyGoTextFilters, formatGoDate, goAspectLabel, goTermEvidencePath, pubmedUrl, quickGoTermUrl, toggledGoAspect } from "../lib/go-evidence.ts";

const component = readFileSync(new URL("../components/go-evidence.tsx", import.meta.url), "utf8");

test("GO evidence uses stable aspect labels and a safely encoded QuickGO term URL", () => {
  assert.equal(goAspectLabel("MF"), "Molecular function");
  assert.equal(goAspectLabel("BP"), "Biological process");
  assert.equal(goAspectLabel("CC"), "Cellular component");
  assert.equal(quickGoTermUrl("GO:0005006"), "https://www.ebi.ac.uk/QuickGO/term/GO%3A0005006");
});

test("only recognised PMID references become external publication links", () => {
  assert.equal(pubmedUrl("PMID:12828935"), "https://pubmed.ncbi.nlm.nih.gov/12828935/");
  assert.equal(pubmedUrl("GO_REF:0000043"), null);
  assert.equal(pubmedUrl("PMID:12<script>"), null);
  assert.equal(formatGoDate("20231211"), "2023-12-11");
  assert.equal(formatGoDate(null), "Not recorded");
});

test("GO text filters only change the request after explicit application", () => {
  assert.deepEqual(applyGoTextFilters(" receptor ", " ida "), { query: "receptor", evidenceCode: "IDA" });
  assert.deepEqual(applyGoTextFilters("   ", ""), { query: "", evidenceCode: "" });
});

test("activating the selected GO aspect closes its browser instead of trapping it open", () => {
  assert.equal(toggledGoAspect("MF", "MF"), null);
  assert.equal(toggledGoAspect("MF", "BP"), "BP");
  assert.equal(toggledGoAspect(null, "CC"), "CC");
});

test("term-level records retain native details disclosure, so a second summary activation closes them", () => {
  assert.match(component, /<details className="go-term-evidence" onToggle=/);
  assert.match(component, /<summary><ChevronRight/);
});

test("the active evidence-code filter is retained by initial and cursor evidence requests", () => {
  assert.equal(
    goTermEvidencePath("P00533", "GO:0005006", { evidenceCode: " ida ", includeNegated: false }),
    "/proteins/P00533/go/terms/GO%3A0005006/evidence?limit=20&evidence_code=IDA",
  );
  assert.equal(
    goTermEvidencePath("P00533", "GO:0005006", { evidenceCode: "IDA", includeNegated: true, cursor: "next-page", limit: 50 }),
    "/proteins/P00533/go/terms/GO%3A0005006/evidence?limit=50&evidence_code=IDA&include_negated=true&cursor=next-page",
  );
});
