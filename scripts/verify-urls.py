#!/usr/bin/env python3
"""Verify reachable HTTP(S) URLs referenced by docs and skill files."""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
# Improved regex: handles parentheses in URLs
URL_RE = re.compile(r"https?://[^\s)>]+(?:\([^)]*\))?")


def _compile_skip_patterns() -> list[re.Pattern[str]]:
    """Compile URL template/placeholder patterns to skip."""
    return [
        re.compile(r"\$[A-Za-z_]+"),           # $name, $pkg, etc.
        re.compile(r"<[A-Za-z_]+>"),           # <repo>, <pkg>, etc.
        re.compile(r"\{\{[^}]+\}\}"),          # {{variable}}
        re.compile(r"%[A-Za-z_]+%"),           # %VAR%
        re.compile(r"example\.com"),           # example.com placeholder
        re.compile(r"github\.com/[^/]+/<"),    # github.com/user/<placeholder
        re.compile(r"github\.com/[^/]+/\$"),   # github.com/user/$placeholder
        re.compile(r"registry\.npmjs\.org/\$"), # registry.npmjs.org/$placeholder
        re.compile(r"api\.npmjs\.org/.*[<$\{]"), # api.npmjs.org with placeholders
    ]


SKIP_PATTERNS = _compile_skip_patterns()


def is_template_url(url: str) -> bool:
    """Check if URL contains template/placeholder patterns."""
    for pattern in SKIP_PATTERNS:
        if pattern.search(url):
            return True
    return False


def iter_markdown_files() -> list[Path]:
    """Find all markdown files to check."""
    files: list[Path] = []
    for root in (ROOT / "README.md", ROOT / "SECURITY.md", ROOT / "CITATION.cff", ROOT / "skills"):
        if root.is_file():
            files.append(root)
        elif root.exists():
            files.extend(sorted(root.glob("**/*.md")))
    return files


def iter_urls() -> list[tuple[Path, str]]:
    """Extract URLs from markdown files, filtering templates."""
    pairs: list[tuple[Path, str]] = []
    for path in iter_markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in URL_RE.finditer(text):
            url = match.group(0).rstrip(".,;")
            if not is_template_url(url):
                pairs.append((path, url))
    return pairs


def request_url(url: str, method: str, *, depth: int = 0) -> str | None:
    """Request URL and return error string if failed, None if OK.

    Args:
        url: URL to check
        method: HTTP method (HEAD or GET)
        depth: Recursion depth for 405 retry (max 1)
    """
    if depth > 1:
        return "max retry depth exceeded"

    request = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": "skill-repo-architecture-url-check"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if 200 <= response.status < 400:
                return None
            return f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if method == "HEAD" and exc.code == 405 and depth == 0:
            return request_url(url, "GET", depth=depth + 1)
        return f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return str(exc.reason)
    except TimeoutError:
        return "timeout"
    except ValueError as exc:
        return f"invalid URL: {exc}"


def main() -> int:
    failures: list[str] = []
    seen: set[str] = set()
    for path, url in iter_urls():
        if url in seen:
            continue
        seen.add(url)
        failure = request_url(url, "HEAD")
        if failure:
            failures.append(f"{path.relative_to(ROOT)}: {url}: {failure}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(f"verified {len(seen)} URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())