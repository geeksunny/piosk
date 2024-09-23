# Import config values
# TODO: Generate default config values if it doesn't exist?
# TODO: Combine with argparse?
import sys
from pathlib import Path

import tomli

try:
    with (Path(__file__).parent.parent / 'config.toml').open('rb') as f:
        CONFIG = tomli.load(f)
except tomli.TOMLDecodeError as e:
    sys.exit(f'Error importing config file: {e}')

