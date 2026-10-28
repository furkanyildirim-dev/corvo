// Structural validation against the exported JSON Schema (ajv).
// Cross-field rules (e.g. mock must not cite a dataset) are NOT in the schema; use
// assertTrustworthy() from provenance.ts for those. Date formats are not checked here.

import Ajv2020Module from "ajv/dist/2020.js";
import schema from "../schema/corvo.schema.json" with { type: "json" };
import { assertTrustworthy } from "./provenance.ts";
import type { ClimateScenario, ManagementPlan, RegionPack, SimRequest, SimState } from "./types.gen.ts";

// ajv is CommonJS: depending on the bundler the constructor is on `.default` or the module itself.
type AjvCtor = new (opts: object) => {
  addSchema: (s: object, key: string) => void;
  getSchema: (ref: string) =>
    | (((data: unknown) => boolean) & { errors?: { instancePath: string; message?: string }[] | null })
    | undefined;
};
const Ajv = ((Ajv2020Module as unknown as { default?: AjvCtor }).default ??
  (Ajv2020Module as unknown as AjvCtor)) as AjvCtor;

const ajv = new Ajv({ strict: false, validateFormats: false, allErrors: true });
ajv.addSchema(schema, "corvo");

function makeParser<T>(def: string): (data: unknown) => T {
  const validate = ajv.getSchema(`corvo#/$defs/${def}`);
  if (!validate) throw new Error(`schema definition missing: ${def}`);
  return (data: unknown): T => {
    if (!validate(data)) {
      const msg = (validate.errors ?? []).map((e) => `${e.instancePath || "/"} ${e.message}`).join("; ");
      throw new Error(`${def} failed validation: ${msg}`);
    }
    assertTrustworthy(data);
    return data as T;
  };
}

export const parseRegionPack = makeParser<RegionPack>("RegionPack");
export const parseManagementPlan = makeParser<ManagementPlan>("ManagementPlan");
export const parseClimateScenario = makeParser<ClimateScenario>("ClimateScenario");
export const parseSimState = makeParser<SimState>("SimState");
export const parseSimRequest = makeParser<SimRequest>("SimRequest");
