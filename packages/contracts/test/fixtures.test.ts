// Guard-level tests on the Python-generated MOCK packs. No ajv needed (see validate.test.ts).
import assert from "node:assert/strict";
import { test } from "node:test";
import { assertTrustworthy, collectProvenance, dataStatus } from "../src/provenance.ts";
import { clone, load } from "./helpers.ts";

for (const id of ["cukurova", "konya"]) {
  test(`${id}: MOCK pack passes the provenance guard and is flagged as containing mock`, () => {
    const pack = load(id);
    assert.doesNotThrow(() => assertTrustworthy(pack));
    assert.equal(dataStatus(pack), "contains_mock");
    assert.equal(pack.id, id);
  });

  test(`${id}: nothing in the pack claims to be real data`, () => {
    const kinds = new Set(collectProvenance(load(id)).map((p) => p.kind));
    assert.deepEqual([...kinds].sort(), ["game_assumption", "mock"]);
  });
}

test("both regions have the identical shape (no region-specific fields)", () => {
  assert.deepEqual(Object.keys(load("cukurova")).sort(), Object.keys(load("konya")).sort());
});

test("a pack relabelled as 'observed' without a dataset is rejected by the guard", () => {
  const tampered = clone(load("cukurova"));
  tampered.climate.provenance.kind = "observed";
  tampered.climate.provenance.generator = null;
  assert.throws(() => assertTrustworthy(tampered), /observed must cite dataset_id/);
});

test("a mock block that fakes a dataset citation is rejected by the guard", () => {
  const tampered = clone(load("konya"));
  tampered.soils.provenance.dataset_id = "SOILGRIDS_V2";
  assert.throws(() => assertTrustworthy(tampered), /mock must not cite a real dataset/);
});
