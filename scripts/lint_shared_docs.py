"""Check that shared docs snippets stay in the portable Markdown subset.

Files under docs/_shared/ are included by this site's pages and by other sites
that render the same Markdown with a different renderer. They may use only
CommonMark, GFM tables, fenced code blocks (including `holmes-config`) and
absolute links. MkDocs-only syntax (admonitions, content tabs, attribute lists,
snippet includes, images, the other custom fences and Markdown extensions) and
relative links, which resolve against the including page, are errors.

Usage: python scripts/lint_shared_docs.py [path ...]   (default: docs/_shared)
"""

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DEFAULT_PATHS = [DOCS_DIR / "_shared"]
SITE_URL = "https://holmesgpt.dev/"
SITE_VERSION_RE = re.compile(r"^(latest|dev|\d+\.\d+\.\d+)/")
ALLOWED_CUSTOM_FENCE = "holmes-config"
ABSOLUTE_LINK_RE = re.compile(r"^(https?://|mailto:)")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([^\s{`]*)")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")

# (rule, pattern) pairs checked on every line outside fenced code, with inline
# code spans removed first.
LINE_RULES = [
    ("admonition", re.compile(r"^\s*(!!!|\?\?\?\+?)\s")),
    ("content tab", re.compile(r"^\s*===\+?\s+\"")),
    ("attribute list", re.compile(r"\{:[^}]*\}|\{\s*[.#][A-Za-z][^}]*\}|\{\s*[\w-]+=")),
    ("snippet include", re.compile(r"-{2}8<-{2}")),
    ("image", re.compile(r"!\[|<img\b", re.IGNORECASE)),
    ("footnote", re.compile(r"\[\^[^\]]+\]")),
    ("abbreviation", re.compile(r"^\*\[[^\]]+\]:")),
    ("definition list", re.compile(r"^:\s{3}")),
    ("emoji shortcode", re.compile(r":(material|fontawesome|octicons|simple)-[\w-]+:")),
    ("keys", re.compile(r"\+\+[\w+-]+\+\+")),
    ("mark", re.compile(r"==[^=\s][^=]*==")),
    ("caret", re.compile(r"\^\^")),
    ("math", re.compile(r"\$\$")),
    ("markdown in HTML", re.compile(r"\bmarkdown=|<\w+[^>]*\bmarkdown\b")),
]
LINK_RES = [
    re.compile(r"\]\(\s*<?([^)\s>]+)"),  # [text](target)
    re.compile(r"^\s*\[[^\]]+\]:\s*<?(\S+?)>?(\s|$)"),  # [ref]: target
    re.compile(r"""\bhref\s*=\s*["']([^"']+)["']""", re.IGNORECASE),
]


class _IgnoreTagsLoader(yaml.SafeLoader):
    """Reads mkdocs.yml, whose `!!python/name:` tags need MkDocs itself."""


_IgnoreTagsLoader.add_multi_constructor("", lambda loader, suffix, node: None)


def custom_fence_names() -> set:
    """The custom fences registered in mkdocs.yml."""
    config = yaml.load((REPO_ROOT / "mkdocs.yml").read_text(), Loader=_IgnoreTagsLoader)
    names = set()
    for ext in config.get("markdown_extensions", []):
        if isinstance(ext, dict) and "pymdownx.superfences" in ext:
            for fence in ext["pymdownx.superfences"].get("custom_fences", []):
                names.add(fence["name"])
    return names


def site_page_exists(url: str) -> bool:
    """Whether a holmesgpt.dev URL points at a page or file in docs/.

    Relative links are checked by MkDocs; absolute ones are not, so this keeps
    the snippets' links to this site from breaking silently.
    """
    path = SITE_VERSION_RE.sub("", url[len(SITE_URL) :].split("#")[0].split("?")[0])
    stem = path.rstrip("/")
    candidates = [DOCS_DIR / "index.md"] if not stem else []
    candidates += [
        DOCS_DIR / f"{stem}.md",
        DOCS_DIR / stem / "index.md",
        DOCS_DIR / stem,
    ]
    return any(c.is_file() for c in candidates)


def lint_file(path: Path, forbidden_fences: set) -> list:
    problems = []
    fence = None
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        match = FENCE_RE.match(line)
        if fence is not None:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
                and not match.group(2)
            ):
                fence = None
            continue
        if match:
            fence = match.group(1)
            language = match.group(2)
            if language in forbidden_fences:
                problems.append(
                    (number, "custom fence", f"`{language}` renders only on this site")
                )
            continue
        text = INLINE_CODE_RE.sub("", line)
        for rule, pattern in LINE_RULES:
            if pattern.search(text):
                problems.append((number, rule, line.strip()))
        for pattern in LINK_RES:
            for link in pattern.finditer(text):
                target = link.group(1)
                if not ABSOLUTE_LINK_RE.match(target):
                    problems.append(
                        (
                            number,
                            "relative link",
                            f"{target} (use an absolute https:// URL)",
                        )
                    )
                elif target.startswith(SITE_URL) and not site_page_exists(target):
                    problems.append(
                        (number, "broken link", f"{target} matches no page in docs/")
                    )
    if fence is not None:
        problems.append((number, "fenced code", "unterminated fenced code block"))
    return problems


def main(argv: list) -> int:
    paths = [Path(p) for p in argv] or DEFAULT_PATHS
    files = sorted(f for p in paths for f in ([p] if p.is_file() else p.rglob("*.md")))
    forbidden = custom_fence_names() - {ALLOWED_CUSTOM_FENCE}
    failures = 0
    for file in files:
        for number, rule, detail in lint_file(file, forbidden):
            print(f"{file}:{number}: {rule}: {detail}")
            failures += 1
    print(f"{len(files)} file(s) checked, {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
