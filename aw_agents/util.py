"""Utils for aw_agents"""

import os
from functools import partial

from config2py import process_path
from aw import AW_DATA_DIR

# ============================================================================
# Persistent Storage Configuration
# ============================================================================

# Get AW_AGENTS data directory from env var, or use subdirectory of AW_DATA_DIR
# Users can override by setting AW_AGENTS_DATA_DIR environment variable
# Default: <AW_DATA_DIR>/agents
# Example: ~/.local/share/aw/agents
_aw_agents_data_dir_raw = os.environ.get('AW_AGENTS_DATA_DIR') or os.path.join(
    AW_DATA_DIR, 'agents'
)

# Process path and ensure it exists
AW_AGENTS_DATA_DIR = process_path(_aw_agents_data_dir_raw, ensure_dir_exists=True)

# Convenience function to join paths relative to AW_AGENTS_DATA_DIR
# Example: djoin('downloads', 'file.pdf') -> '/Users/user/.local/share/aw/agents/downloads/file.pdf'
djoin = partial(os.path.join, AW_AGENTS_DATA_DIR)
djoin.rootdir = AW_AGENTS_DATA_DIR
