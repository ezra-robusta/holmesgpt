import html
import re

import markdown
import pytest

from docs.custom_fences import HolmesConfigError, holmes_config_fence_format

VALID_BLOCK = """\
secrets:
  RABBITMQ_PASSWORD:
    description: Password of the management user
    example: holmes_password
secret_name: rabbitmq-credentials
toolsets:
  rabbitmq/core:
    enabled: true
    config:
      clusters:
        - id: rabbitmq # must be unique
          password: "{{ env.RABBITMQ_PASSWORD }}"
"""


def render(block: str) -> str:
    """Render a page holding one block, with the extensions mkdocs.yml uses for it."""
    return markdown.markdown(
        f"```holmes-config\n{block}```\n",
        extensions=["admonition", "pymdownx.highlight", "pymdownx.superfences"],
        extension_configs={
            "pymdownx.superfences": {
                "custom_fences": [
                    {
                        "name": "holmes-config",
                        "class": "holmes-config",
                        "format": holmes_config_fence_format,
                    }
                ]
            }
        },
    )


def visible_text(page: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", page))


def test_valid_block_renders_cli_and_helm_tabs():
    page = render(VALID_BLOCK)
    text = visible_text(page)

    assert ">Holmes CLI</label>" in page
    assert ">Holmes Helm Chart</label>" in page
    assert 'export RABBITMQ_PASSWORD="holmes_password"' in text
    assert "kubectl create secret generic rabbitmq-credentials" in text
    assert "name: rabbitmq-credentials" in text
    assert "key: rabbitmq-password" in text
    assert "# must be unique" in text  # comments survive
    assert "helm upgrade holmesgpt robusta/holmes -f values.yaml" in text


@pytest.mark.parametrize(
    "block",
    [
        pytest.param("toolsets: []\n", id="schema-error"),
        pytest.param("toolsets: [unclosed\n", id="yaml-syntax-error"),
        pytest.param(
            "models:\n  a:\n    model: openai/gpt-4.1\ndefault_model: [1]\n",
            id="non-string-default-model",
        ),
        pytest.param(
            "models:\n  a:\n    model: openai/gpt-4.1\ndefault_model: b\n",
            id="default-model-not-in-models",
        ),
        pytest.param(
            "secrets:\n  KEY:\n    description: A key\n"
            "toolsets:\n  x:\n    enabled: true\n",
            id="missing-secret-name",
        ),
    ],
)
def test_invalid_block_fails(block):
    with pytest.raises(HolmesConfigError):
        render(block)
