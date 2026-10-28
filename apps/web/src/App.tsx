import type { DataStatus, RegionPack } from "@corvo/contracts";
import { useCallback, useEffect, useState } from "react";
import { getRegionPack, getRegions, type RegionSummary } from "./api.ts";
import { MockBanner, ProvenanceBadge } from "./components/ProvenanceBadge.tsx";
import { FarmCanvas } from "./game/FarmCanvas.tsx";
import { WorldMap } from "./map/WorldMap.tsx";

type View = { kind: "world" } | { kind: "farm"; pack: RegionPack; status: DataStatus };

export function App() {
  const [regions, setRegions] = useState<RegionSummary[]>([]);
  const [view, setView] = useState<View>({ kind: "world" });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRegions().then(setRegions).catch((e: Error) => setError(e.message));
  }, []);

  const enter = useCallback((id: string) => {
    getRegionPack(id)
      .then(({ pack, status }) => setView({ kind: "farm", pack, status }))
      .catch((e: Error) => setError(e.message));
  }, []);

  const anyMock =
    regions.some((r) => r.data_status === "contains_mock") ||
    (view.kind === "farm" && view.status === "contains_mock");

  return (
    <div className="app">
      {anyMock && <MockBanner />}
      {error && <div className="error">{error}</div>}
      {view.kind === "world" ? (
        <WorldMap regions={regions} onSelect={enter} />
      ) : (
        <>
          <FarmCanvas pack={view.pack} />
          <div className="hud">
            <button onClick={() => setView({ kind: "world" })}>← World</button>
            <strong>{view.pack.name}</strong>
            <ProvenanceBadge provenance={view.pack.parcels.provenance} />
            <ProvenanceBadge provenance={view.pack.climate.provenance} />
          </div>
        </>
      )}
    </div>
  );
}
