// Needs ajv ^8 (`npm install`). NOT executed in the M0 build sandbox, which only had ajv 6.
import assert from "node:assert/strict";
import { test } from "node:test";
import { parseRegionPack } from "../src/validate.ts";
import { clone, load } from "./helpers.ts";

for (const id of ["cukurova", "konya"]) {
  test(`${id}: MOCK pack passes the JSON Schema`, () => {
    assert.equal(parseRegionPack(load(id)).parcels.parcels.length, 6);
  });
}

test("schema rejects a missing provenance block", () => {
  const pack = clone(load("cukurova")) as unknown as Record<string, Record<string, unknown>>;
  delete pack.climate!.provenance;
  assert.throws(() => parseRegionPack(pack), /failed validation/);
});

test("schema rejects unknown fields and wrong types", () => {
  const extra = clone(load("konya")) as unknown as Record<string, unknown>;
  extra.surprise = 1;
  assert.throws(() => parseRegionPack(extra), /failed validation/);
  const wrong = clone(load("konya")) as unknown as { site: { center: unknown } };
  wrong.site.center = ["35", "37"];
  assert.throws(() => parseRegionPack(wrong), /failed validation/);
});

test("parse also runs the provenance guard", () => {
  const tampered = clone(load("cukurova"));
  tampered.climate.provenance.kind = "observed";
  tampered.climate.provenance.generator = null;
  assert.throws(() => parseRegionPack(tampered), /Untrustworthy provenance/);
});
