"""Slope64 FastAPI wrapper — runs slope64.exe via Wine and returns results."""
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List, Literal, Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

log = logging.getLogger(__name__)

SLOPE64_EXE = Path(__file__).parent / "bin" / "slope64.exe"
EXAMPLES_DIR = Path(__file__).parent / "examples"
MANUAL_PATH = Path(__file__).parent / "manual" / "manual.txt"

DB_DSN = "host=127.0.0.1 dbname=slope64 user=postgres"

@contextmanager
def get_db():
    conn = psycopg2.connect(DB_DSN)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

app = FastAPI(title="Slope64 API", description="FEM slope stability via Griffiths' Slope64")

# CORS — same-origin only (UI is served from the same host)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # no cross-origin access
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

# Load manual once at startup
_MANUAL_TEXT = MANUAL_PATH.read_text() if MANUAL_PATH.exists() else ""

_SYSTEM_PROMPT = f"""You are a technical assistant for Slope64, a finite element slope stability
program written by D.V. Griffiths (Colorado School of Mines). You answer questions strictly based
on the official Slope64 user manual reproduced below. Do not speculate beyond its content.
If the answer is not covered by the manual, say so clearly.

--- SLOPE64 USER MANUAL ---
{_MANUAL_TEXT}
--- END OF MANUAL ---"""


def run_slope64(dat_path: Path) -> dict:
    """Run slope64.exe on a .dat file, return parsed results."""
    # Validate filename to prevent shell injection and path traversal
    if not dat_path.exists():
        raise HTTPException(404, detail="Input file not found")

    # Ensure dat_path is a child of a safe working directory (not traversed)
    workdir = dat_path.parent
    try:
        dat_path.resolve().relative_to(workdir.resolve())
    except ValueError:
        raise HTTPException(400, detail="Invalid file path")

    stem = dat_path.stem
    # Validate stem: alphanumeric, underscore, hyphen only
    if not re.match(r'^[a-zA-Z0-9_-]+$', stem):
        raise HTTPException(400, detail="Invalid filename: only alphanumeric, underscore, and hyphen allowed")

    result = subprocess.run(
        ["wine", str(SLOPE64_EXE), stem],
        capture_output=True,
        text=True,
        cwd=workdir,
        timeout=300,
        env={"WINEDEBUG": "-all", "HOME": str(Path.home()), "PATH": "/usr/bin:/bin"},
    )

    # All output goes to the .res file; stdout is typically empty
    res_path = workdir / f"{stem}.res"
    if not res_path.exists():
        raise HTTPException(500, detail=f"slope64 produced no output — returncode={result.returncode}")

    res_text = res_path.read_text(encoding="latin-1", errors="replace")

    # Parse FoS: "Estimated Factor of Safety =      1.56"
    fos_match = re.search(r"Estimated Factor of Safety\s*=\s*([\d.]+)", res_text)
    fos = float(fos_match.group(1)) if fos_match else None

    # Parse trial factor table:
    # "    0.5000      0.3050E-01              2"
    trial_rows = re.findall(
        r"^\s+([\d.]+)\s+([\d.E+\-]+)\s+(\d+)\s*$", res_text, re.MULTILINE
    )
    srf_steps = [
        {"srf": float(r[0]), "max_disp": float(r[1]), "iterations": int(r[2])}
        for r in trial_rows
    ]

    # Collect all output files produced by the exe (5 MB cap per file)
    MAX_OUTPUT_SIZE = 20 * 1024 * 1024
    output_files = {}
    for ext in (".res", ".msh", ".dis", ".vec"):
        f = workdir / f"{stem}{ext}"
        if f.exists() and 2 < f.stat().st_size <= MAX_OUTPUT_SIZE:
            output_files[ext.lstrip(".")] = f.read_text(encoding="latin-1", errors="replace")

    return {
        "fos": fos,
        "srf_steps": srf_steps,
        "res": res_text,
        "output_files": output_files,
    }


def _store_result(transect_id: int, result: dict, filename: str):
    """Write FoS + SRF steps back to the transect row in PostGIS."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE slope_analyses
                SET fos = %s, srf_steps = %s, dat_filename = %s
                WHERE id = %s
                """,
                (result.get("fos"), json.dumps(result.get("srf_steps", [])), filename, transect_id),
            )
    except Exception as e:
        log.warning("Failed to store result for transect_id=%s: %s", transect_id, e)


@app.post("/run")
async def run_uploaded(file: UploadFile = File(...), transect_id: Optional[int] = Form(None)):
    """Upload a .dat file and run Slope64. Optionally link to a saved transect."""
    if not file.filename.endswith(".dat"):
        raise HTTPException(400, detail="File must be a .dat file")

    MAX_FILE_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, detail=f"File too large (max {MAX_FILE_SIZE // (1024*1024)} MB)")

    with tempfile.TemporaryDirectory() as tmpdir:
        dat_path = Path(tmpdir) / "input.dat"
        dat_path.write_bytes(content)
        result = run_slope64(dat_path)

    if transect_id is not None:
        _store_result(transect_id, result, file.filename)

    return result


@app.post("/run/{example}")
def run_example(example: str, transect_id: Optional[int] = None):
    """Run one of the bundled example cases (ex1–ex7). Optionally link to a saved transect."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', example):
        raise HTTPException(400, detail="Invalid example name: only alphanumeric, underscore, and hyphen allowed")

    src = EXAMPLES_DIR / f"{example}.dat"

    try:
        src.resolve().relative_to(EXAMPLES_DIR.resolve())
    except ValueError:
        raise HTTPException(400, detail="Invalid example path")

    if not src.exists():
        raise HTTPException(404, detail=f"Example '{example}' not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        dat_path = Path(tmpdir) / f"{example}.dat"
        shutil.copy(src, dat_path)
        result = run_slope64(dat_path)

    if transect_id is not None:
        _store_result(transect_id, result, f"{example}.dat")

    return result


@app.get("/examples")
def list_examples():
    """List bundled example .dat files."""
    return [p.stem for p in sorted(EXAMPLES_DIR.glob("*.dat"))]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class AskRequest(BaseModel):
    messages: List[Message]  # full conversation history


@app.post("/ask")
async def ask(req: AskRequest):
    """Answer questions from the Slope64 manual using OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, detail="OPENAI_API_KEY not set")

    try:
        from openai import OpenAI
        from openai import APIError

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": _SYSTEM_PROMPT}]
                     + [{"role": m.role, "content": m.content} for m in req.messages],
            temperature=0.2,
            max_tokens=1024,
        )
        return {"reply": response.choices[0].message.content}
    except KeyError:
        # Malformed request
        raise HTTPException(400, detail="Invalid request format")
    except APIError as e:
        # OpenAI API errors: do not expose details that might contain credentials
        raise HTTPException(500, detail="OpenAI API error: please check the server logs")
    except Exception as e:
        # Generic errors: log internally, return safe message
        import logging
        logging.error(f"Unexpected error in /ask: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(500, detail="Internal server error")


class TransectRequest(BaseModel):
    name: Optional[str] = None
    geojson: dict  # GeoJSON LineString feature or geometry


@app.post("/transect")
def save_transect(req: TransectRequest):
    """Save a drawn transect (GeoJSON LineString) to PostGIS. Returns the new row ID."""
    geom = req.geojson
    # Accept either a Feature or bare geometry
    if geom.get("type") == "Feature":
        geom = geom["geometry"]
    if geom.get("type") != "LineString":
        raise HTTPException(400, detail="geometry must be a LineString")
    if len(geom.get("coordinates", [])) < 2:
        raise HTTPException(400, detail="LineString must have at least 2 points")

    geojson_str = json.dumps(geom)
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO slope_analyses (name, transect)
                VALUES (%s, ST_GeomFromGeoJSON(%s))
                RETURNING id
                """,
                (req.name or "Unnamed", geojson_str),
            )
            row_id = cur.fetchone()[0]
    except Exception as e:
        log.error("Failed to save transect: %s", e, exc_info=True)
        raise HTTPException(500, detail="Failed to save transect")

    return {"id": row_id}


@app.get("/transects")
def get_transects():
    """Return all analyses as a GeoJSON FeatureCollection."""
    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                """
                SELECT id, name, fos, dat_filename,
                       to_char(created_at, 'YYYY-MM-DD HH24:MI') AS created_at,
                       ST_AsGeoJSON(transect)::json AS geometry
                FROM slope_analyses
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()
    except Exception as e:
        log.error("Failed to load transects: %s", e, exc_info=True)
        raise HTTPException(500, detail="Failed to load transects")

    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "id": row["id"],
                "name": row["name"],
                "fos": row["fos"],
                "dat_filename": row["dat_filename"],
                "created_at": row["created_at"],
            },
        })

    return JSONResponse({"type": "FeatureCollection", "features": features})


@app.get("/health")
def health():
    return {"status": "ok", "exe_exists": SLOPE64_EXE.exists()}


STATIC_DIR = Path(__file__).parent / "static"

@app.get("/manifest.json")
def manifest():
    return FileResponse(str(STATIC_DIR / "manifest.json"), media_type="application/manifest+json")

# Serve static UI if present
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8110)
