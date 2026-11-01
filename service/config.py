"""Private runtime configuration. Importing this module makes no requests."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def settings():
    values = {}
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    values.update(os.environ)
    return values
