// UNVERIFIED in the M0 sandbox (needs `npm install`). Every payload passes the JSON Schema AND
// the provenance guard before the UI sees it: invalid or mislabelled data is rejected, not shown.
import { dataStatus, parseRegionPack } from "@corvo/contracts";
import type { DataStatus, RegionPack } from "@corvo/contracts";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

export interface RegionSummary {
  id: string;
  name: string;
  center: [number, number];
  data_status: DataStatus;
}

async function getJson(path: string): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

export async function getRegions(): Promise<RegionSummary[]> {
  return (await getJson("/regions")) as RegionSummary[];
}

export async function getRegionPack(id: string): Promise<{ pack: RegionPack; status: DataStatus }> {
  const pack = parseRegionPack(await getJson(`/regions/${encodeURIComponent(id)}`));
  return { pack, status: dataStatus(pack) };
}
