"""
Download Agent: Smart content downloader with context-aware naming and intelligent link handling.

This agent can download content from URLs with special handling for:
- Indirect download links (landing pages with actual download links)
- Scientific papers (PDFs from various sources)
- Data from HuggingFace, Kaggle, GitHub
- Context-aware file naming based on conversation context
"""

from pathlib import Path
from typing import Optional, Union, List, Dict, Any, TYPE_CHECKING
from functools import partial
from urllib.parse import urlparse, urljoin
import mimetypes
import re

import requests
from bs4 import BeautifulSoup
from graze import graze

# Import routing from aw package
if TYPE_CHECKING:
    from aw.routing import ExtensionRouter

try:
    from aw.routing import ExtensionRouter as _ExtensionRouter
except ImportError:
    # Fallback if aw.routing not available
    _ExtensionRouter = None


# Extensions that should be treated as placeholders and replaced when better
# information becomes available from response headers or sniffed bytes.
PLACEHOLDER_EXTENSIONS = {'.bin', '.tmp', '.dat', '.download'}


def _normalize_extension(extension: Optional[str]) -> Optional[str]:
    """Return a cleaned extension or None if it's unusable."""

    if not extension:
        return None

    if not extension.startswith('.'):
        extension = f'.{extension}'

    if extension.lower() in PLACEHOLDER_EXTENSIONS:
        return None

    return extension


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


def _remove_url_crap(url: str) -> str:
    url = url.replace("?utm_source=chatgpt.com", "")
    url = url.replace("&utm_source=chatgpt.com", "")
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
        extension_router: Optional['ExtensionRouter'] = None,
    ):
        """
        Initialize the download agent.

        Args:
            default_download_dir: Default directory for downloads (default: ~/Downloads)
            user_agent: User agent string for HTTP requests
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
            extension_router: Custom extension router (uses default if None)
        """
        self.default_download_dir = Path(default_download_dir or _get_home_downloads())
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_redirects = max_redirects

        # Initialize extension router
        if _ExtensionRouter is not None:
            self.extension_router = extension_router or _ExtensionRouter()
        else:
            # Fallback to old behavior if aw.routing not available
            self.extension_router = None

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
        explicit_extension: Optional[str] = None,
    ) -> str:
        """
        Generate a good filename based on context and URL.

        Priority:
        1. Context provided by user
        2. Content-Disposition header
        3. URL path
        4. Fallback to URL-based name

        Extension detection uses ExtensionRouter (if available) for smart routing.
        """
        filename = None
        extension = None

        # Try Content-Disposition header first (may have complete filename)
        if response:
            content_disp = response.headers.get('content-disposition', '')
            if 'filename=' in content_disp:
                match = re.search(r'filename="?([^"]+)"?', content_disp)
                if match:
                    filename = match.group(1)
                    # If Content-Disposition provides complete filename, use it
                    return filename

        # Use context if provided
        if context and not filename:
            filename = _sanitize_filename(context)

        # Fall back to URL path
        if not filename:
            path = urlparse(url).path
            filename = Path(path).stem or 'download'
            filename = _sanitize_filename(filename)

        # Determine extension using router
        if self.extension_router:
            # Gather context for routing
            content = b''
            content_type = ''

            if response:
                content_type = response.headers.get('content-type', '')
                # Try to read first chunk for magic byte detection
                # (only if we have response content available)
                try:
                    if hasattr(response, 'content'):
                        content = response.content[:100]  # First 100 bytes
                except Exception:
                    pass

            # Use router to detect extension
            extension = _normalize_extension(
                self.extension_router(
                    url=url,
                    content=content,
                    content_type=content_type,
                    explicit_extension=explicit_extension,
                )
            )

        if not extension and response:
            content_type = response.headers.get('content-type', '')
            extension = _normalize_extension(
                _infer_extension_from_content_type(content_type)
            )

        if not extension:
            url_ext = Path(urlparse(url).path).suffix
            extension = _normalize_extension(url_ext) or '.bin'

        # Combine filename and extension
        if not filename.endswith(extension):
            filename = filename + extension

        return filename

    def _detect_extension_from_response(
        self,
        url: str,
        response: Optional[requests.Response],
        *,
        content_sample: bytes = b'',
        explicit_extension: Optional[str] = None,
    ) -> Optional[str]:
        """Infer an extension from response metadata/content."""

        if not response:
            return None

        content_type = response.headers.get('content-type', '')
        extension = None

        if self.extension_router:
            try:
                extension = _normalize_extension(
                    self.extension_router(
                        url=url,
                        content=content_sample or b'',
                        content_type=content_type,
                        explicit_extension=explicit_extension,
                    )
                )
            except Exception:
                extension = None

        if not extension and content_type:
            extension = _normalize_extension(
                _infer_extension_from_content_type(content_type)
            )

        if not extension:
            url_ext = Path(urlparse(url).path).suffix
            extension = _normalize_extension(url_ext)

        return extension

    def _ensure_extension_matches_content(
        self,
        filename: str,
        *,
        url: str,
        response: Optional[requests.Response],
        content_sample: bytes,
        user_supplied: bool,
    ) -> tuple[str, Optional[str]]:
        """
        Make sure the filename extension aligns with detected content type.

        Returns the (maybe updated) filename and an optional warning message.
        """

        detected_extension = self._detect_extension_from_response(
            url,
            response,
            content_sample=content_sample,
        )

        if not detected_extension:
            return filename, None

        if not detected_extension.startswith('.'):
            detected_extension = f'.{detected_extension}'

        current_ext = Path(filename).suffix
        if current_ext.lower() == detected_extension.lower():
            return filename, None

        can_replace = (
            not user_supplied
            or not current_ext
            or current_ext.lower() in PLACEHOLDER_EXTENSIONS
        )

        if not can_replace:
            return filename, None

        new_filename = f"{Path(filename).stem}{detected_extension}"
        content_type = response.headers.get('content-type') if response else None
        warning = (
            "Adjusted filename extension to match detected content type"
            f" ({content_type or 'unknown'}): {filename} -> {new_filename}"
        )
        return new_filename, warning

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
        url = _remove_url_crap(url)

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
        user_provided_filename = filename is not None
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

            chunk_iter = response.iter_content(chunk_size=8192)
            first_chunk = next(chunk_iter, b'')

            filename, extension_warning = self._ensure_extension_matches_content(
                filename,
                url=final_url,
                response=response,
                content_sample=first_chunk,
                user_supplied=user_provided_filename,
            )
            if extension_warning:
                warnings.append(extension_warning)

            file_path = target_dir / filename

            with open(file_path, 'wb') as f:
                if first_chunk:
                    f.write(first_chunk)
                for chunk in chunk_iter:
                    if chunk:
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
