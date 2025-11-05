"""
MCP (Model Context Protocol) adapter for AW agents.

This adapter wraps any AgentBase subclass to expose it as an MCP server
for use with Claude Desktop.
"""

import asyncio
from typing import Any, Dict
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: mcp package not installed. Install with: pip install mcp")

from aw_agents.base import AgentBase


class MCPAdapter:
    """
    Adapter to expose an AgentBase as an MCP server.

    Usage:
        agent = YourAgent()
        adapter = MCPAdapter(agent, server_name="your-agent")
        adapter.run()
    """

    def __init__(self, agent: AgentBase, server_name: str):
        """
        Initialize MCP adapter.

        Args:
            agent: Agent instance to wrap
            server_name: Name for the MCP server
        """
        if not MCP_AVAILABLE:
            raise ImportError("mcp package required. Install with: pip install mcp")

        self.agent = agent
        self.server = Server(server_name)
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools from the agent."""
            agent_tools = self.agent.get_tools()

            mcp_tools = []
            for tool in agent_tools:
                mcp_tools.append(
                    Tool(
                        name=tool['name'],
                        description=tool['description'],
                        inputSchema=tool['parameters'],
                    )
                )

            return mcp_tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls from Claude."""
            try:
                result = self.agent.execute_tool(name, arguments)

                # Format response based on result
                if result['success']:
                    response_text = self._format_success_response(result)
                else:
                    response_text = self._format_error_response(result)

                return [TextContent(type="text", text=response_text)]

            except Exception as e:
                return [
                    TextContent(
                        type="text", text=f"❌ Error executing {name}:\n{str(e)}"
                    )
                ]

    def _format_success_response(self, result: Dict[str, Any]) -> str:
        """Format a successful tool execution response."""
        parts = []

        if result.get('message'):
            parts.append(f"✓ {result['message']}")
        else:
            parts.append("✓ Operation completed successfully")

        # Add data if present
        if result.get('data'):
            parts.append("")
            parts.append(str(result['data']))

        # Add warnings if present
        if result.get('warnings'):
            parts.append("")
            parts.append("Warnings:")
            for warning in result['warnings']:
                parts.append(f"  • {warning}")

        return "\n".join(parts)

    def _format_error_response(self, result: Dict[str, Any]) -> str:
        """Format an error response."""
        message = result.get('message', 'Unknown error')
        return f"❌ Error: {message}"

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )

    def run_sync(self):
        """Run the MCP server (synchronous wrapper)."""
        asyncio.run(self.run())


def create_mcp_server_script(agent_class, server_name: str, output_path: Path):
    """
    Generate an MCP server script for an agent.

    Args:
        agent_class: Agent class to wrap
        server_name: Name for the MCP server
        output_path: Path to write the script
    """
    # Determine module path for import
    agent_module = agent_class.__module__
    if agent_module.startswith('aw_agents.'):
        # Extract the submodule (e.g., 'download' from 'aw_agents.download.agent')
        parts = agent_module.split('.')
        if len(parts) > 2:
            import_module = '.'.join(parts[:2])  # aw_agents.download
        else:
            import_module = agent_module
    else:
        import_module = agent_module

    script_content = f'''"""
MCP Server for {agent_class.__name__}

Auto-generated MCP server script.

To use with Claude Desktop, add to your config:
{{
  "mcpServers": {{
    "{server_name}": {{
      "command": "python",
      "args": ["{output_path.absolute()}"]
    }}
  }}
}}
"""

from aw_agents.adapters.mcp import MCPAdapter
from {import_module} import {agent_class.__name__}


def main():
    agent = {agent_class.__name__}()
    adapter = MCPAdapter(agent, "{server_name}")
    adapter.run_sync()


if __name__ == "__main__":
    main()
'''

    output_path.write_text(script_content)
    output_path.chmod(0o755)

    return output_path
