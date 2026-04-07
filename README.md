# Slope64 API

FastAPI wrapper around Griffiths' [Slope64](https://inside.mines.edu/~vgriffit/slope64/) FEM slope stability program.
Runs the original Windows binary via Wine on Linux, exposing a simple HTTP interface.

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
  "fos": 1.547,
  "srf_steps": [
    {"srf": 1.0,  "iterations": 7,   "fmax": 0.40},
    {"srf": 1.5,  "iterations": 500, "fmax": 0.35},
    ...
  ],
  "stdout": "   SRF= 1.000000   ITERS=   1   FMAX= ...",
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
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8110
```

Requires `wine` and `wine32` installed (`apt install wine wine32`).

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
