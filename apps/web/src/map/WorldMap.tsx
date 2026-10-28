// M0 stub: a MapLibre canvas with the two pilot regions as clickable points.
// No basemap and no globe projection yet - real imagery (NASA GIBS) and globe come in M1.
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import type { RegionSummary } from "../api.ts";

interface Props {
  regions: RegionSummary[];
  onSelect: (id: string) => void;
}

export function WorldMap({ regions, onSelect }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: {
        version: 8,
        sources: {},
        layers: [{ id: "bg", type: "background", paint: { "background-color": "#0b1d2a" } }],
      },
      center: [34, 37],
      zoom: 5,
    });
    map.on("load", () => {
      map.addSource("regions", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: regions.map((r) => ({
            type: "Feature",
            properties: { id: r.id, name: r.name },
            geometry: { type: "Point", coordinates: r.center },
          })),
        },
      });
      map.addLayer({
        id: "regions",
        type: "circle",
        source: "regions",
        paint: { "circle-radius": 9, "circle-color": "#f2b84b", "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
      });
      map.on("click", "regions", (e) => {
        const id = e.features?.[0]?.properties?.id;
        if (typeof id === "string") onSelect(id);
      });
      map.on("mouseenter", "regions", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "regions", () => (map.getCanvas().style.cursor = ""));
    });
    return () => map.remove();
  }, [regions, onSelect]);

  return <div ref={ref} className="world-map" />;
}
