"""
Base classes and protocols for AW agents.

This module provides the foundation for building AI agents that can be
deployed to multiple chatbot platforms (Claude, ChatGPT, etc.).
"""

from typing import Protocol, Any, Dict, Optional
from abc import ABC, abstractmethod


class AgentBase(ABC):
    """
    Base class for all AW agents.
    
    Agents should inherit from this and implement the core methods.
    Adapters (MCP, OpenAPI) will wrap these agents for deployment.
    """
    
    @abstractmethod
    def get_tools(self) -> list[Dict[str, Any]]:
        """
        Return tool definitions for this agent.
        
        Each tool should have:
        - name: str
        - description: str
        - parameters: dict (JSON schema)
        
        Returns:
            List of tool definitions
        """
        pass
    
    @abstractmethod
    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments
        
        Returns:
            Result dictionary with at least:
            - success: bool
            - data: Any
            - message: Optional[str]
            - warnings: Optional[list[str]]
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get agent metadata.
        
        Returns:
            Metadata including name, version, description
        """
        return {
            'name': self.__class__.__name__,
            'version': '1.0.0',
            'description': self.__doc__ or 'No description'
        }


class ToolExecutionResult:
    """Standard result format for tool execution."""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        message: Optional[str] = None,
        warnings: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.message = message
        self.warnings = warnings or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'warnings': self.warnings,
            'metadata': self.metadata
        }
    
    @classmethod
    def success_result(
        cls,
        data: Any,
        message: Optional[str] = None,
        **kwargs
    ) -> 'ToolExecutionResult':
        """Create a success result."""
        return cls(success=True, data=data, message=message, **kwargs)
    
    @classmethod
    def error_result(
        cls,
        message: str,
        data: Any = None,
        **kwargs
    ) -> 'ToolExecutionResult':
        """Create an error result."""
        return cls(success=False, data=data, message=message, **kwargs)


def create_json_schema(
    properties: Dict[str, Dict[str, Any]],
    required: Optional[list[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Helper to create JSON schema for tool parameters.
    
    >>> schema = create_json_schema(
    ...     properties={
    ...         'url': {'type': 'string', 'description': 'URL to process'},
    ...         'context': {'type': 'string', 'description': 'Context info'}
    ...     },
    ...     required=['url']
    ... )
    >>> schema['type']
    'object'
    >>> 'url' in schema['required']
    True
    """
    return {
        'type': 'object',
        'properties': properties,
        'required': required or [],
        **kwargs
    }
