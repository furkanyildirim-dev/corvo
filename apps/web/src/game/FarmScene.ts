// M0 stub: draws the pack's parcels as placeholder rectangles. It READS the pack and never
// computes science. Real art (style decision D11) and gameplay arrive in M1/M2.
import Phaser from "phaser";
import { dataStatus, safeLabel } from "@corvo/contracts";
import type { RegionPack } from "@corvo/contracts";
import { bboxOf, makeProjector, type LonLat } from "./projection.ts";

export const PACK_KEY = "pack";

export class FarmScene extends Phaser.Scene {
  constructor() {
    super("farm");
  }

  create(): void {
    const pack = this.registry.get(PACK_KEY) as RegionPack;
    const { width, height } = this.scale;
    const rings = pack.parcels.parcels.flatMap((p) => p.ring as LonLat[]);
    const project = makeProjector(bboxOf(rings), width, height, 48);

    this.cameras.main.setBackgroundColor("#2f4a2c");
    const g = this.add.graphics();
    for (const parcel of pack.parcels.parcels) {
      const pts = parcel.ring.map((r) => project(r as LonLat));
      g.fillStyle(0x8a6d3b, 1).fillPoints(pts, true);
      g.lineStyle(2, 0xf2e6c4, 1).strokePoints(pts, true);
      const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
      const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
      this.add
        .text(cx, cy, `${parcel.name}\n${parcel.area_ha.toFixed(0)} ha`, {
          fontFamily: "monospace", fontSize: "14px", color: "#fff", align: "center",
        })
        .setOrigin(0.5);
    }

    // Every scene states what its data is. Mock data gets a loud ribbon.
    const label = safeLabel(pack.parcels.provenance);
    const ribbon = dataStatus(pack) === "contains_mock" ? `${label} PARCELS (placeholder)` : label;
    this.add.text(12, 10, ribbon, { fontFamily: "monospace", fontSize: "16px", color: "#ffd166" });
  }
}
