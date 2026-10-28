import assert from "node:assert/strict";
import { test } from "node:test";
import type { Provenance } from "@corvo/contracts/types";
import { badgeModel } from "./badge.ts";

const base: Provenance = {
  kind: "mock", source: "Synthetic", dataset_id: null, version: null, retrieved_at: null,
  resolution_m: null, temporal_resolution: null, license: null, generator: "tests",
  derived_from: [], notes: null,
};

test("a mock is shown with the loud MOCK badge", () => {
  const m = badgeModel(base);
  assert.equal(m.label, "MOCK");
  assert.equal(m.tone, "mock");
});

test("a mock pretending to cite a dataset is shown as INVALID, never as trusted", () => {
  const m = badgeModel({ ...base, dataset_id: "POWER_DAILY" });
  assert.equal(m.tone, "invalid");
  assert.match(m.title, /Invalid provenance/);
});

test("real data with a proper citation is shown as real", () => {
  const m = badgeModel({
    ...base, kind: "reanalysis", generator: null, dataset_id: "POWER_DAILY",
    retrieved_at: "2026-10-28T00:00:00+00:00", source: "NASA POWER",
  });
  assert.equal(m.tone, "real");
  assert.match(m.label, /REANALYSIS/);
});
