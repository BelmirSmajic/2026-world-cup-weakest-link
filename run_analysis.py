"""Rebuild the final analysis outputs from repository-root data files."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from worldcup_weakest_link.pipeline import main


if __name__ == "__main__":
    main()
