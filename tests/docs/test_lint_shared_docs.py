import subprocess
import sys
from pathlib import Path

import pytest

LINT = Path(__file__).resolve().parents[2] / "scripts" / "lint_shared_docs.py"

CLEAN_SNIPPET = """\
Intro with an [absolute link](https://holmesgpt.dev/data-sources/builtin-toolsets/kubernetes/).

| Field | Meaning |
|-------|---------|
| `api_url` | Where to connect |

```holmes-config
toolsets:
  rabbitmq/core:
    enabled: true
```

Inline code like `{:target}` and `--8<--` is allowed.
"""


def lint(tmp_path, text):
    snippet = tmp_path / "snippet.md"
    snippet.write_text(text)
    return subprocess.run(
        [sys.executable, str(LINT), str(snippet)], capture_output=True, text=True
    )


def test_clean_snippet_passes(tmp_path):
    result = lint(tmp_path, CLEAN_SNIPPET)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    "line, rule",
    [
        ('!!! note "Title"\n    Body', "admonition"),
        ('=== "Holmes CLI"\n\n    Tab body', "content tab"),
        ('[Link](https://example.com){:target="_blank"}', "attribute list"),
        ('--8<-- "snippets/toolset_refresh_warning.md"', "snippet include"),
        ("![Diagram](https://example.com/diagram.png)", "image"),
        ("See [the other page](kubernetes.md).", "relative link"),
        ("See [a page](https://holmesgpt.dev/no-such-page/).", "broken link"),
        ("```multi-instance\ntoolset: x\n```", "custom fence"),
        ("Text[^1]", "footnote"),
    ],
)
def test_forbidden_construct_fails(tmp_path, line, rule):
    result = lint(tmp_path, CLEAN_SNIPPET + "\n" + line + "\n")
    assert result.returncode == 1
    assert f": {rule}: " in result.stdout
