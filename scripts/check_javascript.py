"""Run every checked-in JavaScript suite, without platform-specific shell globs."""
from pathlib import Path
import shutil
import subprocess


def main():
    node = shutil.which("node")
    if node is None:
        raise SystemExit("Node.js is required for the JavaScript checks.")
    root = Path(__file__).resolve().parents[1]
    suites = sorted((root / "tests").glob("*.js"))
    if not suites:
        raise SystemExit("No JavaScript suites found; this is not a passing check.")
    for suite in suites:
        subprocess.run([node, str(suite)], cwd=root, check=True, timeout=120)
    print(f"Passed {len(suites)} JavaScript suites.")


if __name__ == "__main__":
    main()
