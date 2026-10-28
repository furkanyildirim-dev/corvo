import type { RegionPack } from "@corvo/contracts";
import Phaser from "phaser";
import { useEffect, useRef } from "react";
import { FarmScene, PACK_KEY } from "./FarmScene.ts";

export function FarmCanvas({ pack }: { pack: RegionPack }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: ref.current,
      width: ref.current.clientWidth,
      height: ref.current.clientHeight,
      backgroundColor: "#1c2a1a",
      scene: [FarmScene],
      // The pack must be in the registry before the scene's create() runs.
      callbacks: { preBoot: (g) => g.registry.set(PACK_KEY, pack) },
    });
    return () => game.destroy(true);
  }, [pack]);

  return <div ref={ref} className="farm-canvas" />;
}
