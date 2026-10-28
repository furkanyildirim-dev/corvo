"""FastAPI entry point (thin layer over registry + contracts).

STATUS (M0): written but NOT executed in the build sandbox (fastapi could not be installed
there). Run `pytest` + `uvicorn corvo_api.main:app` on a machine with network access.
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .contracts import RegionPack, SimRequest, SimState, data_status
from .registry import RegionSummary, load_pack, summaries

app = FastAPI(title="CORVO API", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/regions", response_model=list[RegionSummary])
def list_regions() -> list[RegionSummary]:
    return summaries()


@app.get("/regions/{region_id}", response_model=RegionPack)
def get_region(region_id: str, response: Response) -> RegionPack:
    try:
        pack = load_pack(region_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown region {region_id!r}") from None
    response.headers["X-Corvo-Data-Status"] = data_status(pack)
    return pack


@app.post("/simulate", response_model=SimState)
def simulate(_: SimRequest) -> SimState:
    # Body validation (422) already works. The engine arrives in M4 (mock) and M7 (AquaCrop).
    raise HTTPException(status_code=501, detail="Simulation engine not implemented yet (M4).")
