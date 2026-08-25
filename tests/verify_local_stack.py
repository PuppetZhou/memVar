"""Full-stack regression check for same-origin browser data access."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


WEBSITE_ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def request(url: str, *, headers: dict[str, str] | None = None):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=headers or {}),
        timeout=5,
    )


def main() -> None:
    api_port = free_port()
    web_port = free_port()
    while web_port == api_port:
        web_port = free_port()
    next_dist_dir = f".next-stack-{os.getpid()}-{web_port}"
    tsconfig_path = WEBSITE_ROOT / "frontend" / "tsconfig.json"
    original_tsconfig = tsconfig_path.read_bytes()

    environment = {
        **os.environ,
        "MEMVAR_API_PORT": str(api_port),
        "MEMVAR_WEB_PORT": str(web_port),
        "MEMVAR_NEXT_DIST_DIR": next_dist_dir,
    }
    with tempfile.TemporaryFile(mode="w+") as log:
        process = subprocess.Popen(
            [str(WEBSITE_ROOT / "start-local.sh")],
            cwd=WEBSITE_ROOT,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            base = f"http://127.0.0.1:{web_port}"
            deadline = time.monotonic() + 40
            while True:
                if process.poll() is not None:
                    raise RuntimeError("Local stack stopped during startup")
                try:
                    with request(f"{base}/api/v1/proteins/P00533") as response:
                        if response.status == 200:
                            break
                except (OSError, urllib.error.URLError):
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError("Same-origin protein endpoint was not ready within 40 seconds")
                time.sleep(0.2)

            with request(
                f"{base}/api/v1/proteins/P00533",
                headers={"Origin": "http://localhost:63884", "Accept": "application/json"},
            ) as response:
                overview = json.load(response)
                assert response.status == 200
                assert overview["uniprot_accession"] == "P00533"
                assert overview["gene_symbol"] == "EGFR"

            with request(f"{base}/api/v1/proteins/A0A087X1C5") as response:
                sparse = json.load(response)
                assert response.status == 200
                assert sparse["uniprot_accession"] == "A0A087X1C5"

            opener = urllib.request.build_opener(NoRedirect)
            try:
                opener.open(f"{base}/search?q=P00533", timeout=5)
                raise AssertionError("Exact search did not redirect")
            except urllib.error.HTTPError as response:
                assert response.code == 307
                assert response.headers["Location"] == "/protein/P00533"

            with request(f"{base}/search?q=SHORT") as response:
                ambiguous_page = response.read().decode("utf-8")
                assert response.status == 200
                assert "Choose a protein entry" in ambiguous_page

            with request(f"{base}/search?q=MEMVAR_NO_SUCH_PROTEIN") as response:
                empty_page = response.read().decode("utf-8")
                assert response.status == 200
                assert "No matching reviewed protein entry" in empty_page

            with request(
                f"{base}/api/v1/proteins/P00533/structures/1/pdb",
                headers={"Range": "bytes=0-9"},
            ) as response:
                assert response.status == 206
                assert response.headers["Content-Range"].startswith("bytes 0-9/")
                assert len(response.read()) == 10

            with request(f"{base}/api/v1/proteins/P00533/alphagenome/summary") as response:
                alpha_summary = json.load(response)
                assert response.status == 200
                assert alpha_summary["availability"] == "available"
                assert alpha_summary["prediction_kind"] == "reference_sequence_tracks"

            with request(f"{base}/api/v1/proteins/P00533/anatomy/summary") as response:
                anatomy = json.load(response)
                assert response.status == 200
                assert anatomy["fill_semantics"] == "availability_or_selection_only"
                assert anatomy["cross_modality_score"] is False

            with request(
                f"{base}/api/v1/variants/7-55156538-A-C/evidence/stability?protein_accession=P00533"
            ) as response:
                variant = json.load(response)
                assert response.status == 200
                stability = variant["prediction"]
                assert stability["model_name"] == "ThermoMPNN"
                assert stability["unit"] == "kcal/mol"
                assert abs(stability["ddg"] - (-0.06067943572998047)) < 1e-9

            with request(
                f"{base}/api/v1/proteins/P00533/alphagenome/signals"
                "?ensembl_gene_id=ENSG00000146648&tile_id=tile_000"
                "&track_id=rna_seq%3A000&bins=256"
            ) as response:
                alpha_signal = json.load(response)
                assert response.status == 200
                assert len(alpha_signal["values"]) == 256
        except Exception:
            log.seek(0)
            print(log.read())
            raise
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            shutil.rmtree(WEBSITE_ROOT / "frontend" / next_dist_dir, ignore_errors=True)
            if tsconfig_path.read_bytes() != original_tsconfig:
                tsconfig_path.write_bytes(original_tsconfig)

    print("same-origin local stack regression passed")


if __name__ == "__main__":
    main()
