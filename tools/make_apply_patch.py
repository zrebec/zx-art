#!/usr/bin/env python3
"""Create an apply_patch replacement patch without writing the target file."""

from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: make_apply_patch.py TARGET RELATIVE_PATH NEW_FILE")
    target = Path(sys.argv[1])
    relative = sys.argv[2]
    new_file = Path(sys.argv[3])
    old = target.read_text(encoding="utf-8")
    new = new_file.read_text(encoding="utf-8")
    lines = ["*** Begin Patch", f"*** Update File: {relative}", "@@"]
    lines.extend(f"-{line}" for line in old.splitlines())
    lines.extend(f"+{line}" for line in new.splitlines())
    lines.append("*** End Patch")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
