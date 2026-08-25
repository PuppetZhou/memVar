import assert from "node:assert/strict";
import test from "node:test";

import { formatDdg, partnerFor, percentage, stabilityDirectionLabel } from "../lib/site-evidence.ts";

test("site evidence keeps a missing ΔΔG distinct from zero", () => {
  assert.equal(formatDdg(null), "Not predicted");
  assert.equal(formatDdg(0), "+0.00 kcal/mol");
  assert.equal(percentage(null), "—");
});

test("site evidence labels stability direction and covalent partner without color", () => {
  assert.equal(stabilityDirectionLabel("predicted_stabilizing"), "Predicted stabilizing");
  assert.equal(stabilityDirectionLabel("predicted_destabilizing"), "Predicted destabilizing");
  assert.equal(partnerFor({ start_endpoint: 31, end_endpoint: 58 }, 31), 58);
  assert.equal(partnerFor({ start_endpoint: 31, end_endpoint: 58 }, 58), 31);
});
