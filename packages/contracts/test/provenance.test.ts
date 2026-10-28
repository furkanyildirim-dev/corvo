import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import schema from "../schema/corvo.schema.json" with { type: "json" };
import {
  INVALID_LABEL,
  KIND_LABELS,
  assertTrustworthy,
  collectProvenance,
  dataStatus,
  provenanceViolations,
  safeLabel,
} from "../src/provenance.ts";
import type { DataKind, Provenance } from "../src/types.gen.ts";

const cases = JSON.parse(
  readFileSync(new URL("../fixtures/provenance_cases.json", import.meta.url), "utf8"),
) as { name: string; provenance: Provenance; valid: boolean }[];

test("every DataKind in the schema has a UI label; MOCK is loud and labels are distinct", () => {
  const kinds = (schema.$defs as unknown as { DataKind: { enum: DataKind[] } }).DataKind.enum;
  assert.deepEqual([...kinds].sort(), Object.keys(KIND_LABELS).sort());
  assert.equal(KIND_LABELS.mock, "MOCK");
  assert.equal(new Set(Object.values(KIND_LABELS)).size, kinds.length);
});

test("TS guard agrees with Python on every provenance case (drift detector)", () => {
  assert.ok(cases.length >= 10);
  for (const c of cases) {
    const violations = provenanceViolations(c.provenance);
    assert.equal(violations.length === 0, c.valid, `${c.name}: ${violations.join("; ") || "no violations"}`);
  }
});

test("a valid mock is labelled MOCK; an invalid one never gets a trusted label", () => {
  const good = cases.find((c) => c.name === "mock proper")!;
  assert.equal(safeLabel(good.provenance), "MOCK");
  const posing = cases.find((c) => c.name === "mock posing as dataset")!;
  assert.equal(safeLabel(posing.provenance), INVALID_LABEL);
  const fakeObserved = cases.find((c) => c.name === "observed without dataset")!;
  assert.equal(safeLabel(fakeObserved.provenance), INVALID_LABEL);
});

test("collectProvenance finds nested provenance; dataStatus flags mock", () => {
  const mock = cases.find((c) => c.name === "mock proper")!.provenance;
  const real = cases.find((c) => c.name === "observed with dataset")!.provenance;
  const tree = { a: { provenance: real, items: [{ provenance: mock }] }, b: [{ c: { provenance: real } }] };
  assert.equal(collectProvenance(tree).length, 3);
  assert.equal(dataStatus(tree), "contains_mock");
  assert.equal(dataStatus({ x: { provenance: real } }), "no_mock");
  assert.equal(dataStatus({ nothing: 1 }), "no_mock");
});

test("assertTrustworthy throws on a payload that hides a violation", () => {
  const bad = cases.find((c) => c.name === "mock posing as dataset")!.provenance;
  assert.throws(() => assertTrustworthy({ deep: [{ provenance: bad }] }), /Untrustworthy/);
  const ok = cases.find((c) => c.name === "mock proper")!.provenance;
  assert.doesNotThrow(() => assertTrustworthy({ provenance: ok }));
});
