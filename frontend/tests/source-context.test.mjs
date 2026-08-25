import assert from "node:assert/strict";
import test from "node:test";

import { sharedSourceRecordValue, sourceRecordMetadataIsUniform, sourceRecordMetadataText } from "../lib/source-context.ts";

test("source context exposes metadata only when all displayed records agree", () => {
  assert.equal(sharedSourceRecordValue([
    { source_release: "2026-01" },
    { source_release: "2026-01" },
  ], "source_release"), "2026-01");
  assert.equal(sourceRecordMetadataIsUniform([{ source_release: null }, { source_release: null }], "source_release"), true);
});

test("source context does not merge missing or heterogeneous record metadata", () => {
  assert.equal(sharedSourceRecordValue([
    { evidence_grain: "assertion" },
    { evidence_grain: "association" },
  ], "evidence_grain"), null);
  assert.equal(sharedSourceRecordValue([
    { source_release: "2026-01" },
    { source_release: null },
  ], "source_release"), null);
  assert.equal(sourceRecordMetadataIsUniform([{ source_release: "2026-01" }, { source_release: null }], "source_release"), false);
});

test("source context renders absent record grain explicitly", () => {
  assert.equal(sourceRecordMetadataText(null), "Not reported in this response");
  assert.equal(sourceRecordMetadataText(undefined), "Not reported in this response");
  assert.equal(sourceRecordMetadataText("   "), "Not reported in this response");
  assert.equal(sourceRecordMetadataText("  expert-panel assertion  "), "expert-panel assertion");
});
