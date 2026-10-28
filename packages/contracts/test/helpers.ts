import { readFileSync } from "node:fs";
import type { RegionPack } from "../src/types.gen.ts";

export const load = (name: string): RegionPack =>
  JSON.parse(readFileSync(new URL(`../fixtures/${name}.mock.json`, import.meta.url), "utf8"));
export const clone = <T>(x: T): T => JSON.parse(JSON.stringify(x));
