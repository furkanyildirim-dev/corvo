# M0 status — what actually ran, what did not

Last verified: 2026-10-28, in the build sandbox. **That sandbox could not reach pypi.org or registry.npmjs.org**
(proxy policy denial, HTTP 403), so no packages were installed. Only tools already on the machine were used.

## Verified by running

| Area | Result |
|---|---|
| Python contracts + mock packs + registry (`services/api/tests`) | **61 passed** (pytest, pydantic 2.13, jsonschema 4.26) |
| JSON Schema accepts Python output; schema is strict; committed contract files are not stale | passed (inside the 61) |
| TypeScript provenance guard + fixtures (`packages/contracts/test`) | **12 passed** (Node 22 `node --test`) |
| Python ↔ TypeScript agree on every provenance case (drift detector) | passed (inside the 12) |
| Web pure logic: projection + badge model (`apps/web/src/**/*.test.ts`) | **8 passed** |
| `tsc --strict` on generated types, provenance guard, projection, badge | 0 errors |
| Generated TS types are up to date (`python tools/export_contracts.py --check`) | up to date |

## Written but NOT executed or compiled

| File(s) | Why not | What to run |
|---|---|---|
| `services/api/corvo_api/main.py` (FastAPI) | `fastapi`, `httpx` not installable | `pip install -e "services/api[dev]"` then `uvicorn corvo_api.main:app` |
| `packages/contracts/src/validate.ts` + `test/validate.test.ts` (ajv 8) | sandbox only had ajv 6 | `npm install` then `npm test -w @corvo/contracts` |
| `apps/web` React / Phaser / MapLibre / Vite shell | packages not installable; never built or opened in a browser | `npm install && npm run build && npm run dev:web` |
| `tools/probes/*` (POWER, CMR, AquaCrop) | no network / no pip | see `PROBES.md` |

Treat the "not executed" files as unreviewed drafts: they may need small fixes at first build
(import-attribute handling in Vite, Phaser typings, ajv ESM interop are the likeliest spots).

## Sandbox-only helpers (not committed)

`packages/contracts/node_modules` and `apps/web/node_modules/*` are symlinks to the machine's global tools,
used only to run the tests above. `.gitignore` excludes them; a real `npm install` replaces them.

## Export for local development (post-M0)
- Cross-platform script launcher `tools/py.mjs`; globs quoted; TypeScript ^5.8; `engines.node >=22.18`.
- `.env.example` files, `.gitattributes`, shared `.vscode` settings, `README_RUN_LOCAL.md`.
- `docs/CONTRACT_GAPS.md`: farmer priorities missing; soil/crop/rotation partial.
- Re-verified in sandbox: gen:check, 61 pytest, 12 contracts guard tests, 8 web tests.
- Still NOT executed: FastAPI app, ajv-based validate.test.ts, typecheck/build/dev of the web app.
