"""Build the pure-Python wheels this proof of concept loads in Pyodide.

NumPy and PyYAML come from the Pyodide build. These wheels are generated
locally and are not part of the application archive.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent / "wheels"
LIBRARY = (
    "lic-dsf-2025-08-12 @ git+https://github.com/Teal-Insights/"
    "lic-dsf-2025-08-12@e0f5a8c2359e6931bb43adfdcb16a754232b2ffd"
)
LIBRARY_COMMIT = "e0f5a8c2359e6931bb43adfdcb16a754232b2ffd"
PROVENANCE = {
    "url": "https://github.com/Teal-Insights/lic-dsf-2025-08-12",
    "vcs_info": {
        "commit_id": LIBRARY_COMMIT,
        "requested_revision": LIBRARY_COMMIT,
        "vcs": "git",
    },
}


def _wheel(*specs: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(DEST), *specs])


def _inject_provenance(wheel: Path) -> None:
    payload = json.dumps(PROVENANCE, sort_keys=True).encode()
    digest = hashlib.sha256(payload).digest()
    import base64
    token = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    replaced = wheel.with_suffix(".whl.tmp")
    with zipfile.ZipFile(wheel) as source, zipfile.ZipFile(replaced, "w", compression=zipfile.ZIP_DEFLATED) as output:
        record_name = next(name for name in source.namelist() if name.endswith(".dist-info/RECORD"))
        prefix = record_name.rsplit("/", 1)[0]
        provenance_name = prefix + "/direct_url.json"
        lines = []
        for line in source.read(record_name).decode().splitlines():
            if line.startswith(provenance_name + ","):
                continue
            lines.append(line)
        lines.append(f"{provenance_name},sha256={token},{len(payload)}")
        for info in source.infolist():
            if info.filename == provenance_name:
                continue
            data = ("\n".join(lines) + "\n").encode() if info.filename == record_name else source.read(info.filename)
            output.writestr(info, data)
        output.writestr(provenance_name, payload)
    replaced.replace(wheel)


def build() -> list[str]:
    DEST.mkdir(parents=True, exist_ok=True)
    for existing in DEST.glob("*.whl"):
        existing.unlink()
    _wheel(str(ROOT))
    _wheel(LIBRARY)
    _wheel("fastpyxl==1.1.0", "openpyxl==3.1.5", "et-xmlfile==2.0.0")
    library = next(DEST.glob("lic_dsf_2025_08_12-*.whl"))
    _inject_provenance(library)
    names = sorted(path.name for path in DEST.glob("*.whl"))
    manifest = {
        "pyodide": "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/",
        "pyodide_packages": ["micropip", "numpy", "pyyaml"],
        "wheels": [f"wheels/{name}" for name in names],
        "library_commit": LIBRARY_COMMIT,
    }
    (DEST.parent / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return names


if __name__ == "__main__":
    print("\n".join(build()))
