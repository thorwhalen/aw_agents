"""
OpenAPI/FastAPI adapter for AW agents.

This adapter wraps any AgentBase subclass to expose it as a REST API
with OpenAPI spec for use with ChatGPT Custom GPTs.
"""

from typing import Any, Dict, Optional
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field, create_model
    import uvicorn

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print(
        "Warning: fastapi not installed. Install with: pip install fastapi uvicorn pydantic"
    )

from aw_agents.base import AgentBase


class OpenAPIAdapter:
    """
    Adapter to expose an AgentBase as a FastAPI/OpenAPI service.

    Usage:
        agent = YourAgent()
        adapter = OpenAPIAdapter(agent, title="Your Agent API")
        adapter.run(port=8000)
    """

    def __init__(
        self,
        agent: AgentBase,
        *,
        title: str = "AI Agent API",
        description: str = "AI Agent exposed via OpenAPI",
        version: str = "1.0.0",
    ):
        """
        Initialize OpenAPI adapter.

        Args:
            agent: Agent instance to wrap
            title: API title
            description: API description
            version: API version
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "fastapi required. Install with: pip install fastapi uvicorn pydantic"
            )

        self.agent = agent

        # Get metadata from agent
        metadata = agent.get_metadata()

        self.app = FastAPI(
            title=title or metadata.get('name', 'AI Agent API'),
            description=description
            or metadata.get('description', 'AI Agent exposed via OpenAPI'),
            version=version or metadata.get('version', '1.0.0'),
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Restrict in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        """Set up FastAPI routes from agent tools."""

        # Root endpoint
        @self.app.get("/")
        async def root():
            """Root endpoint with API information."""
            metadata = self.agent.get_metadata()
            return {
                "name": metadata.get('name'),
                "version": metadata.get('version'),
                "description": metadata.get('description'),
                "docs": "/docs",
                "openapi": "/openapi.json",
            }

        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy"}

        # Create endpoints for each tool
        for tool in self.agent.get_tools():
            self._create_tool_endpoint(tool)

    def _create_tool_endpoint(self, tool: Dict[str, Any]):
        """Create a FastAPI endpoint for a tool."""
        name = tool['name']
        description = tool['description']
        parameters = tool['parameters']

        # Create Pydantic model for request
        request_model = self._create_pydantic_model(f"{name}_request", parameters)

        # Create Pydantic model for response
        response_model = create_model(
            f"{name}_response",
            success=(bool, Field(..., description="Whether operation succeeded")),
            data=(Optional[Any], Field(None, description="Result data")),
            message=(Optional[str], Field(None, description="Message")),
            warnings=(Optional[list[str]], Field(None, description="Warnings")),
            metadata=(Optional[Dict[str, Any]], Field(None, description="Metadata")),
        )

        # Create endpoint
        @self.app.post(
            f"/{name.replace('_', '-')}",
            response_model=response_model,
            description=description,
        )
        async def tool_endpoint(request: request_model):  # type: ignore
            try:
                result = self.agent.execute_tool(name, request.dict())
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Store endpoint reference (needed for FastAPI)
        setattr(self, f"_endpoint_{name}", tool_endpoint)

    def _create_pydantic_model(
        self, model_name: str, json_schema: Dict[str, Any]
    ) -> type[BaseModel]:
        """Create a Pydantic model from JSON schema."""
        properties = json_schema.get('properties', {})
        required = set(json_schema.get('required', []))

        fields = {}
        for prop_name, prop_schema in properties.items():
            prop_type = self._json_type_to_python(prop_schema.get('type', 'string'))
            prop_desc = prop_schema.get('description', '')

            if prop_name in required:
                fields[prop_name] = (prop_type, Field(..., description=prop_desc))
            else:
                fields[prop_name] = (
                    Optional[prop_type],
                    Field(None, description=prop_desc),
                )

        return create_model(model_name, **fields)  # type: ignore

    def _json_type_to_python(self, json_type: str) -> type:
        """Convert JSON schema type to Python type."""
        type_map = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        return type_map.get(json_type, str)

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """
        Run the FastAPI server.

        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional uvicorn arguments
        """
        uvicorn.run(self.app, host=host, port=port, **kwargs)


def create_api_server_script(
    agent_class, output_path: Path, *, default_port: int = 8000
):
    """
    Generate an API server script for an agent.

    Args:
        agent_class: Agent class to wrap
        output_path: Path to write the script
        default_port: Default port for the server
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
FastAPI Server for {agent_class.__name__}

Auto-generated API server script.

To run:
    python {output_path.name} [--port PORT]

To use with ChatGPT Custom GPT:
1. Start this server
2. Go to https://chat.openai.com/gpts/editor
3. Create a Custom GPT
4. Add action using schema from: http://localhost:{default_port}/openapi.json
"""

import argparse
from aw_agents.adapters.openapi import OpenAPIAdapter
from {import_module} import {agent_class.__name__}


def main():
    parser = argparse.ArgumentParser(description='Run {agent_class.__name__} API server')
    parser.add_argument('--port', type=int, default={default_port}, help='Port to run on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    args = parser.parse_args()
    
    agent = {agent_class.__name__}()
    adapter = OpenAPIAdapter(agent)
    
    print(f"Starting {agent_class.__name__} API server...")
    print(f"  OpenAPI spec: http://localhost:{{args.port}}/openapi.json")
    print(f"  Docs: http://localhost:{{args.port}}/docs")
    
    adapter.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
'''

    output_path.write_text(script_content)
    output_path.chmod(0o755)

    return output_path
