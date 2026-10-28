import type { Provenance } from "@corvo/contracts/types";
import { badgeModel } from "./badge.ts";

export function ProvenanceBadge({ provenance }: { provenance: Provenance }) {
  const m = badgeModel(provenance);
  return (
    <span className={`prov prov-${m.tone}`} title={m.title}>
      {m.label}
    </span>
  );
}

/** Persistent, non-dismissable banner shown whenever any MOCK data is on screen. */
export function MockBanner() {
  return (
    <div className="mock-banner" role="status">
      MOCK DATA — placeholder values, not real observations
    </div>
  );
}
