# Quick Usage Guide

## Running Agents as Servers

Each agent in `aw_agents` can be run directly as a server with built-in setup instructions.

### Download Agent

The Download Agent provides smart content downloading with context-aware naming.

#### For Claude Desktop (MCP Protocol)

```bash
# Run the agent - it automatically configures Claude Desktop!
python -m aw_agents.agents.download.agent --mcp

# Or run directly
python aw_agents/agents/download/agent.py --mcp
```

**What happens:**
1. **The agent automatically adds itself to your Claude Desktop config**
2. Starts the MCP server
3. Tells you to restart Claude Desktop
4. Waits for Claude to connect

**That's it!** Just restart Claude Desktop and you're ready to go.

**To manage servers later:**
```python
from aw.util import claude_desktop_config

mcp = claude_desktop_config()
list(mcp)  # See all configured servers
del mcp['download']  # Remove a server
```

#### For ChatGPT (FastAPI Server)

```bash
# Run the agent on default port 8000
python -m aw_agents.agents.download.agent --api

# Or specify a custom port
python -m aw_agents.agents.download.agent --api --port 8080

# Or run directly
python aw_agents/agents/download/agent.py --api --port 8080
```

**What happens:**
1. The agent starts a FastAPI server
2. It prints the server URL and OpenAPI schema URL
3. Shows you how to configure ChatGPT Custom GPT
4. Provides ngrok instructions for remote access
5. Starts the server and waits for requests

**Use the OpenAPI schema URL** in ChatGPT's Custom GPT action configuration.

#### Using with ngrok for Remote Access

If you need to expose your local server for ChatGPT to access:

1. Start ngrok in another terminal:
   ```bash
   ngrok http 8000
   ```

2. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

3. Run the agent with the ngrok URL:
   ```bash
   python -m aw_agents.agents.download.agent --api --server-url https://abc123.ngrok.io
   ```

The OpenAPI schema will now include your ngrok URL, making ChatGPT setup seamless.

### Command-Line Options

```bash
# Show help
python -m aw_agents.agents.download.agent --help

# MCP server (default)
python -m aw_agents.agents.download.agent
python -m aw_agents.agents.download.agent --mcp

# API server
python -m aw_agents.agents.download.agent --api
python -m aw_agents.agents.download.agent --api --port 8080

# API server with custom server URL (for ngrok or production deployment)
python -m aw_agents.agents.download.agent --api --server-url https://your-url.com
```

## Why This Approach?

✅ **No manual script creation** - agent is already runnable
✅ **Customized instructions** - tailored to the specific agent
✅ **Copy-paste configs** - ready to use, no editing needed
✅ **Absolute paths** - automatically includes correct paths
✅ **Less error-prone** - no typos in manual setup

## Using Agents Programmatically

You can still use agents in your Python code:

```python
from aw_agents.agents.download import DownloadAgent

# Create agent instance
agent = DownloadAgent()

# Get available tools
tools = agent.get_tools()
print([t['name'] for t in tools])

# Execute a tool
result = agent.execute_tool('download_content', {
    'url': 'https://example.com/file.pdf',
    'context': 'Important Document'
})

if result['success']:
    print(f"Downloaded to: {result['data']['path']}")
```

## Advanced: Manual Deployment

If you need more control, you can still create custom server scripts:

```python
# For Claude Desktop (MCP)
from aw_agents.agents.download import DownloadAgent
from aw_agents.adapters import MCPAdapter

agent = DownloadAgent()
adapter = MCPAdapter(agent, "my-custom-name")
adapter.run_sync()
```

```python
# For ChatGPT (FastAPI)
from aw_agents.agents.download import DownloadAgent
from aw_agents.adapters import OpenAPIAdapter

agent = DownloadAgent()
adapter = OpenAPIAdapter(agent, title="My Custom API")
adapter.run(host="0.0.0.0", port=8000)
```

Or use the deployment scripts:

```bash
# Generate MCP server script
python scripts/deploy_mcp.py DownloadAgent --output my_server.py

# Generate API server script
python scripts/deploy_api.py DownloadAgent --output my_api.py
```

## Creating Your Own Agent

To make your own agent runnable as a server:

1. Create your agent class extending `AgentBase`
2. Add a `main()` function similar to the Download Agent
3. Add `if __name__ == '__main__': main()`

See `aw_agents/agents/download/agent.py` for a complete example.
