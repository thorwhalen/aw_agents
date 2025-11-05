#!/usr/bin/env python
"""
Generate MCP server script for any agent.

Usage:
    python scripts/deploy_mcp.py DownloadAgent --output mcp_download.py
"""

import argparse
from pathlib import Path
import importlib


def main():
    parser = argparse.ArgumentParser(
        description='Generate MCP server script for an agent'
    )
    parser.add_argument('agent_name', help='Agent class name (e.g., DownloadAgent)')
    parser.add_argument('--output', '-o', required=True, help='Output script path')
    parser.add_argument(
        '--server-name', help='MCP server name (default: agent name in lowercase)'
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

    # Determine server name
    server_name = (
        args.server_name or args.agent_name.lower().replace('agent', '').strip()
    )
    if not server_name:
        server_name = args.agent_name.lower()

    # Generate the script
    output_path = Path(args.output)

    from aw_agents.adapters import create_mcp_server_script

    created_path = create_mcp_server_script(agent_class, server_name, output_path)

    print(f"✓ Created MCP server script: {created_path}")
    print(f"\nTo use with Claude Desktop, add to your config:")
    print(
        f'''
{{
  "mcpServers": {{
    "{server_name}": {{
      "command": "python",
      "args": ["{created_path.absolute()}"]
    }}
  }}
}}
'''
    )


if __name__ == '__main__':
    exit(main() or 0)
