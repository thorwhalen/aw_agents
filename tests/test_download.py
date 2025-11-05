"""Tests for Download Agent."""

import pytest
from pathlib import Path
from aw_agents.download import DownloadAgent


def test_agent_tools():
    """Test that agent returns expected tools."""
    agent = DownloadAgent()
    tools = agent.get_tools()
    
    assert len(tools) == 3
    tool_names = {t['name'] for t in tools}
    assert tool_names == {'download_content', 'download_multiple', 'list_downloads'}


def test_agent_metadata():
    """Test agent metadata."""
    agent = DownloadAgent()
    metadata = agent.get_metadata()
    
    assert metadata['name'] == 'DownloadAgent'
    assert 'version' in metadata
    assert 'description' in metadata


def test_list_downloads():
    """Test listing downloads."""
    agent = DownloadAgent()
    result = agent.execute_tool('list_downloads', {})
    
    assert result['success'] is True
    assert 'data' in result
    assert 'directory' in result['data']


def test_unknown_tool():
    """Test handling of unknown tool."""
    agent = DownloadAgent()
    result = agent.execute_tool('nonexistent_tool', {})
    
    assert result['success'] is False
    assert 'Unknown tool' in result['message']


# Add more tests as needed
# These would require network access or mocking:
# - test_download_content()
# - test_download_multiple()
# - test_github_url_handling()
# - test_landing_page_detection()
