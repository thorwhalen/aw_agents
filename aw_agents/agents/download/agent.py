"""
Download Agent - Smart content downloader with context-aware naming.

This agent wraps the core download functionality and exposes it through
the AgentBase interface for use with multiple chatbot platforms.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from aw_agents.base import AgentBase, ToolExecutionResult, create_json_schema

# Import the core download logic
try:
    from .download_core import DownloadEngine
except ImportError:
    # Support running as a script
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from aw_agents.agents.download.download_core import DownloadEngine


class DownloadAgent(AgentBase):
    """
    Smart download agent with context-aware naming and intelligent link handling.

    Features:
    - Detects landing pages and finds actual download links
    - Special handling for GitHub, HuggingFace, Kaggle
    - Context-aware file naming
    - Multiple content type support

    >>> agent = DownloadAgent()
    >>> tools = agent.get_tools()
    >>> len(tools) >= 3
    True
    """

    def __init__(
        self, default_download_dir: Optional[Union[str, Path]] = None, **kwargs
    ):
        """
        Initialize the download agent.

        Args:
            default_download_dir: Default directory for downloads
            **kwargs: Additional arguments for DownloadEngine
        """
        self.engine = DownloadEngine(
            default_download_dir=default_download_dir, **kwargs
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tool definitions for this agent."""
        return [
            {
                'name': 'download_content',
                'description': (
                    "Download content from a URL with intelligent handling. "
                    "Automatically detects landing pages and finds actual download links. "
                    "Handles PDFs, datasets, and other content types. "
                    "Generates context-aware filenames. "
                    "Special support for GitHub, HuggingFace, Kaggle, and academic papers."
                ),
                'parameters': create_json_schema(
                    properties={
                        'url': {
                            'type': 'string',
                            'description': 'URL to download from',
                        },
                        'context': {
                            'type': 'string',
                            'description': (
                                'Context about the content (title, description) - '
                                'used to generate a meaningful filename'
                            ),
                        },
                        'download_dir': {
                            'type': 'string',
                            'description': (
                                'Optional: Directory to download to. '
                                'Default: ~/Downloads'
                            ),
                        },
                        'filename': {
                            'type': 'string',
                            'description': 'Optional: Override automatic filename generation',
                        },
                    },
                    required=['url'],
                ),
            },
            {
                'name': 'download_multiple',
                'description': (
                    "Download multiple URLs at once. "
                    "Returns paths to all downloaded files. "
                    "Each URL can have its own context for filename generation."
                ),
                'parameters': create_json_schema(
                    properties={
                        'urls': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of URLs to download',
                        },
                        'contexts': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': (
                                'Optional: List of contexts (one per URL) '
                                'for filename generation'
                            ),
                        },
                        'download_dir': {
                            'type': 'string',
                            'description': (
                                'Optional: Directory to download to. '
                                'Default: ~/Downloads'
                            ),
                        },
                    },
                    required=['urls'],
                ),
            },
            {
                'name': 'list_downloads',
                'description': (
                    "List files in the downloads directory. "
                    "Helps track what has been downloaded."
                ),
                'parameters': create_json_schema(
                    properties={
                        'download_dir': {
                            'type': 'string',
                            'description': (
                                'Optional: Directory to list. ' 'Default: ~/Downloads'
                            ),
                        },
                        'pattern': {
                            'type': 'string',
                            'description': (
                                'Optional: Glob pattern to filter files '
                                '(e.g., "*.pdf", "*.csv")'
                            ),
                        },
                    },
                    required=[],
                ),
            },
        ]

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given arguments."""

        if name == 'download_content':
            return self._download_content(**arguments)
        elif name == 'download_multiple':
            return self._download_multiple(**arguments)
        elif name == 'list_downloads':
            return self._list_downloads(**arguments)
        else:
            return ToolExecutionResult.error_result(
                message=f"Unknown tool: {name}"
            ).to_dict()

    def _download_content(
        self,
        url: str,
        context: Optional[str] = None,
        download_dir: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download a single file."""
        try:
            result = self.engine.download(
                url, context=context, download_dir=download_dir, filename=filename
            )

            # Format message
            message = f"Downloaded successfully to: {result['path']}"

            return ToolExecutionResult.success_result(
                data={'path': result['path'], 'url': result['url']},
                message=message,
                warnings=result.get('warnings', []),
                metadata=result.get('metadata', {}),
            ).to_dict()

        except Exception as e:
            return ToolExecutionResult.error_result(
                message=f"Failed to download {url}: {str(e)}"
            ).to_dict()

    def _download_multiple(
        self,
        urls: List[str],
        contexts: Optional[List[str]] = None,
        download_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download multiple files."""
        try:
            results = self.engine.download_multiple(
                urls, contexts=contexts, download_dir=download_dir
            )

            successful = sum(1 for r in results if r['path'])
            failed = len(results) - successful

            message = f"Downloaded {successful}/{len(results)} files"
            if failed > 0:
                message += f" ({failed} failed)"

            return ToolExecutionResult.success_result(
                data={
                    'results': results,
                    'total': len(results),
                    'successful': successful,
                    'failed': failed,
                },
                message=message,
            ).to_dict()

        except Exception as e:
            return ToolExecutionResult.error_result(
                message=f"Failed to download files: {str(e)}"
            ).to_dict()

    def _list_downloads(
        self, download_dir: Optional[str] = None, pattern: str = "*"
    ) -> Dict[str, Any]:
        """List downloaded files."""
        try:
            target_dir = Path(download_dir or self.engine.default_download_dir)

            if not target_dir.exists():
                return ToolExecutionResult.error_result(
                    message=f"Directory does not exist: {target_dir}"
                ).to_dict()

            files = sorted(target_dir.glob(pattern))
            file_list = [
                {
                    'name': f.name,
                    'path': str(f),
                    'size': f.stat().st_size,
                    'size_formatted': self._format_size(f.stat().st_size),
                }
                for f in files
                if f.is_file()
            ]

            message = f"Found {len(file_list)} files in {target_dir}"

            return ToolExecutionResult.success_result(
                data={
                    'directory': str(target_dir),
                    'files': file_list,
                    'total': len(file_list),
                },
                message=message,
            ).to_dict()

        except Exception as e:
            return ToolExecutionResult.error_result(
                message=f"Failed to list files: {str(e)}"
            ).to_dict()

    @staticmethod
    def _format_size(bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata."""
        return {
            'name': 'DownloadAgent',
            'version': '1.0.0',
            'description': (
                'Smart content downloader with context-aware naming and '
                'intelligent link handling'
            ),
        }


def _print_banner():
    """Print a banner for the download agent."""
    print("=" * 70)
    print("  Download Agent Server")
    print("  Smart content downloader with context-aware naming")
    print("=" * 70)
    print()


def _run_mcp_server():
    """Run the MCP server for Claude Desktop."""
    try:
        from aw_agents.adapters import MCPAdapter
    except ImportError:
        print("❌ Error: MCP adapter not available.")
        print("   Install with: pip install mcp")
        return 1

    try:
        from aw.util import claude_desktop_config
    except ImportError:
        print("❌ Error: aw package not available.")
        print("   Install with: pip install aw")
        return 1

    _print_banner()
    print("Starting MCP server for Claude Desktop...")
    print()

    agent = DownloadAgent()
    adapter = MCPAdapter(agent, "download-agent")

    # Automatically add to Claude Desktop config
    server_config = {
        'command': 'python',
        'args': [str(Path(__file__).absolute())],
    }

    try:
        mcp = claude_desktop_config()
        mcp['download'] = server_config
        print("✓ Automatically added 'download' server to Claude Desktop config!")
        print()
    except Exception as e:
        print(f"⚠️  Warning: Could not automatically update Claude Desktop config: {e}")
        print()
        print("   You can manually add this to your config:")
        print(
            f"   Location: ~/Library/Application Support/Claude/claude_desktop_config.json"
        )
        print()
        print('   {')
        print('     "mcpServers": {')
        print('       "download": {')
        print('         "command": "python",')
        print(f'         "args": ["{Path(__file__).absolute()}"]')
        print('       }')
        print('     }')
        print('   }')
        print()

    # Print instructions
    print("📋 Next steps:")
    print()
    print("1. Restart Claude Desktop")
    print("   - Completely quit Claude Desktop (not just close)")
    print("   - Reopen Claude Desktop")
    print()
    print("2. You should see the download tools available in Claude")
    print("   - Try: 'Download this PDF: [URL]'")
    print()
    print("3. To remove this server later:")
    print("   - Use: claude_desktop_config()['download']")
    print("   - Or manually edit the config file")
    print()
    print("🚀 Starting server now...")
    print("-" * 70)
    print()

    try:
        adapter.run_sync()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        return 0
    except Exception as e:
        print(f"\n❌ Error running server: {e}")
        return 1


def _run_api_server(port: int = 8000, server_url: Optional[str] = None):
    """Run the OpenAPI/FastAPI server for ChatGPT."""
    try:
        from aw_agents.adapters import OpenAPIAdapter
    except ImportError:
        print("❌ Error: OpenAPI adapter not available.")
        print("   Install with: pip install fastapi uvicorn")
        return 1

    _print_banner()
    print(f"Starting FastAPI server for ChatGPT Custom GPT on port {port}...")
    print()

    agent = DownloadAgent()
    adapter = OpenAPIAdapter(agent, title="Download Agent API", server_url=server_url)

    # Print instructions
    print("✓ Server will start momentarily!")
    print()

    if not server_url:
        print("⚠️  IMPORTANT: ChatGPT cannot access localhost!")
        print("   You must use ngrok or deploy to a public server.")
        print()
        print("   Quick setup with ngrok:")
        print(f"   1. Run: ngrok http {port}")
        print("   2. Copy the ngrok URL (e.g., https://abc123.ngrok.io)")
        print("   3. Rerun with: --server-url https://abc123.ngrok.io")
        print()

    print("📋 To use with ChatGPT Custom GPT:")
    print()
    print("1. The server will be available at:")
    if server_url:
        print(f"   {server_url}")
        print(f"   OpenAPI schema: {server_url}/openapi.json")
        print(f"   API docs: {server_url}/docs")
    else:
        print(f"   http://localhost:{port} (local only - not accessible to ChatGPT)")
        print(f"   OpenAPI schema: http://localhost:{port}/openapi.json")
        print(f"   API docs: http://localhost:{port}/docs")
    print()
    print("2. In ChatGPT Custom GPT editor:")
    print("   - Click 'Create new action'")
    if server_url:
        print(f"   - Import schema from: {server_url}/openapi.json")
        print("   - ChatGPT can now call your agent!")
    else:
        print("   - You need a public URL (see ngrok instructions above)")
    print()
    if not server_url:
        print("3. Alternative: Deploy to a cloud service")
        print("   - Railway, Render, Fly.io, etc.")
        print("   - Then use --server-url with your deployment URL")
    else:
        print("3. You're all set!")
        print(f"   - ChatGPT will use: {server_url}")
        print("   - Make sure this server stays running")
    print()
    print("🚀 Starting server now...")
    print("-" * 70)
    print("-" * 70)
    print()

    try:
        adapter.run(port=port)
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        return 0
    except Exception as e:
        print(f"\n❌ Error running server: {e}")
        return 1


def main():
    """Main entry point for running the agent as a server."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run the Download Agent server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run MCP server for Claude Desktop (default)
  python -m aw_agents.agents.download.agent
  python -m aw_agents.agents.download.agent --mcp
  
  # Run API server for ChatGPT
  python -m aw_agents.agents.download.agent --api
  python -m aw_agents.agents.download.agent --api --port 8080
  
  # Run API server with custom server URL (e.g., for ngrok)
  python -m aw_agents.agents.download.agent --api --server-url https://abc123.ngrok.io
        """,
    )

    parser.add_argument(
        '--mcp', action='store_true', help='Run MCP server for Claude Desktop (default)'
    )
    parser.add_argument(
        '--api', action='store_true', help='Run OpenAPI/FastAPI server for ChatGPT'
    )
    parser.add_argument(
        '--port', type=int, default=8000, help='Port for API server (default: 8000)'
    )
    parser.add_argument(
        '--server-url',
        type=str,
        help='Server URL for OpenAPI schema (e.g., ngrok URL like https://abc123.ngrok.io)',
    )

    args = parser.parse_args()

    # Default to MCP if neither specified
    if not args.api and not args.mcp:
        args.mcp = True

    if args.mcp and args.api:
        print("❌ Error: Cannot run both MCP and API servers simultaneously")
        print("   Choose one: --mcp or --api")
        return 1

    if args.mcp:
        return _run_mcp_server()
    elif args.api:
        return _run_api_server(port=args.port, server_url=args.server_url)


if __name__ == '__main__':
    import sys

    sys.exit(main())
