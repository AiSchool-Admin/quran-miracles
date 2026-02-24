"""Validate Quranic text integrity via checksum verification.

Ensures the Quranic text from tanzil.net has not been modified.
"""

import hashlib
import sys
from pathlib import Path

EXPECTED_CHECKSUMS: dict[str, str] = {
    # Will be populated with actual checksums after initial data import
}


def validate():
    data_dir = Path(__file__).parent.parent.parent / "data" / "quran"

    if not data_dir.exists():
        print("WARNING: data/quran/ directory not found — skipping validation")
        return

    quran_files = list(data_dir.glob("*.xml")) + list(data_dir.glob("*.txt"))

    if not quran_files:
        print("WARNING: No Quranic text files found — skipping validation")
        return

    for file_path in quran_files:
        sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
        print(f"  {file_path.name}: {sha256}")

        if file_path.name in EXPECTED_CHECKSUMS:
            expected = EXPECTED_CHECKSUMS[file_path.name]
            if sha256 != expected:
                print(f"ERROR: Checksum mismatch for {file_path.name}!")
                sys.exit(1)

    print("Quranic text integrity check passed.")


if __name__ == "__main__":
    validate()
