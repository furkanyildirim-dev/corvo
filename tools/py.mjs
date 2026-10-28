// Cross-platform Python launcher used by the npm scripts:  node tools/py.mjs <python args...>
// Resolution order: $CORVO_PYTHON, the active virtualenv ($VIRTUAL_ENV), then platform defaults.
// (Windows has no `python3`; `py -3` ignores an activated venv, so the venv is checked first.)
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

const win = process.platform === "win32";
/** @type {string[][]} */
const candidates = [];
if (process.env.CORVO_PYTHON) candidates.push([process.env.CORVO_PYTHON]);
if (process.env.VIRTUAL_ENV) {
  const exe = join(process.env.VIRTUAL_ENV, win ? "Scripts/python.exe" : "bin/python");
  if (existsSync(exe)) candidates.push([exe]);
}
candidates.push(...(win ? [["py", "-3"], ["python"]] : [["python3"], ["python"]]));

for (const [cmd, ...pre] of candidates) {
  const r = spawnSync(cmd, [...pre, ...process.argv.slice(2)], { stdio: "inherit" });
  if (r.error && /** @type {NodeJS.ErrnoException} */ (r.error).code === "ENOENT") continue;
  process.exit(r.status ?? 1);
}
console.error("Python 3.12+ not found. Install it, or set CORVO_PYTHON to the python executable.");
process.exit(127);
