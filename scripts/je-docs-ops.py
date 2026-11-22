"""Entry point; provider selection and permissions belong to the host."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jedocsops.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
