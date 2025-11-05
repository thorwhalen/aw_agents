"""Adapters for exposing agents to different platforms."""

from aw_agents.adapters.mcp import MCPAdapter, create_mcp_server_script
from aw_agents.adapters.openapi import OpenAPIAdapter, create_api_server_script

__all__ = [
    'MCPAdapter',
    'OpenAPIAdapter',
    'create_mcp_server_script',
    'create_api_server_script',
]
