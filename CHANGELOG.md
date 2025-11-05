# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-04

### Added
- Initial release of aw-agents
- `AgentBase` protocol for building agents
- `MCPAdapter` for Claude Desktop integration
- `OpenAPIAdapter` for ChatGPT Custom GPT integration
- `DownloadAgent` with smart content downloading
  - Landing page detection
  - Context-aware file naming
  - Special handling for GitHub, HuggingFace, Kaggle
  - Multiple content type support
- Deployment scripts for MCP and API servers
- Comprehensive documentation and examples

### Framework Features
- Unified tool execution interface
- Standard result format (`ToolExecutionResult`)
- JSON schema helpers for tool parameters
- Automatic adapter generation
- Support for multiple agent deployment modes

### Download Agent Features
- Smart URL resolution
- Automatic file extension detection
- graze integration for caching
- Batch download support
- File listing capabilities
