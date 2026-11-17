"""Download Pyodide package wheels next to the local Pyodide, so the build can import them.

    python build/fetch_wheels.py numpy pandas

Node's own fetch does not go through the corporate proxy here, but curl does, and
Pyodide looks in its own folder before trying the CDN.
"""
import json
import subprocess
import sys
from pathlib import Path

PYO = Path(__file__).resolve().parent / "node_modules" / "pyodide"
lock = json.loads((PYO / "pyodide-lock.json").read_text(encoding="utf-8"))
version = json.loads((PYO / "package.json").read_text(encoding="utf-8"))["version"]
cdn = f"https://cdn.jsdelivr.net/pyodide/v{version}/full/"
pkgs = lock["packages"]


def deps(name, seen):
    if name in seen:
        return
    seen.add(name)
    for d in pkgs[name].get("depends", []):
        deps(d, seen)


want = set()
for n in sys.argv[1:]:
    deps(n.lower(), want)
for n in sorted(want):
    f = pkgs[n]["file_name"]
    if (PYO / f).exists():
        print("have", f)
        continue
    subprocess.run(["curl", "-s", "-f", "-o", str(PYO / f), cdn + f], check=True)
    print("got ", f)
