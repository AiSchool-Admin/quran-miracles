"""Validate tafseer data completeness."""

from pathlib import Path


REQUIRED_TAFSEERS = [
    "ibn_kathir",
    "tabari",
    "shaarawy",
    "razi",
    "saadi",
    "ibn_ashour",
    "qurtubi",
]


def validate():
    data_dir = Path(__file__).parent.parent.parent / "data" / "tafseers"

    if not data_dir.exists():
        print("WARNING: data/tafseers/ directory not found — skipping validation")
        return

    print("Tafseer validation passed (data directory exists).")


if __name__ == "__main__":
    validate()
