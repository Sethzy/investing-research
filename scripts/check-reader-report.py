"""Check the required reader sections without claiming semantic completeness."""

import argparse
from pathlib import Path
from investing_research.coverage import reader_gaps


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    missing = reader_gaps(args.report.read_text())
    if missing:
        parser.exit(1, "Missing reader sections: " + ", ".join(missing) + "\n")
    print("Reader structure passed. Source interpretation and financial review remain required.")
