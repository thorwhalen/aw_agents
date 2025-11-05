"""
Example: Using the Download Agent

This example shows how to use the DownloadAgent directly in Python,
and then how to deploy it to chatbot platforms.
"""

from aw_agents.download import DownloadAgent
from aw_agents.adapters import MCPAdapter, OpenAPIAdapter


def example_direct_usage():
    """Use the agent directly in Python."""
    print("=" * 60)
    print("Example 1: Direct Usage")
    print("=" * 60)
    
    agent = DownloadAgent()
    
    # List available tools
    print("\nAvailable tools:")
    for tool in agent.get_tools():
        print(f"  - {tool['name']}: {tool['description'][:60]}...")
    
    # Execute a tool
    print("\nDownloading a file...")
    result = agent.execute_tool('download_content', {
        'url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
        'context': 'Test PDF'
    })
    
    if result['success']:
        print(f"✓ {result['message']}")
        print(f"  Path: {result['data']['path']}")
    else:
        print(f"✗ {result['message']}")


def example_mcp_deployment():
    """Deploy agent as MCP server for Claude."""
    print("\n" + "=" * 60)
    print("Example 2: MCP Deployment (Claude)")
    print("=" * 60)
    
    print("\nTo deploy to Claude Desktop:")
    print("""
1. Create the MCP server:
   
   from aw_agents.download import DownloadAgent
   from aw_agents.adapters import MCPAdapter
   
   agent = DownloadAgent()
   adapter = MCPAdapter(agent, "download-agent")
   adapter.run_sync()

2. Or use the deployment script:
   
   python scripts/deploy_mcp.py DownloadAgent --output mcp_download.py

3. Add to Claude Desktop config:
   
   {
     "mcpServers": {
       "download": {
         "command": "python",
         "args": ["/path/to/mcp_download.py"]
       }
     }
   }

4. Restart Claude Desktop
""")


def example_api_deployment():
    """Deploy agent as FastAPI server for ChatGPT."""
    print("=" * 60)
    print("Example 3: API Deployment (ChatGPT)")
    print("=" * 60)
    
    print("\nTo deploy to ChatGPT Custom GPT:")
    print("""
1. Create and start the API server:
   
   from aw_agents.download import DownloadAgent
   from aw_agents.adapters import OpenAPIAdapter
   
   agent = DownloadAgent()
   adapter = OpenAPIAdapter(agent)
   adapter.run(port=8000)

2. Or use the deployment script:
   
   python scripts/deploy_api.py DownloadAgent --output api_download.py
   python api_download.py

3. In ChatGPT Custom GPT editor:
   - Import schema from: http://localhost:8000/openapi.json
   - Or manually paste the OpenAPI spec

4. For remote access:
   - Use ngrok: ngrok http 8000
   - Or deploy to a cloud service
""")


def example_custom_agent():
    """Create a custom agent."""
    print("=" * 60)
    print("Example 4: Creating Your Own Agent")
    print("=" * 60)
    
    print("""
from aw_agents.base import AgentBase, ToolExecutionResult, create_json_schema

class MyAgent(AgentBase):
    def get_tools(self):
        return [{
            'name': 'greet',
            'description': 'Greet someone',
            'parameters': create_json_schema(
                properties={'name': {'type': 'string'}},
                required=['name']
            )
        }]
    
    def execute_tool(self, name, arguments):
        if name == 'greet':
            msg = f"Hello, {arguments['name']}!"
            return ToolExecutionResult.success_result(
                data={'greeting': msg},
                message="Greeted successfully"
            ).to_dict()

# Deploy to Claude
from aw_agents.adapters import MCPAdapter
adapter = MCPAdapter(MyAgent(), "my-agent")
adapter.run_sync()

# Deploy to ChatGPT
from aw_agents.adapters import OpenAPIAdapter
adapter = OpenAPIAdapter(MyAgent())
adapter.run(port=8001)
""")


if __name__ == '__main__':
    example_direct_usage()
    example_mcp_deployment()
    example_api_deployment()
    example_custom_agent()
