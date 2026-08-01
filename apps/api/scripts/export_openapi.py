"""Write a deterministic OpenAPI artifact for frontend type generation."""

import json
from pathlib import Path

from ask_lucas.main import app


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "openapi.json"
    destination.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
