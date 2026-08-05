"""Download and extract a Statistics Canada full-table CSV bundle.

The script uses the public Statistics Canada Web Data Service (WDS):
https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/{pid}/en
"""

from __future__ import annotations

import argparse
import json
import shutil
import ssl
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_STATCAN_DIR = PROJECT_ROOT / "data" / "raw" / "statcan"


def ssl_context(allow_insecure_ssl: bool) -> ssl.SSLContext | None:
    if allow_insecure_ssl:
        return ssl._create_unverified_context()
    return None


def wds_download_url(pid: str, language: str, context: ssl.SSLContext | None) -> str:
    endpoint = (
        "https://www150.statcan.gc.ca/t1/wds/rest/"
        f"getFullTableDownloadCSV/{pid}/{language}"
    )
    with urllib.request.urlopen(endpoint, timeout=60, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("status") != "SUCCESS":
        raise RuntimeError(f"StatsCan WDS request failed: {payload}")
    return payload["object"]


def download_file(url: str, destination: Path, context: ssl.SSLContext | None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120, context=context) as response:
        with destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)


def extract_zip(zip_path: Path, extract_dir: Path) -> list[str]:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)
        return archive.namelist()


def write_manifest(
    manifest_path: Path,
    *,
    pid: str,
    language: str,
    wds_url: str,
    zip_path: Path,
    extracted_files: list[str],
) -> None:
    manifest = {
        "pid": pid,
        "language": language,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "wds_url": wds_url,
        "zip_path": str(zip_path.relative_to(PROJECT_ROOT)),
        "extracted_files": extracted_files,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", required=True, help="StatsCan product ID, e.g. 23100253")
    parser.add_argument("--language", default="en", choices=["en", "fr"])
    parser.add_argument(
        "--allow-insecure-ssl",
        action="store_true",
        help="Disable SSL verification for local environments with broken certificate chains.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pid = args.pid
    language = args.language
    table_dir = RAW_STATCAN_DIR / pid
    zip_path = table_dir / f"{pid}-{language}.zip"
    context = ssl_context(args.allow_insecure_ssl)

    wds_url = wds_download_url(pid, language, context)
    download_file(wds_url, zip_path, context)
    extracted_files = extract_zip(zip_path, table_dir)
    write_manifest(
        table_dir / "manifest.json",
        pid=pid,
        language=language,
        wds_url=wds_url,
        zip_path=zip_path,
        extracted_files=extracted_files,
    )

    print(f"Downloaded {pid} to {zip_path}")
    print("Extracted:")
    for file_name in extracted_files:
        print(f"- {file_name}")


if __name__ == "__main__":
    main()
