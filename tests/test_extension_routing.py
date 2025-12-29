"""
Tests for extension routing and filename generation.

These tests verify that the ExtensionRouter properly handles various cases,
including the ArXiv PDF bug where .html extension was incorrectly assigned.
"""

import pytest
from pathlib import Path
from aw_agents.download.download_core import DownloadEngine


def test_pdf_extension_from_url():
    """Test that PDF URLs get .pdf extension even with wrong content-type."""
    engine = DownloadEngine()

    # ArXiv case: URL has .pdf but content-type might say text/html
    url = 'https://arxiv.org/pdf/2103.00020.pdf'
    filename = engine._generate_filename(url, context='Important ML Paper')

    assert filename == 'Important_ML_Paper.pdf'
    assert filename.endswith('.pdf')


def test_md_extension_priority():
    """Test that .md URLs get .md extension (priority extension)."""
    engine = DownloadEngine()

    url = 'https://github.com/user/repo/blob/main/README.md'
    filename = engine._generate_filename(url, context='Readme')

    assert filename.endswith('.md')


def test_explicit_extension_override():
    """Test that explicit extension has highest priority."""
    engine = DownloadEngine()

    url = 'https://example.com/file.txt'
    filename = engine._generate_filename(
        url, context='MyFile', explicit_extension='json'
    )

    assert filename == 'MyFile.json'


def test_context_based_filename():
    """Test that context is used for filename."""
    engine = DownloadEngine()

    url = 'https://example.com/download'
    filename = engine._generate_filename(url, context='My Important Document')

    # Should sanitize spaces to underscores
    assert 'My_Important_Document' in filename


def test_fallback_to_url_extension():
    """Test fallback to URL extension when no priority match."""
    engine = DownloadEngine()

    url = 'https://example.com/data.json'
    filename = engine._generate_filename(url, context='Data')

    assert filename.endswith('.json')


def test_router_configurability():
    """Test that extension router can be customized."""
    from aw.routing import ExtensionRouter

    # Create custom router with different priority extensions
    custom_router = ExtensionRouter(priority_extensions=frozenset(['.json', '.xml']))

    engine = DownloadEngine(extension_router=custom_router)

    # JSON should now short-circuit
    url = 'https://example.com/file.json'
    filename = engine._generate_filename(url, context='Data')

    assert filename.endswith('.json')


def test_sanitize_filename():
    """Test that special characters are sanitized."""
    engine = DownloadEngine()

    url = 'https://example.com/file.pdf'
    # Context with special characters that should be sanitized
    filename = engine._generate_filename(
        url, context='File: Name <with> Special*Chars?'
    )

    # Special chars should be replaced with underscores
    assert '<' not in filename
    assert '>' not in filename
    assert '*' not in filename
    assert '?' not in filename
    assert ':' not in filename
