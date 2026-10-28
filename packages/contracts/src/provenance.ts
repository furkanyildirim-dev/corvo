// Client-side provenance guard. The Python contracts are the source of truth; this mirrors the
// invariants so a bad payload can never be shown as trustworthy data. A cross-language test
// (fixtures/provenance_cases.json, produced by Python) fails if the two ever drift apart.

import labels from "../schema/provenance-labels.json" with { type: "json" };
import type { DataKind, Provenance } from "./types.gen.ts";

export const KIND_LABELS = labels as Record<DataKind, string>;
export const INVALID_LABEL = "INVALID PROVENANCE";

const REAL_KINDS: ReadonlySet<DataKind> = new Set<DataKind>([
  "observed",
  "reanalysis",
  "forecast",
  "model_estimate",
]);
const GENERATED_KINDS: ReadonlySet<DataKind> = new Set<DataKind>([
  "mock",
  "game_assumption",
  "simulated",
]);

export type DataStatus = "contains_mock" | "no_mock";

/** Human-readable invariant violations; empty array = trustworthy. */
export function provenanceViolations(p: Provenance): string[] {
  const out: string[] = [];
  if (!(p.kind in KIND_LABELS)) return [`unknown kind ${String(p.kind)}`];
  if (REAL_KINDS.has(p.kind)) {
    if (!p.dataset_id || !p.retrieved_at) out.push(`${p.kind} must cite dataset_id and retrieved_at`);
    if (p.generator) out.push(`${p.kind} cannot come from a generator`);
  }
  if (p.kind === "mock" && (p.dataset_id || p.retrieved_at)) {
    out.push("mock must not cite a real dataset or retrieval time");
  }
  if (GENERATED_KINDS.has(p.kind) && !p.generator) out.push(`${p.kind} must name its generator`);
  return out;
}

export const isMock = (p: Provenance): boolean => p.kind === "mock";

/** Label to show in the UI. Invalid provenance is never presented under a trusted label. */
export function safeLabel(p: Provenance): string {
  return provenanceViolations(p).length ? INVALID_LABEL : KIND_LABELS[p.kind];
}

function looksLikeProvenance(v: unknown): v is Provenance {
  return (
    typeof v === "object" &&
    v !== null &&
    typeof (v as { kind?: unknown }).kind === "string" &&
    typeof (v as { source?: unknown }).source === "string"
  );
}

/** Every Provenance reachable from `value` (looks under any `provenance` key). */
export function collectProvenance(value: unknown): Provenance[] {
  const found: Provenance[] = [];
  const walk = (v: unknown): void => {
    if (Array.isArray(v)) return v.forEach(walk);
    if (typeof v !== "object" || v === null) return;
    for (const [key, child] of Object.entries(v)) {
      if (key === "provenance" && looksLikeProvenance(child)) found.push(child);
      else walk(child);
    }
  };
  walk(value);
  return found;
}

export function dataStatus(value: unknown): DataStatus {
  return collectProvenance(value).some(isMock) ? "contains_mock" : "no_mock";
}

/** Throws if any provenance in `value` violates an invariant. Call on every API payload. */
export function assertTrustworthy(value: unknown): void {
  const problems = collectProvenance(value).flatMap(provenanceViolations);
  if (problems.length) throw new Error(`Untrustworthy provenance: ${problems.join("; ")}`);
}
