#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "blueprints" / "moonshine-stt"
    compose = (root / "docker-compose.yml").read_text()
    config = (root / "template.toml").read_text()
    payload = {"compose": compose, "config": config}
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
