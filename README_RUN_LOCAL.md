# CORVO M0 — run locally (Windows + VS Code)

State of this code, honestly:

| Part | Status |
|---|---|
| Python contracts + 61 pytest tests | **Ran and passed** in the build sandbox |
| `npm run gen:check` | **Ran and passed** in the sandbox |
| `@corvo/contracts` guard tests (12) | **Ran and passed** (`provenance.test.ts`, `fixtures.test.ts`) |
| `apps/web` unit tests (8) | **Ran and passed** |
| FastAPI app (`corvo_api.main`) | **Never executed** (fastapi could not be installed in the sandbox) |
| `validate.test.ts` (ajv 8) | **Never executed** (needs ajv 8) |
| Vite / React / Phaser / MapLibre web app | **Never built or opened** |
| `npm run typecheck` / `build` | **Never run** with the full dependency set |

Expect that the first `npm install` + `build`/`dev:web` may reveal errors. Please send them back (see the end).

## 1. Install prerequisites
- **Node.js ≥ 22.18** (LTS 22.x or newer; needed to run `.ts` tests directly). Check: `node --version`
- **Python ≥ 3.12** from python.org (tick "Add python.exe to PATH" / keep the `py` launcher). Check: `py -3 --version`
- **Git** (only if using the bundle).
- VS Code with the *Python* extension (recommended extensions are suggested automatically).

## 2. Get the code
Either unzip `CORVO_M0_Source.zip` (creates a `corvo` folder), or restore history from the bundle:
```powershell
git clone CORVO_M0.bundle corvo
```
Then `code corvo` (or File → Open Folder).

## 3. Python environment (PowerShell, repo root)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, reopen the terminal.
```powershell
python -m pip install --upgrade pip
pip install -e "services/api[dev]"
```
In VS Code choose the interpreter `.venv\Scripts\python.exe` (Ctrl+Shift+P → Python: Select Interpreter).
Keep the venv **activated** in the terminal where you run npm scripts; they pick it up automatically.

## 4. Node dependencies (repo root)
```powershell
npm install
```

## 5. Test
```powershell
npm run gen:check       # generated contracts match the Python models
npm run test:api        # expected: 61 passed   (not yet verified on your machine)
npm run test:contracts  # 12 guard tests + 5 ajv tests in validate.test.ts (the 5 never ran before)
npm run test:web        # expected: 8 passed
npm run typecheck       # never run before — may report errors
```
After changing a Python contract: `npm run gen`, then commit the regenerated files.

## 6. Run
Two terminals (the Python venv activated in the first):
```powershell
npm run dev:api   # http://127.0.0.1:8000/health , /regions , /regions/cukurova
npm run dev:web   # http://localhost:5173  (proxies /api to the API)
```
`/simulate` intentionally returns 501: no simulation engine in M0. All region data is labelled **MOCK**.

## 7. Configuration
See `.env.example` and `apps/web/.env.example`. Only `CORVO_REGION_DIR` (API), `VITE_API_BASE` (web) and
the optional `CORVO_PYTHON` are used. No secrets are needed or included. `.env` files are not auto-loaded by the API;
set variables in the shell (`$env:CORVO_REGION_DIR = "..."`).

## 8. Troubleshooting
- `Python 3.12+ not found` → install Python, or `$env:CORVO_PYTHON = "C:\...\python.exe"`.
- `ModuleNotFoundError: fastapi` → venv not active or step 3 pip install skipped.
- Tests with `.ts` fail with a syntax/flag error → Node is older than 22.18.
- `npm install` peer/engine errors → send the full output.
- Line endings: the repo uses LF (`.gitattributes`); `gen:check` compares generated files byte-wise.

## 9. If something fails
Send back: the exact command, the full error output, `node --version`, `py -3 --version`, `npm --version`.
Do not treat any item marked "never executed" above as working.
