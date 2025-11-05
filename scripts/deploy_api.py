#!/usr/bin/env python
"""
Generate FastAPI server script for any agent.

Usage:
    python scripts/deploy_api.py DownloadAgent --output api_download.py
"""

import argparse
from pathlib import Path
import importlib


def main():
    parser = argparse.ArgumentParser(
        description='Generate API server script for an agent'
    )
    parser.add_argument('agent_name', help='Agent class name (e.g., DownloadAgent)')
    parser.add_argument('--output', '-o', required=True, help='Output script path')
    parser.add_argument(
        '--port', type=int, default=8000, help='Default port (default: 8000)'
    )

    args = parser.parse_args()

    # Import the agent class
    try:
        # Try different import patterns
        if args.agent_name == 'DownloadAgent':
            from aw_agents.download import DownloadAgent as agent_class
        else:
            # Try to import from aw_agents
            module_name = args.agent_name.lower().replace('agent', '')
            module = importlib.import_module(f'aw_agents.{module_name}')
            agent_class = getattr(module, args.agent_name)
    except (ImportError, AttributeError) as e:
        print(f"Error: Could not import {args.agent_name}")
        print(f"  {e}")
        return 1

    # Generate the script
    output_path = Path(args.output)

    from aw_agents.adapters import create_api_server_script

    created_path = create_api_server_script(
        agent_class, output_path, default_port=args.port
    )

    print(f"✓ Created API server script: {created_path}")
    print(f"\nTo run:")
    print(f"  python {created_path}")
    print(f"\nTo use with ChatGPT Custom GPT:")
    print(f"  1. Start the server")
    print(f"  2. Import schema from: http://localhost:{args.port}/openapi.json")


if __name__ == '__main__':
    exit(main() or 0)
