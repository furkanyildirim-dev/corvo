// Pure lon/lat -> canvas math for the farm view (no Phaser import, so it is unit-testable).
// M0 uses a local equirectangular fit; at parcel scale (a few km) the error is negligible.
// M2 replaces this with the region's projected CRS (RegionPack.site.local_epsg).

export type LonLat = readonly [number, number];
export type BBox = readonly [number, number, number, number]; // west, south, east, north
export interface Point {
  x: number;
  y: number;
}

/** Fit `bbox` into a width x height canvas, preserving aspect ratio, north up, with padding. */
export function makeProjector(bbox: BBox, width: number, height: number, padPx = 24) {
  const [west, south, east, north] = bbox;
  const midLat = ((south + north) / 2) * (Math.PI / 180);
  const spanX = (east - west) * Math.cos(midLat); // degrees of longitude shrink with latitude
  const spanY = north - south;
  const scale = Math.min((width - 2 * padPx) / spanX, (height - 2 * padPx) / spanY);
  const offX = (width - spanX * scale) / 2;
  const offY = (height - spanY * scale) / 2;
  return (p: LonLat): Point => ({
    x: offX + (p[0] - west) * Math.cos(midLat) * scale,
    y: offY + (north - p[1]) * scale,
  });
}

/** Bounding box of a set of lon/lat points. */
export function bboxOf(points: readonly LonLat[]): BBox {
  const lons = points.map((p) => p[0]);
  const lats = points.map((p) => p[1]);
  return [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)];
}
