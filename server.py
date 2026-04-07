"""Slope64 FastAPI wrapper — runs slope64.exe via Wine and returns results."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

SLOPE64_EXE = Path(__file__).parent / "bin" / "slope64.exe"
EXAMPLES_DIR = Path(__file__).parent / "examples"

app = FastAPI(title="Slope64 API", description="FEM slope stability via Griffiths' Slope64")


def run_slope64(dat_path: Path) -> dict:
    """Run slope64.exe on a .dat file, return parsed results."""
    stem = dat_path.stem
    workdir = dat_path.parent

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

    # Collect all output files produced by the exe
    output_files = {}
    for ext in (".res", ".msh", ".dis", ".vec"):
        f = workdir / f"{stem}{ext}"
        if f.exists() and f.stat().st_size > 2:
            output_files[ext.lstrip(".")] = f.read_text(encoding="latin-1", errors="replace")

    return {
        "fos": fos,
        "srf_steps": srf_steps,
        "res": res_text,
        "output_files": output_files,
    }


@app.post("/run")
async def run_uploaded(file: UploadFile = File(...)):
    """Upload a .dat file and run Slope64."""
    if not file.filename.endswith(".dat"):
        raise HTTPException(400, detail="File must be a .dat file")

    with tempfile.TemporaryDirectory() as tmpdir:
        dat_path = Path(tmpdir) / "input.dat"
        dat_path.write_bytes(await file.read())
        return run_slope64(dat_path)


@app.post("/run/{example}")
def run_example(example: str):
    """Run one of the bundled example cases (ex1–ex7)."""
    src = EXAMPLES_DIR / f"{example}.dat"
    if not src.exists():
        raise HTTPException(404, detail=f"Example '{example}' not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        dat_path = Path(tmpdir) / f"{example}.dat"
        shutil.copy(src, dat_path)
        return run_slope64(dat_path)


@app.get("/examples")
def list_examples():
    """List bundled example .dat files."""
    return [p.stem for p in sorted(EXAMPLES_DIR.glob("*.dat"))]


@app.get("/health")
def health():
    return {"status": "ok", "exe": str(SLOPE64_EXE), "exe_exists": SLOPE64_EXE.exists()}


# Serve static UI if present
if (Path(__file__).parent / "static").exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8110)
