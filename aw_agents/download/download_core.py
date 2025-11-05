"""
Download Agent: Smart content downloader with context-aware naming and intelligent link handling.

This agent can download content from URLs with special handling for:
- Indirect download links (landing pages with actual download links)
- Scientific papers (PDFs from various sources)
- Data from HuggingFace, Kaggle, GitHub
- Context-aware file naming based on conversation context
"""

from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from functools import partial
from urllib.parse import urlparse, urljoin
import mimetypes
import re

import requests
from bs4 import BeautifulSoup
from graze import graze


def _get_home_downloads() -> Path:
    """Get the system-independent Downloads folder."""
    return Path.home() / "Downloads"


def _sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Sanitize a string to be a valid filename.

    >>> _sanitize_filename("My Document")
    'My_Document'
    """
    # Replace invalid characters with underscores
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Replace multiple spaces/underscores with single underscore
    name = re.sub(r'[\s_]+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Limit length
    if len(name) > max_length:
        name = name[:max_length]
    return name


def _infer_extension_from_content_type(content_type: str) -> str:
    """
    Infer file extension from content type.

    >>> _infer_extension_from_content_type('application/pdf')
    '.pdf'
    >>> _infer_extension_from_content_type('text/html')
    '.html'
    """
    ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
    return ext or ''


def _is_likely_landing_page(response: requests.Response) -> bool:
    """
    Check if response is likely a landing page rather than direct content.

    Returns True if:
    - Content type is HTML
    - Content is relatively small (< 1MB)
    - Contains common download link patterns
    """
    content_type = response.headers.get('content-type', '').lower()

    if 'text/html' not in content_type:
        return False

    # If HTML is very large, it's probably the actual content
    if len(response.content) > 1_000_000:
        return False

    # Look for download link patterns
    soup = BeautifulSoup(response.content, 'html.parser')

    # Common patterns for download links
    download_patterns = [
        'download',
        'get file',
        'direct link',
        'pdf',
        '.zip',
        '.tar',
        '.csv',
        '.json',
    ]

    # Check links and buttons
    links = soup.find_all(['a', 'button'])
    for link in links:
        text = link.get_text().lower()
        href = link.get('href', '').lower()

        if any(pattern in text or pattern in href for pattern in download_patterns):
            return True

    return False


def _find_download_link(url: str, response: requests.Response) -> Optional[str]:
    """
    Try to find the actual download link from a landing page.

    Returns the most likely download URL, or None if not found.
    """
    soup = BeautifulSoup(response.content, 'html.parser')

    # Priority patterns for download links
    priority_patterns = [
        (r'\.pdf$', 10),  # Direct PDF links
        (r'download', 8),
        (r'\.zip$', 7),
        (r'\.tar\.gz$', 7),
        (r'\.csv$', 6),
        (r'\.json$', 6),
        (r'/raw/', 5),  # GitHub raw links
        (r'/blob/', 3),  # GitHub blob (need to convert to raw)
    ]

    candidates = []

    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text().lower()

        # Make absolute URL
        abs_url = urljoin(url, href)

        # Score this link
        score = 0
        for pattern, points in priority_patterns:
            if re.search(pattern, abs_url.lower()) or re.search(pattern, text):
                score += points

        if score > 0:
            candidates.append((score, abs_url))

    if candidates:
        # Return highest scoring candidate
        candidates.sort(reverse=True)
        return candidates[0][1]

    return None


def _handle_github_url(url: str) -> str:
    """
    Convert GitHub blob URLs to raw URLs for direct download.

    >>> _handle_github_url('https://github.com/user/repo/blob/main/file.pdf')
    'https://raw.githubusercontent.com/user/repo/main/file.pdf'
    """
    if 'github.com' in url and '/blob/' in url:
        # Convert blob to raw
        url = url.replace('github.com', 'raw.githubusercontent.com')
        url = url.replace('/blob/', '/')
    return url


def _handle_huggingface_url(url: str) -> str:
    """
    Ensure HuggingFace URLs point to direct download.

    >>> _handle_huggingface_url('https://huggingface.co/datasets/user/dataset/blob/main/data.csv')
    'https://huggingface.co/datasets/user/dataset/resolve/main/data.csv'
    """
    if 'huggingface.co' in url and '/blob/' in url:
        # Convert blob to resolve for direct download
        url = url.replace('/blob/', '/resolve/')
    return url


class DownloadEngine:
    """
    Core download engine with smart link handling and context-aware naming.

    >>> engine = DownloadEngine()
    >>> # engine.download("https://example.com/paper.pdf", context="Important ML Paper")
    """

    def __init__(
        self,
        default_download_dir: Optional[Union[str, Path]] = None,
        *,
        user_agent: str = "DownloadAgent/1.0",
        timeout: int = 30,
        max_redirects: int = 5,
    ):
        """
        Initialize the download agent.

        Args:
            default_download_dir: Default directory for downloads (default: ~/Downloads)
            user_agent: User agent string for HTTP requests
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
        """
        self.default_download_dir = Path(default_download_dir or _get_home_downloads())
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_redirects = max_redirects

        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})

    def _resolve_download_url(self, url: str) -> tuple[str, Optional[str]]:
        """
        Resolve the actual download URL, handling landing pages.

        Returns:
            (download_url, warning_message)
        """
        # Handle special domains
        url = _handle_github_url(url)
        url = _handle_huggingface_url(url)

        # Make initial request
        try:
            response = self.session.head(
                url, timeout=self.timeout, allow_redirects=True
            )

            # If HEAD doesn't work, try GET with streaming
            if response.status_code >= 400:
                response = self.session.get(
                    url, timeout=self.timeout, stream=True, allow_redirects=True
                )
        except Exception as e:
            return (
                url,
                f"Warning: Could not verify URL ({e}). Will attempt download anyway.",
            )

        # Check if this is a landing page
        if _is_likely_landing_page(response):
            # Try to find actual download link
            actual_url = _find_download_link(url, response)

            if actual_url:
                return (
                    actual_url,
                    f"Detected landing page, found download link: {actual_url}",
                )
            else:
                return (
                    url,
                    "Warning: This appears to be a landing page, but couldn't find download link. Please verify.",
                )

        return url, None

    def _generate_filename(
        self,
        url: str,
        context: Optional[str] = None,
        response: Optional[requests.Response] = None,
    ) -> str:
        """
        Generate a good filename based on context and URL.

        Priority:
        1. Context provided by user
        2. Content-Disposition header
        3. URL path
        4. Fallback to URL-based name
        """
        filename = None
        extension = None

        # Try to get extension from content type
        if response:
            content_type = response.headers.get('content-type', '')
            extension = _infer_extension_from_content_type(content_type)

            # Try Content-Disposition header
            content_disp = response.headers.get('content-disposition', '')
            if 'filename=' in content_disp:
                match = re.search(r'filename="?([^"]+)"?', content_disp)
                if match:
                    filename = match.group(1)

        # Use context if provided
        if context and not filename:
            filename = _sanitize_filename(context)

        # Fall back to URL path
        if not filename:
            path = urlparse(url).path
            filename = Path(path).stem or 'download'
            filename = _sanitize_filename(filename)

            # Get extension from URL if not from content-type
            if not extension:
                url_ext = Path(path).suffix
                if url_ext:
                    extension = url_ext

        # Ensure we have an extension
        if not extension:
            extension = '.bin'  # Generic binary

        # Combine filename and extension
        if not filename.endswith(extension):
            filename = filename + extension

        return filename

    def download(
        self,
        url: str,
        *,
        context: Optional[str] = None,
        download_dir: Optional[Union[str, Path]] = None,
        filename: Optional[str] = None,
        force_redownload: bool = False,
    ) -> Dict[str, Any]:
        """
        Download content from a URL with smart handling.

        Args:
            url: URL to download from
            context: Context about the content (used for filename generation)
            download_dir: Directory to download to (default: self.default_download_dir)
            filename: Override automatic filename generation
            force_redownload: Force re-download even if cached

        Returns:
            Dictionary with:
                - 'path': Path to downloaded file
                - 'url': Final URL downloaded from
                - 'warnings': List of warning messages
                - 'metadata': Additional metadata

        Example:
            >>> engine = DownloadEngine()
            >>> # result = engine.download("https://example.com/paper.pdf", context="ML Paper")
            >>> # print(result['path'])
        """
        warnings = []

        # Resolve actual download URL
        final_url, warning = self._resolve_download_url(url)
        if warning:
            warnings.append(warning)

        # Determine download directory
        target_dir = Path(download_dir or self.default_download_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Configure graze for this download
        cache_dir = target_dir
        my_graze = partial(graze, rootdir=cache_dir)

        # Generate filename if not provided
        if not filename:
            # Need to make a request to get headers for filename generation
            try:
                head_response = self.session.head(final_url, timeout=self.timeout)
                filename = self._generate_filename(final_url, context, head_response)
            except Exception:
                filename = self._generate_filename(final_url, context, None)

        # Download using graze
        try:
            # Use graze to download and cache
            file_path = target_dir / filename

            # Download
            response = self.session.get(final_url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            metadata = {
                'content_type': response.headers.get('content-type'),
                'content_length': response.headers.get('content-length'),
                'final_url': final_url,
            }

            return {
                'path': str(file_path),
                'url': final_url,
                'warnings': warnings,
                'metadata': metadata,
            }

        except Exception as e:
            raise RuntimeError(f"Failed to download {final_url}: {e}") from e

    def download_multiple(
        self,
        urls: List[str],
        *,
        contexts: Optional[List[str]] = None,
        download_dir: Optional[Union[str, Path]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Download multiple URLs.

        Args:
            urls: List of URLs to download
            contexts: Optional list of contexts (same length as urls)
            download_dir: Directory to download to

        Returns:
            List of result dictionaries (one per URL)
        """
        if contexts is None:
            contexts = [None] * len(urls)

        if len(contexts) != len(urls):
            raise ValueError("contexts must be same length as urls")

        results = []
        for url, context in zip(urls, contexts):
            try:
                result = self.download(url, context=context, download_dir=download_dir)
                results.append(result)
            except Exception as e:
                results.append(
                    {
                        'path': None,
                        'url': url,
                        'warnings': [f"Failed: {e}"],
                        'metadata': {},
                    }
                )

        return results


# Convenience function
def download_content(
    url: str,
    *,
    context: Optional[str] = None,
    download_dir: Optional[Union[str, Path]] = None,
) -> str:
    """
    Convenience function to download a single URL and return the path.

    Example:
        >>> # path = download_content("https://example.com/file.pdf", context="Important doc")
    """
    engine = DownloadEngine(default_download_dir=download_dir)
    result = engine.download(url, context=context)
    return result['path']
