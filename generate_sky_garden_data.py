#!/usr/bin/env python3
import json
from pathlib import Path

FLOWERS = [
    {"name": "Rose", "color": "Red", "sunlight": "Full sun"},
    {"name": "Lavender", "color": "Purple", "sunlight": "Full sun"},
    {"name": "Jasmine", "color": "White", "sunlight": "Partial shade"},
    {"name": "Sunflower", "color": "Yellow", "sunlight": "Full sun"},
]


def generate(output_file: str = "sky-garden-data.js") -> Path:
    output_path = Path(output_file)
    payload = (
        "window.SKY_GARDEN_FLOWERS = "
        + json.dumps(FLOWERS, ensure_ascii=False, indent=2)
        + ";\n"
    )
    output_path.write_text(payload, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    file_path = generate()
    print(f"Generated {file_path}")
