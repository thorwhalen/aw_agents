# aw-agents

**AI Agents for Agentic Workflows** - Easily deploy AI agents to multiple chatbot platforms (Claude, ChatGPT, and more).

## Overview

`aw-agents` provides a unified framework for building AI agents and deploying them to different chatbot platforms with minimal boilerplate. Write your agent once, deploy everywhere.

### Key Features

- 🎯 **Write Once, Deploy Everywhere**: Single agent implementation works with Claude, ChatGPT, and future platforms
- 🔌 **Pluggable Adapters**: MCP for Claude, OpenAPI for ChatGPT
- 📦 **Batteries Included**: Built-in download agent with smart features
- 🛠️ **Easy to Extend**: Simple base class for creating new agents
- 🎨 **Clean Architecture**: Separation of agent logic and platform adapters

## Installation

```bash
# From source (recommended for development)
git clone https://github.com/thorwhalen/aw_agents.git
cd aw_agents
pip install -e .

# With Claude Desktop support (MCP)
pip install -e .[mcp]

# With ChatGPT Custom GPT support (FastAPI)
pip install -e .[api]

# With all features
pip install -e .[all]

# For development
pip install -e .[dev]
```

### Verify Installation

```bash
# Test the installation
python -c "from aw_agents.download import DownloadAgent; agent = DownloadAgent(); print('✓ Installation successful!')"
```

## Quick Start

### Using the Download Agent

The package includes a smart download agent out of the box:

```python
from aw_agents.download import DownloadAgent

agent = DownloadAgent()

# Get available tools
tools = agent.get_tools()
print([t['name'] for t in tools])
# ['download_content', 'download_multiple', 'list_downloads']

# Execute a tool
result = agent.execute_tool('download_content', {
    'url': 'https://arxiv.org/pdf/2103.00020.pdf',
    'context': 'Important ML Paper'
})

print(result['data']['path'])  # ~/Downloads/Important_ML_Paper.pdf
```

### Deploy to Claude Desktop (MCP)

**Step 1: Create MCP Server Script**

```python
from aw_agents.download import DownloadAgent
from aw_agents.adapters import MCPAdapter

agent = DownloadAgent()
adapter = MCPAdapter(agent, "download-agent")

# This starts an MCP server for Claude Desktop
if __name__ == "__main__":
    adapter.run_sync()
```

Save this as `mcp_download.py` or use the deployment script:

```bash
python scripts/deploy_mcp.py DownloadAgent --output mcp_download.py
```

**Step 2: Configure Claude Desktop**

Edit your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this configuration:
```json
{
  "mcpServers": {
    "download": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_download.py"]
    }
  }
}
```

**Important**: Use the absolute path to your script, not `~/` or relative paths.

**Step 3: Restart Claude Desktop**

Completely quit and restart Claude Desktop.

**Step 4: Test It**

Ask Claude:
```
Download this paper for me: https://arxiv.org/pdf/2103.00020.pdf
Context: "Attention is All You Need"
```

**Troubleshooting**:
- Check logs: `~/Library/Logs/Claude/` (macOS)
- Verify Python path in config
- Ensure dependencies are installed in the correct Python environment

### Deploy to ChatGPT Custom GPT (FastAPI)

**Step 1: Create and Start API Server**

```python
from aw_agents.download import DownloadAgent
from aw_agents.adapters import OpenAPIAdapter

agent = DownloadAgent()
adapter = OpenAPIAdapter(agent, title="Download Agent API")

# This starts a FastAPI server
if __name__ == "__main__":
    adapter.run(port=8000)
```

Save this as `api_download.py` or use the deployment script:

```bash
python scripts/deploy_api.py DownloadAgent --output api_download.py
python api_download.py  # Start the server
```

The server will be available at http://localhost:8000

**Step 2: Create Custom GPT**

1. Go to https://chat.openai.com/gpts/editor
2. Click "Create a GPT"
3. Name it (e.g., "Download Assistant")
4. Add instructions:
   ```
   You help users download files from URLs. Use the download_content 
   action when users provide URLs. Always ask for context to generate 
   good filenames. You can download multiple files at once and list 
   previously downloaded files.
   ```

**Step 3: Add Actions**

1. In the GPT editor, go to "Configure" → "Actions"
2. Click "Create new action"
3. Import schema from: `http://localhost:8000/openapi.json`
4. Click "Add Action"

**Step 4: Test Your GPT**

Ask your Custom GPT:
```
Download this dataset: https://github.com/user/repo/blob/main/data.csv
Context: "Sales Data Q4"
```

**Important Notes**:
- **Local Testing**: ChatGPT servers can't access `localhost` from OpenAI's infrastructure
- **For Remote Access**: 
  - Use ngrok: `ngrok http 8000` (provides a public URL)
  - Deploy to cloud service (AWS, GCP, Azure, Heroku)
  - Use local network IP if on the same network

**Production Deployment**:
1. Deploy to cloud service with HTTPS
2. Add authentication (API keys, OAuth)
3. Update Custom GPT actions with public URL

## Architecture

```
aw_agents/
├── base.py              # AgentBase, ToolExecutionResult
├── adapters/
│   ├── mcp.py          # MCPAdapter for Claude
│   └── openapi.py      # OpenAPIAdapter for ChatGPT
└── download/           # Download agent implementation
    ├── agent.py        # DownloadAgent (AgentBase subclass)
    └── download_core.py # Core download logic
```

### Creating Your Own Agent

```python
from aw_agents.base import AgentBase, ToolExecutionResult, create_json_schema

class MyAgent(AgentBase):
    """My custom agent."""
    
    def get_tools(self):
        return [
            {
                'name': 'my_tool',
                'description': 'Does something useful',
                'parameters': create_json_schema(
                    properties={
                        'input': {
                            'type': 'string',
                            'description': 'Input text'
                        }
                    },
                    required=['input']
                )
            }
        ]
    
    def execute_tool(self, name, arguments):
        if name == 'my_tool':
            # Your logic here
            result = self._process(arguments['input'])
            
            return ToolExecutionResult.success_result(
                data={'output': result},
                message="Processed successfully"
            ).to_dict()
        
        return ToolExecutionResult.error_result(
            message=f"Unknown tool: {name}"
        ).to_dict()
    
    def _process(self, input_text):
        # Your implementation
        return input_text.upper()
```

Then deploy it:

```python
# For Claude
from aw_agents.adapters import MCPAdapter
adapter = MCPAdapter(MyAgent(), "my-agent")
adapter.run_sync()

# For ChatGPT
from aw_agents.adapters import OpenAPIAdapter
adapter = OpenAPIAdapter(MyAgent())
adapter.run(port=8001)
```

## Included Agents

### Download Agent

Smart content downloader with:
- **Landing page detection**: Automatically finds actual download links
- **Context-aware file naming**: Uses conversation context for meaningful filenames
- **Special handling for**:
  - GitHub (converts blob URLs to raw)
  - HuggingFace (handles dataset downloads)
  - Kaggle datasets
  - Academic papers (arXiv, etc.)
- **Support for**: PDFs, datasets, CSV, JSON, and more

**Tools:**
- `download_content` - Download a single URL with smart handling
- `download_multiple` - Download multiple URLs at once
- `list_downloads` - List downloaded files

**Examples:**

```python
from aw_agents.download import DownloadAgent

agent = DownloadAgent()

# Download with context-aware naming
result = agent.execute_tool('download_content', {
    'url': 'https://github.com/user/repo/blob/main/data.csv',
    'context': 'Dataset for analysis'
})
# Automatically converts to raw.githubusercontent.com
# Saves as: Dataset_for_analysis.csv

# Download multiple files
result = agent.execute_tool('download_multiple', {
    'urls': [
        'https://arxiv.org/pdf/2103.00020.pdf',
        'https://arxiv.org/pdf/1706.03762.pdf'
    ],
    'contexts': [
        'Attention Paper',
        'Transformer Original'
    ]
})

# List downloaded PDFs
result = agent.execute_tool('list_downloads', {
    'pattern': '*.pdf'
})
```

**Smart Features:**

1. **Landing Page Detection**:
   ```python
   # Input: Landing page URL
   agent.execute_tool('download_content', {
       'url': 'https://papers.nips.cc/paper/2017/hash/xxx-Abstract.html'
   })
   # Agent detects HTML, finds PDF link, downloads PDF, warns about redirect
   ```

2. **GitHub URL Handling**:
   ```python
   # Input: GitHub blob URL
   'https://github.com/user/repo/blob/main/data.csv'
   # Converts to: 
   'https://raw.githubusercontent.com/user/repo/main/data.csv'
   ```

3. **Context-Aware Naming**:
   ```python
   # Without context:
   # Filename: 2103.00020.pdf
   
   # With context:
   agent.execute_tool('download_content', {
       'url': 'https://arxiv.org/pdf/2103.00020.pdf',
       'context': 'Attention is All You Need - Transformer Paper'
   })
   # Filename: Attention_is_All_You_Need_Transformer_Paper.pdf
   ```

## Integration Guides

### Claude Desktop Integration

1. Create MCP server script:
   ```bash
   python scripts/deploy_mcp.py DownloadAgent --output ~/mcp_download.py
   ```

2. Edit Claude Desktop config:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. Add to config:
   ```json
   {
     "mcpServers": {
       "download": {
         "command": "python",
         "args": ["/absolute/path/to/mcp_download.py"]
       }
     }
   }
   ```

4. Restart Claude Desktop

**Usage Examples in Claude:**

```
Download this paper: https://arxiv.org/pdf/2103.00020.pdf
Context: "Attention is All You Need paper"

I need these papers:
1. https://arxiv.org/pdf/2103.00020.pdf - "Attention Paper"
2. https://arxiv.org/pdf/1706.03762.pdf - "Transformer Original"

Show me what PDFs I've downloaded
```

### ChatGPT Custom GPT Integration

1. Create API server script:
   ```bash
   python scripts/deploy_api.py DownloadAgent --output ~/api_download.py
   python ~/api_download.py
   ```

2. Create Custom GPT at https://chat.openai.com/gpts/editor

3. Add actions using schema from: `http://localhost:8000/openapi.json`

4. For remote access, deploy to cloud or use ngrok:
   ```bash
   ngrok http 8000
   ```

**Usage Examples in ChatGPT:**

```
Download this dataset: https://github.com/user/repo/blob/main/data.csv
Context: "Sales Data Q4 2024"

Can you download these research papers for me?
[List of URLs with contexts]
```

## Troubleshooting

### Installation Issues

**Problem**: Module not found errors

**Solution**:
```bash
# Update pip and reinstall
pip install --upgrade pip
pip uninstall aw-agents
pip install -e .[all]
```

**Problem**: Missing dependencies

**Solution**:
```bash
# Install specific feature sets
pip install -e .[mcp]    # For Claude
pip install -e .[api]    # For ChatGPT
pip install -e .[all]    # Everything
```

### Claude Desktop Issues

**Problem**: Claude doesn't see the download tools

**Solution**:
1. Verify config file location (see paths above)
2. Use absolute path in config (not `~/` or `./`)
3. Check logs: `~/Library/Logs/Claude/` (macOS)
4. Restart Claude Desktop completely (Quit, not just close window)
5. Verify Python environment: `which python`

**Problem**: "Module not found" when Claude tries to use agent

**Solution**:
```bash
# Install in the Python environment Claude uses
which python  # Check which Python Claude is using
# Use that Python to install dependencies
/path/to/python -m pip install mcp requests beautifulsoup4 graze
```

### ChatGPT Custom GPT Issues

**Problem**: Actions can't connect to localhost

**Solution**:
- ChatGPT servers can't access `localhost` from OpenAI's infrastructure
- Options:
  1. **For testing**: Use ngrok to expose local server
     ```bash
     ngrok http 8000
     # Use the ngrok URL in your Custom GPT actions
     ```
  2. **For production**: Deploy to cloud service (AWS, GCP, Azure, Heroku)
  3. **Same network**: Use your local IP address

**Problem**: Schema import fails

**Solution**:
1. Ensure server is running: `curl http://localhost:8000/openapi.json`
2. Check for CORS issues (FastAPI handles this by default)
3. Try manual schema paste instead of URL import

### General Issues

**Problem**: Downloads failing

**Solution**:
1. Check internet connection
2. Verify URL is accessible: `curl -I [URL]`
3. Some sites may block automated downloads
4. Check download directory permissions

**Problem**: Import errors in Python

**Solution**:
```bash
# Verify installation
python -c "from aw_agents.download import DownloadAgent; print('✓ Success')"

# Reinstall if needed
pip install -e .[all]
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black aw_agents tests

# Lint
ruff aw_agents tests

# Type check
mypy aw_agents
```

### Adding a New Agent

1. Create a new directory in `aw_agents/`:
   ```
   aw_agents/myagent/
   ├── __init__.py
   ├── agent.py
   └── core.py (if needed)
   ```

2. Implement `AgentBase` in `agent.py`

3. Add to `aw_agents/__init__.py`:
   ```python
   from aw_agents.myagent import MyAgent
   __all__.append('MyAgent')
   ```

4. Create tests in `tests/test_myagent.py`

5. Update documentation

## Roadmap

- [ ] Additional built-in agents (research, data prep, etc.)
- [ ] Support for more platforms (Slack, Discord, etc.)
- [ ] Agent composition and chaining
- [ ] Persistent state management
- [ ] Authentication and authorization
- [ ] Web UI for agent management
- [ ] CLI tools for deployment

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- [dol](https://github.com/i2mint/dol) - Storage abstractions
- [graze](https://github.com/thorwhalen/graze) - Download and caching
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

Part of the [thorwhalen](https://github.com/thorwhalen) ecosystem.
