// Pure view-model for provenance badges (no React import, so it is unit-testable).
import { INVALID_LABEL, isMock, provenanceViolations, safeLabel } from "@corvo/contracts/provenance";
import type { Provenance } from "@corvo/contracts/types";

export type BadgeTone = "mock" | "invalid" | "real" | "generated";

export interface BadgeModel {
  label: string;
  tone: BadgeTone;
  title: string; // tooltip: where the data comes from
}

export function badgeModel(p: Provenance): BadgeModel {
  const label = safeLabel(p);
  const tone: BadgeTone =
    label === INVALID_LABEL
      ? "invalid"
      : isMock(p)
        ? "mock"
        : p.kind === "game_assumption" || p.kind === "simulated"
          ? "generated"
          : "real";
  const problems = provenanceViolations(p);
  const title =
    problems.length > 0
      ? `Invalid provenance: ${problems.join("; ")}`
      : [p.source, p.dataset_id, p.notes].filter(Boolean).join(" · ");
  return { label, tone, title };
}
