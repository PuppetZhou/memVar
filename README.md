# memVar local website

The local release candidate serves the read-only API and Next.js website from
one explicit, immutable serving release. Scientific data is stored outside the
code worktree and is never committed to Git.

## Python environment

The website is run from this local checkout; it is not published as a Python
package. Create an isolated Python 3.13 environment and install the pinned
runtime, ETL, and test dependencies from the repository root:

```bash
cd /home/xuyzh/memVar/website
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Verify the direct imports and the installed dependency graph before starting
the services:

```bash
python -c "import duckdb, fastapi, h5py, httpx, numpy, pyarrow, pydantic, pytest, starlette, uvicorn, yaml"
python -m pip check
```

## Start

Set the exact root of a complete serving release and its filesystem UUID, then
start both services:

```bash
MEMVAR_DATA_ROOT=/absolute/path/to/serve-v1.0.0 \
MEMVAR_DATA_UUID=the-filesystem-uuid \
  /home/xuyzh/memVar/website/start-local.sh
```

After v1 is signed, `MEMVAR_DATA_ROOT` changes to the published
`/media/xuyzh/Newsmy/memvar-data/serving/serve-v1.0.0` directory. Startup fails
closed when the mount UUID, `RELEASE.json`, `_READY`, or a required asset is
missing; it does not silently fall back to `website/data/generated`.
The current `serve-v1.0.0-foundation` staging directory deliberately has no
`_READY` marker while its remaining assets are being copied, so it must not be
used as a serving release yet.

When the terminal reports that memVar is ready, open:

- <http://127.0.0.1:3000>
- <http://127.0.0.1:3000/protein/P00533> for the EGFR example

Press `Ctrl+C` once in the same terminal to stop both the frontend and API.
The script checks Python and frontend dependencies, the configured data
release, its core catalog, and port availability before startup.

Optional local overrides:

```bash
MEMVAR_DATA_ROOT=/absolute/path/to/serve-v1.0.0 \
MEMVAR_DATA_UUID=the-filesystem-uuid \
MEMVAR_API_PORT=8100 MEMVAR_WEB_PORT=3100 \
  /home/xuyzh/memVar/website/start-local.sh
```

The default bind address is `127.0.0.1`, so the site is available only on the
local machine. Set `MEMVAR_LOCAL_HOST` explicitly only when another bind
address is intentionally required.

Browser data requests stay on the website origin under `/api/v1`. Next.js
forwards them to the loopback FastAPI process with server-only configuration,
so desktop preview proxies and their temporary ports do not require CORS
allowlists or expose the backend address to browser code.

## Verify the backend

```bash
cd /home/xuyzh/memVar/website/backend
python -m pytest -q
```

The full-stack network regression starts isolated temporary ports, verifies
Search, Protein overview, and ranged PDB access through the website origin, and
then shuts both processes down:

```bash
python /home/xuyzh/memVar/website/tests/verify_local_stack.py
```

## Build the local AlphaFold v6 structure release

The structure builder reads the canonical membrane-protein allowlist from
`View/Basic_info/protein_basic.parquet`, validates every selected PDB gzip and
publishes only generated data under `website/data/generated/structure/`.
The supplied human v6 archive has an audited damaged prefix, so recovery must
be requested explicitly:

```bash
cd /home/xuyzh/memVar
python website/etl/build_structure.py --recover-prefix
```

Without `--recover-prefix`, the builder intentionally rejects this archive.
The release retains the official compressed PDB filenames and writes
`manifest.parquet` plus `missing_accessions.parquet`; it never modifies the
source tar or anything under `View/`.

## Build ThermoMPNN stability and anatomy summaries

ThermoMPNN source files remain immutable. The first command validates the
protein-specific prediction identity and writes only bucketed website data;
the second builds the explicit cross-source anatomy availability summary from
existing website marts:

```bash
cd /home/xuyzh/memVar/website
python etl/build_thermompnn.py --threads 8
python etl/build_anatomy.py
```

The 31 current predictions whose reference residue does not match the website
canonical sequence remain available in the Variant branch but are excluded
from the Sequence track rather than being drawn at an invalid residue.
