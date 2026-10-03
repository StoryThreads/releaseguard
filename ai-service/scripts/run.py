#!/usr/bin/env python3
import sys
from pathlib import Path

# Add ai-service root to sys.path
SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.cli.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
