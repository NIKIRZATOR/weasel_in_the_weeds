from __future__ import annotations

import argparse
from pathlib import Path

from game.world.tmx_loader import load_tmx_preview, preview_to_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Tiled TMX file")
    parser.add_argument("tmx_path", nargs="?", help="Path to .tmx file")
    args = parser.parse_args()

    if args.tmx_path:
        tmx_path = Path(args.tmx_path)
    else:
        matches = sorted(Path(".").glob("*.tmx"))
        if not matches:
            raise SystemExit("No .tmx files found in the current directory.")
        tmx_path = matches[0]

    preview = load_tmx_preview(tmx_path)
    print(preview_to_json(preview))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
