"""
Download Agent - Smart content downloader with context-aware naming.

This agent wraps the core download functionality and exposes it through
the AgentBase interface for use with multiple chatbot platforms.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from aw_agents.base import AgentBase, ToolExecutionResult, create_json_schema

# Import the core download logic from the original implementation
import sys
sys.path.insert(0, str(Path(__file__).parent))
from download_core import DownloadEngine


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
        self,
        default_download_dir: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        """
        Initialize the download agent.
        
        Args:
            default_download_dir: Default directory for downloads
            **kwargs: Additional arguments for DownloadEngine
        """
        self.engine = DownloadEngine(
            default_download_dir=default_download_dir,
            **kwargs
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
                            'description': 'URL to download from'
                        },
                        'context': {
                            'type': 'string',
                            'description': (
                                'Context about the content (title, description) - '
                                'used to generate a meaningful filename'
                            )
                        },
                        'download_dir': {
                            'type': 'string',
                            'description': (
                                'Optional: Directory to download to. '
                                'Default: ~/Downloads'
                            )
                        },
                        'filename': {
                            'type': 'string',
                            'description': 'Optional: Override automatic filename generation'
                        }
                    },
                    required=['url']
                )
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
                            'description': 'List of URLs to download'
                        },
                        'contexts': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': (
                                'Optional: List of contexts (one per URL) '
                                'for filename generation'
                            )
                        },
                        'download_dir': {
                            'type': 'string',
                            'description': (
                                'Optional: Directory to download to. '
                                'Default: ~/Downloads'
                            )
                        }
                    },
                    required=['urls']
                )
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
                                'Optional: Directory to list. '
                                'Default: ~/Downloads'
                            )
                        },
                        'pattern': {
                            'type': 'string',
                            'description': (
                                'Optional: Glob pattern to filter files '
                                '(e.g., "*.pdf", "*.csv")'
                            )
                        }
                    },
                    required=[]
                )
            }
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
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Download a single file."""
        try:
            result = self.engine.download(
                url,
                context=context,
                download_dir=download_dir,
                filename=filename
            )
            
            # Format message
            message = f"Downloaded successfully to: {result['path']}"
            
            return ToolExecutionResult.success_result(
                data={'path': result['path'], 'url': result['url']},
                message=message,
                warnings=result.get('warnings', []),
                metadata=result.get('metadata', {})
            ).to_dict()
            
        except Exception as e:
            return ToolExecutionResult.error_result(
                message=f"Failed to download {url}: {str(e)}"
            ).to_dict()
    
    def _download_multiple(
        self,
        urls: List[str],
        contexts: Optional[List[str]] = None,
        download_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Download multiple files."""
        try:
            results = self.engine.download_multiple(
                urls,
                contexts=contexts,
                download_dir=download_dir
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
                    'failed': failed
                },
                message=message
            ).to_dict()
            
        except Exception as e:
            return ToolExecutionResult.error_result(
                message=f"Failed to download files: {str(e)}"
            ).to_dict()
    
    def _list_downloads(
        self,
        download_dir: Optional[str] = None,
        pattern: str = "*"
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
                    'size_formatted': self._format_size(f.stat().st_size)
                }
                for f in files
                if f.is_file()
            ]
            
            message = f"Found {len(file_list)} files in {target_dir}"
            
            return ToolExecutionResult.success_result(
                data={
                    'directory': str(target_dir),
                    'files': file_list,
                    'total': len(file_list)
                },
                message=message
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
            )
        }
