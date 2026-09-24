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
        pytest.param(
            'toolsets:\n  x:\n    config:\n      token: "{{ env.TOKEN }}"\n',
            id="undeclared-env-reference",
        ),
        pytest.param(
            "models: {a: {model: openai/gpt-4.1}}\n",
            id="flow-style-section",
        ),
        pytest.param(
            "models:\n  a:\n    model: openai/gpt-4.1\n# Not rendered\ndefault_model: a\n",
            id="comment-on-unrendered-section",
        ),
    ],
)
def test_invalid_block_fails(block):
    with pytest.raises(HolmesConfigError):
        render(block)


MODEL_BLOCK = """\
secrets:
  OPENAI_API_KEY:
    description: OpenAI API key
    example: sk-!secret
secret_name: openai-credentials
# Configure at least one model
models:
  gpt-4.1:
    api_key: "{{ env.OPENAI_API_KEY }}"
    model: openai/gpt-4.1
default_model: gpt-4.1
# Trailing comment
"""


def test_model_block_renders_model_list_and_default_model():
    text = visible_text(render(MODEL_BLOCK))
    cli, helm = text.split("Create a Kubernetes secret:")

    assert "~/.holmes/model_list.yaml" in cli
    assert "\ngpt-4.1:\n  api_key:" in cli
    assert "--model=gpt-4.1" in cli
    assert "modelList:\n  gpt-4.1:" in helm
    assert "- name: MODEL\n    value: gpt-4.1" in helm


def test_comments_render_with_their_section_in_every_tab():
    cli, helm = visible_text(render(MODEL_BLOCK)).split("Create a Kubernetes secret:")

    for tab in (cli, helm):
        assert "# Configure at least one model" in tab
        assert "# Trailing comment" in tab


def test_example_with_exclamation_mark_is_single_quoted():
    text = visible_text(render(MODEL_BLOCK))

    assert "export OPENAI_API_KEY='sk-!secret'" in text
    assert "--from-literal=openai-api-key='sk-!secret'" in text


def test_mcp_servers_block_renders_in_both_tabs():
    block = """\
mcp_servers:
  jenkins:
    description: Jenkins CI/CD server
    config:
      url: https://jenkins.example.com/mcp-server/mcp
      mode: streamable-http
"""
    cli, helm = visible_text(render(block)).split("When using the standalone")

    for tab in (cli, helm):
        assert "mcp_servers:\n  jenkins:" in tab
        assert "mode: streamable-http" in tab
    assert "~/.holmes/config.yaml" in cli
