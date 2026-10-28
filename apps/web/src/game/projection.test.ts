import assert from "node:assert/strict";
import { test } from "node:test";
import { bboxOf, makeProjector } from "./projection.ts";

const BBOX = [35.0, 36.9, 35.2, 37.0] as const;

test("bbox center lands at the canvas center", () => {
  const proj = makeProjector(BBOX, 800, 600);
  const c = proj([35.1, 36.95]);
  assert.ok(Math.abs(c.x - 400) < 1e-6 && Math.abs(c.y - 300) < 1e-6, JSON.stringify(c));
});

test("north is up: larger latitude gives smaller y; east is right", () => {
  const proj = makeProjector(BBOX, 800, 600);
  assert.ok(proj([35.1, 37.0]).y < proj([35.1, 36.9]).y);
  assert.ok(proj([35.2, 36.95]).x > proj([35.0, 36.95]).x);
});

test("aspect ratio is preserved with cos(lat) correction", () => {
  const proj = makeProjector([0, 60, 1, 61], 1000, 1000); // at 60N, 1 deg lon ~ 0.5 deg lat
  const w = proj([1, 60.5]).x - proj([0, 60.5]).x;
  const h = proj([0.5, 60]).y - proj([0.5, 61]).y;
  assert.ok(Math.abs(w / h - 0.5) < 0.01, `w/h = ${w / h}`);
});

test("everything inside the bbox stays inside the canvas", () => {
  const proj = makeProjector(BBOX, 640, 480, 20);
  for (const p of [[35.0, 36.9], [35.2, 37.0], [35.0, 37.0], [35.2, 36.9]] as const) {
    const q = proj(p);
    assert.ok(q.x >= 0 && q.x <= 640 && q.y >= 0 && q.y <= 480, JSON.stringify(q));
  }
});

test("bboxOf", () => {
  assert.deepEqual(bboxOf([[1, 5], [3, 2], [2, 9]]), [1, 2, 3, 9]);
});
