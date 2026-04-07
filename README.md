# Slope64 API

FastAPI wrapper around Griffiths' [Slope64](https://inside.mines.edu/~vgriffit/slope64/) FEM slope stability program.
Runs the original Windows binary via Wine on Linux, exposing a simple HTTP interface.

---

## Web UI

A browser-based GUI is served at `http://localhost:8110/` alongside the API.
It works on both desktop and mobile.

### Running an example

1. Open `http://<host>:8110/` in your browser.
2. The **Examples** tab is selected by default. Choose one of the seven bundled cases from the dropdown — each is labelled with its key parameters.
3. Tap **Run analysis**. Results appear below within a few seconds.

### Uploading your own file

1. Switch to the **Upload .dat** tab.
2. Tap the file area (or drag and drop on desktop) and select your `.dat` file.
3. Tap **Run analysis**.

### Reading the results

- **Factor of Safety** — displayed large with a colour-coded badge:
  - Green **Stable** — FoS ≥ 1.5
  - Amber **Marginal** — 1.2 ≤ FoS < 1.5
  - Red **Unstable** — FoS < 1.2
- **Strength Reduction Steps** — each trial SRF value, the maximum nodal displacement, iteration count, and whether that step converged. A ✓ means the mesh converged within the iteration limit; ✗ means it did not (typically the final bracketing step beyond the true FoS).
- **Show full output** — expands the raw `.res` text from Slope64, including the full trial factor table and program header.

### Mobile

The UI is optimised for phones. Add it to your home screen (iOS: Share → Add to Home Screen; Android: browser menu → Install app) for a full-screen experience.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/run` | Upload a `.dat` file, returns FoS + full output |
| `POST` | `/run/{example}` | Run a bundled example (`ex1`–`ex7`) |
| `GET` | `/examples` | List available examples |
| `GET` | `/health` | Health check |

### Response format

```json
{
  "fos": 1.56,
  "srf_steps": [
    {"srf": 0.5,    "max_disp": 0.0305, "iterations": 2},
    {"srf": 1.0,    "max_disp": 0.0305, "iterations": 7},
    {"srf": 1.5625, "max_disp": 0.0403, "iterations": 1000}
  ],
  "res": "   _____ _      ____  ...\nEstimated Factor of Safety =      1.56",
  "output_files": {
    "res": "...",
    "msh": "...",
    "dis": "...",
    "vec": "..."
  }
}
```

---

## Run

### Direct

```bash
# 1. Download the binary from Griffiths' site
mkdir -p bin
curl -o bin/slope64.exe https://inside.mines.edu/~vgriffit/slope64/slope64.exe

# 2. Install Wine
sudo apt install wine wine32:i386

# 3. Install Python deps and run
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8110
```

### Docker

```bash
docker build -t slope64-api .
docker run -p 8110:8110 slope64-api
```

### Test

```bash
# Run example 1
curl -X POST http://localhost:8110/run/ex1 | python3 -m json.tool

# Upload your own .dat file
curl -X POST http://localhost:8110/run -F "file=@myslope.dat"
```

---

## Credit

Slope64 is the work of **D.V. Griffiths** (Colorado School of Mines).
The binary is downloaded from [inside.mines.edu/~vgriffit/slope64/](https://inside.mines.edu/~vgriffit/slope64/).

Reference: Griffiths, D.V. & Lane, P.A. (1999). *Slope stability analysis by finite elements.*
Géotechnique, 49(3), 387–403. [doi:10.1680/geot.1999.49.3.387](https://doi.org/10.1680/geot.1999.49.3.387)

This repo contains only a thin API wrapper. All analytical credit belongs to Griffiths.
