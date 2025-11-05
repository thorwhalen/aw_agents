"""
aw_agents - AI Agents for Agentic Workflows

A collection of AI agents that can be easily deployed to multiple chatbot
platforms (Claude, ChatGPT, etc.) through adapters.

Agents:
    - DownloadAgent: Smart content downloader with context-aware naming

Adapters:
    - MCPAdapter: For Claude Desktop (MCP protocol)
    - OpenAPIAdapter: For ChatGPT Custom GPTs (OpenAPI/FastAPI)

Example:
    >>> from aw_agents.download import DownloadAgent
    >>> from aw_agents.adapters import MCPAdapter
    >>> 
    >>> agent = DownloadAgent()
    >>> adapter = MCPAdapter(agent, "download-agent")
    >>> adapter.run()  # Serves agent via MCP for Claude
"""

__version__ = "0.1.0"

# Core abstractions
from aw_agents.base import AgentBase, ToolExecutionResult, create_json_schema

# Adapters
from aw_agents.adapters import (
    MCPAdapter,
    OpenAPIAdapter,
    create_mcp_server_script,
    create_api_server_script,
)

# Agents
from aw_agents.download import DownloadAgent

__all__ = [
    # Version
    '__version__',
    # Base
    'AgentBase',
    'ToolExecutionResult',
    'create_json_schema',
    # Adapters
    'MCPAdapter',
    'OpenAPIAdapter',
    'create_mcp_server_script',
    'create_api_server_script',
    # Agents
    'DownloadAgent',
]
