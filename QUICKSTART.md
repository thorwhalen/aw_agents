# Quick Start Guide

## Installation

```bash
cd /path/to/aw_agents
pip install -e .
```

## Test the Download Agent

```python
from aw_agents.agents.download import DownloadAgent

# Create agent
agent = DownloadAgent()

# Download a file
result = agent.execute_tool('download_content', {
    'url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
    'context': 'Test PDF Document'
})

print(f"Success: {result['success']}")
if result['success']:
    print(f"Downloaded to: {result['data']['path']}")
```

## Try the Interactive Notebook

```bash
jupyter notebook aw_agents/agents/download/demo_download_agent.ipynb
```

The notebook includes comprehensive examples and tests.

## Deploy to Claude Desktop

**Easiest Way - Automatic Configuration:**

```bash
# The agent automatically configures Claude Desktop!
python -m aw_agents.agents.download.agent --mcp
```

That's it! The agent will:
- Automatically add itself to your Claude Desktop config
- Start the MCP server
- Tell you to restart Claude Desktop

**Alternative - Manual Setup:**

1. **Generate MCP server script:**
   ```bash
   python scripts/deploy_mcp.py DownloadAgent --output ~/mcp_download.py
   ```

2. **Add to Claude Desktop config:**
   
   ```python
   from aw.util import claude_desktop_config
   
   mcp = claude_desktop_config()
   mcp['download'] = {
       'command': 'python',
       'args': ['/absolute/path/to/mcp_download.py']
   }
   ```

3. **Restart Claude Desktop**

4. **Test in Claude:**
   ```
   Download this paper for me: https://arxiv.org/pdf/2103.00020.pdf
   Context: "Attention is All You Need"
   ```

**Config file locations** (if you need to edit manually):
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Note**: Install MCP first if needed: `pip install -e .[mcp]`

## Deploy to ChatGPT

1. **Generate API server script:**
   ```bash
   python scripts/deploy_api.py DownloadAgent --output ~/api_download.py
   ```

2. **Start the server:**
   ```bash
   python ~/api_download.py
   ```

3. **Create Custom GPT:**
   - Go to https://chat.openai.com/gpts/editor
   - Create a new GPT
   - Add instructions about helping users download files
   - Add action using schema from: `http://localhost:8000/openapi.json`

**Note**: Install FastAPI first if needed: `pip install -e .[api]`

## Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=aw_agents --cov-report=term-missing

# Run doctests
python -m doctest aw_agents/agents/download/download_core.py
```

## Key Features

✅ **Smart URL handling** - Auto-converts GitHub, HuggingFace URLs  
✅ **Context-aware naming** - Uses descriptions for filenames  
✅ **Landing page detection** - Finds actual download links  
✅ **Multiple downloads** - Batch download support  
✅ **File listing** - Track downloaded files  

## Documentation

- **Full README**: `README.md`
- **API Documentation**: Run API server and visit `/docs`
- **Examples**: See `examples.py` (if created)
- **Demo Notebook**: `aw_agents/agents/download/demo_download_agent.ipynb`

## Troubleshooting

**Import errors:**
```bash
pip install -e .
```

**Missing dependencies:**
```bash
pip install -e .[all]  # Install everything
```

**Claude doesn't see tools:**
- Check config file path
- Use absolute paths (not `~/`)
- Restart Claude Desktop completely
- Check logs: `~/Library/Logs/Claude/` (macOS)

**ChatGPT can't connect:**
- ChatGPT servers can't access localhost
- Use ngrok: `ngrok http 8000`
- Or deploy to cloud service

## Next Steps

1. ✅ Review the demo notebook
2. ✅ Test locally with Python
3. ✅ Deploy to Claude or ChatGPT
4. ✅ Read the full README for advanced usage
5. ✅ Create your own agents using the same pattern

Happy agent building! 🚀
