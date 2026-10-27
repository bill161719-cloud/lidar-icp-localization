"""Check the recorded UCRT64 compiler/runtime and dependency package versions."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("msys_root", type=Path)
    args = parser.parse_args()
    lock = json.loads(Path(__file__).with_name("dependencies-msys2.lock.json").read_text())
    installed = {}
    for path in (args.msys_root / "var/lib/pacman/local").glob("*/desc"):
        lines = path.read_text(encoding="utf-8").splitlines()
        if "%NAME%" in lines and "%VERSION%" in lines:
            installed[lines[lines.index("%NAME%") + 1]] = lines[lines.index("%VERSION%") + 1]
    errors = []
    for item in lock["packages"]:
        actual = installed.get(item["name"], "NOT INSTALLED")
        if actual != item["version"]:
            errors.append(f'{item["name"]}: expected {item["version"]}, found {actual}')
    if errors:
        raise SystemExit("UCRT64 package baseline mismatch:\n" + "\n".join(errors))
    print(f'UCRT64 package baseline OK: {len(lock["packages"])} locked versions.')


if __name__ == "__main__":
    main()
