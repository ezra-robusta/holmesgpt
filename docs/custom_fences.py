"""
Custom fence processors for MkDocs documentation.

Fences available:
- holmes-config: Renders deployment-neutral Holmes configuration (secrets, toolsets, mcp_servers, models,
  default_model, secret_name) as Holmes CLI and Holmes Helm Chart tabs. Blocks are validated against
  docs/_shared/holmes-config.schema.json.
- robusta-region: Creates 3 tabs (US, EU, AP) for any text containing api.robusta.dev, platform.robusta.dev, or
  sp.robusta.dev. Plain URLs render as code blocks; markdown links `[text](url)` render as clickable links.
"""

import html
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import markdown
import yaml  # type: ignore
from jsonschema import Draft202012Validator
from pymdownx.superfences import SuperFencesException

ROBUSTA_REGIONS = (("US", ""), ("EU", "eu"), ("AP", "ap"))
ROBUSTA_DOMAIN_RE = re.compile(r"\b(api|platform|sp)\.robusta\.dev\b")
MARKDOWN_LINK_RE = re.compile(r"^\[([^\]]+)\]\(([^)\s]+)\)(\{[^}]*\})?$")


def _rewrite_robusta_domain(text: str, region_infix: str) -> str:
    """Rewrite api/platform/sp .robusta.dev to the regional variant."""
    if not region_infix:
        return text
    return ROBUSTA_DOMAIN_RE.sub(rf"\1.{region_infix}.robusta.dev", text)


HOLMES_CONFIG_SCHEMA_PATH = (
    Path(__file__).parent / "_shared" / "holmes-config.schema.json"
)
HOLMES_CONFIG_VALIDATOR = Draft202012Validator(
    json.loads(HOLMES_CONFIG_SCHEMA_PATH.read_text())
)
# The release name and chart of the Helm installation guide, so the rendered
# command upgrades the release the reader installed.
HOLMES_HELM_UPGRADE = "helm upgrade holmesgpt robusta/holmes -f values.yaml"
SECRET_NAMESPACE_NOTE_PATH = (
    Path(__file__).parent / "snippets" / "secret_namespace_note.md"
)
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$")


class _IndentedListDumper(yaml.SafeDumper):
    """Indent list items under their key, as the hand-written examples do."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


class HolmesConfigError(SuperFencesException):
    """An invalid `holmes-config` block. Superfences swallows any other exception
    from a fence and renders the block as plain code; this one fails the build."""


ENV_REFERENCE_RE = re.compile(r"\{\{\s*env\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
# Sections rendered from the author's text, which must be in block style.
TEXT_SECTIONS = ("toolsets", "mcp_servers", "models")


@dataclass
class _Section:
    """One top-level key of a block, as the author wrote it.

    `lead` holds the column-0 comments above the key, so every comment renders
    with its section in every tab.
    """

    lead: list
    key_line: str
    body: list

    def as_key(self, name: str) -> str:
        """The section under its key, renamed to `name`."""
        key_line = re.sub(r"^[^:]+:", f"{name}:", self.key_line, count=1)
        return _strip_blank_lines([*self.lead, key_line, *self.body])

    def as_file(self) -> str:
        """The section's body as a file of its own, dedented to column 0."""
        indents = [
            len(ln) - len(ln.lstrip())
            for ln in self.body
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
        base = min(indents, default=0)
        body = [ln[base:] if ln[:base].isspace() else ln for ln in self.body]
        return _strip_blank_lines([*self.lead, *body])


def _strip_blank_lines(lines: list) -> str:
    return "\n".join(lines).strip("\n")


def _uncommented(line: str) -> str:
    """The line without its YAML comment (a `#` at the start or after a space,
    outside quotes)."""
    quote = None
    for i, char in enumerate(line):
        if quote:
            quote = None if char == quote else quote
        elif char in "'\"":
            quote = char
        elif char == "#" and (i == 0 or line[i - 1].isspace()):
            return line[:i]
    return line


def _sections(source: str) -> dict:
    """Split the block's YAML text at its top-level keys.

    Rendering slices the author's text instead of re-dumping the parsed data, so
    comments and key order survive into every tab.
    """
    sections: dict = {}
    current = None
    pending: list = []
    for line in source.splitlines():
        match = TOP_LEVEL_KEY_RE.match(line)
        if match:
            current = sections[match.group(1)] = _Section(pending, line, [])
            pending = []
        elif not line.strip() or line.startswith("#"):
            pending.append(line)
        elif current is not None:
            current.body.extend(pending + [line])
            pending = []
    # Comments after the last key go with the last section that renders as text.
    last_text = [k for k in sections if k in TEXT_SECTIONS]
    if last_text:
        sections[last_text[-1]].body.extend(pending)
    return sections


def parse_holmes_config(source: str) -> tuple:
    """The block's data and its sections; HolmesConfigError when the block is
    not valid YAML, does not match the schema, or cannot be rendered."""
    try:
        spec = yaml.safe_load(source)
    except yaml.YAMLError as e:
        raise HolmesConfigError(f"invalid holmes-config block: {e}") from e
    problems = [
        f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
        for error in sorted(
            HOLMES_CONFIG_VALIDATOR.iter_errors(spec), key=lambda e: list(e.path)
        )
    ]
    if problems:
        raise HolmesConfigError(f"invalid holmes-config block: {'; '.join(problems)}")
    if "default_model" in spec and spec["default_model"] not in spec["models"]:
        problems.append(f"default_model {spec['default_model']!r} is not in models")
    sections = _sections(source)
    for key, section in sections.items():
        if key not in TEXT_SECTIONS and any(
            ln.lstrip().startswith("#") for ln in section.lead + section.body
        ):
            problems.append(
                f"comments on {key} would not render in any tab; put them in the prose"
            )
    for key in TEXT_SECTIONS:
        if (
            key in sections
            and _uncommented(sections[key].key_line).split(":", 1)[1].strip()
        ):
            problems.append(f"{key} must be written in block style")
    # A reader follows one block, so it declares every variable it reads.
    referenced = {
        name
        for line in source.splitlines()
        for name in ENV_REFERENCE_RE.findall(_uncommented(line))
    }
    problems += [
        f"{{{{ env.{name} }}}} is not declared in secrets"
        for name in sorted(referenced - set(spec.get("secrets") or {}))
    ]
    if problems:
        raise HolmesConfigError(f"invalid holmes-config block: {'; '.join(problems)}")
    return spec, sections


def _dump(data) -> str:
    return yaml.dump(data, Dumper=_IndentedListDumper, sort_keys=False).rstrip()


def _secret_key(env_name: str) -> str:
    return env_name.lower().replace("_", "-")


def _shell_quoted_example(env_name: str, secret: dict) -> str:
    """Double quotes let an example be a command substitution; a `!` inside them
    triggers interactive history expansion, so such examples are single-quoted."""
    value = secret.get("example") or f"<{env_name}>"
    if "!" in value and "'" not in value:
        return f"'{value}'"
    return f'"{value}"'


def _code_step(md, intro: str, lang: str, code: str) -> str:
    """Highlighted like a regular fenced block, so tabs match hand-written pages."""
    # pymdown-extensions has no public call that highlights with the site's
    # configured settings; superfences' preprocessor holds that configuration,
    # so its method gives the same markup, line anchors and copy button.
    block = md.preprocessors["fenced_code_block"].highlight(
        src=code, language=lang, options={}, md=md, classes=[], id_value="", attrs={}
    )
    return f"<p>{intro}</p>\n{block}\n"


def _cli_steps(spec: dict, sections: dict, md):
    secrets = spec.get("secrets") or {}
    if secrets:
        yield _code_step(
            md,
            "Set the environment variables:",
            "bash",
            "\n".join(
                f"export {name}={_shell_quoted_example(name, s)}  # {s['description']}"
                for name, s in secrets.items()
            ),
        )
    config = [
        sections[k].as_key(k) for k in ("toolsets", "mcp_servers") if k in sections
    ]
    if config:
        yield _code_step(
            md,
            "Add the following to <strong>~/.holmes/config.yaml</strong>. "
            "Create the file if it doesn't exist:",
            "yaml",
            "\n\n".join(config),
        )
    if "models" in spec:
        yield _code_step(
            md,
            "Add the following to <strong>~/.holmes/model_list.yaml</strong>. "
            "Create the file if it doesn't exist:",
            "yaml",
            sections["models"].as_file(),
        )
    if config:
        yield _code_step(
            md,
            "After making changes to your configuration, run:",
            "bash",
            "holmes toolset refresh",
        )
    if "models" in spec:
        model = spec.get("default_model") or next(iter(spec["models"]))
        yield _code_step(
            md,
            "Run Holmes with the model:",
            "bash",
            f'holmes ask "what pods are failing?" --model={model}',
        )


def _helm_steps(spec: dict, sections: dict, md):
    secrets = spec.get("secrets") or {}
    env_vars = []
    if secrets:
        command = [f"kubectl create secret generic {spec['secret_name']}"] + [
            f"  --from-literal={_secret_key(name)}={_shell_quoted_example(name, s)}"
            for name, s in secrets.items()
        ]
        yield _code_step(
            md, "Create a Kubernetes secret:", "bash", " \\\n".join(command)
        )
        yield (
            markdown.markdown(
                SECRET_NAMESPACE_NOTE_PATH.read_text(), extensions=["admonition"]
            )
            + "\n"
        )
        env_vars = [
            {
                "name": name,
                "valueFrom": {
                    "secretKeyRef": {
                        "name": spec["secret_name"],
                        "key": _secret_key(name),
                    }
                },
            }
            for name in secrets
        ]
    if spec.get("default_model"):
        # The chart reads no default-model value; Holmes reads $MODEL.
        env_vars.append({"name": "MODEL", "value": spec["default_model"]})
    values = [_dump({"additionalEnvVars": env_vars})] if env_vars else []
    values += [
        sections[k].as_key(k) for k in ("toolsets", "mcp_servers") if k in sections
    ]
    if "models" in sections:
        values.append(sections["models"].as_key("modelList"))
    yield _code_step(
        md,
        "When using the <strong>standalone Holmes Helm Chart</strong>, update your "
        "<code>values.yaml</code>:",
        "yaml",
        "\n\n".join(values),
    )
    yield _code_step(
        md,
        "Apply the configuration:",
        "bash",
        HOLMES_HELM_UPGRADE,
    )


def holmes_config_fence_format(source, language, css_class, options, md, **kwargs):
    """Render a `holmes-config` block as Holmes CLI and Holmes Helm Chart tabs.

    The block is deployment-neutral Holmes configuration (see
    `docs/_shared/holmes-config.schema.json`):

        ```holmes-config
        secrets:        # env vars whose values come from a secret
          RABBITMQ_PASSWORD:
            description: Password of the management user
            example: holmes_password
        secret_name: rabbitmq-credentials  # the Kubernetes secret holding them
        toolsets:       # as in the Holmes config file
          rabbitmq/core:
            enabled: true
            config: ...
        mcp_servers:    # as in the Holmes config file
        models:         # a model list
        default_model:  # a key of models
        ```

    Every block is validated against the schema; an invalid one fails the build.
    The fence does not process Jinja2, so `{{ env.VAR }}` stays as-is.
    """
    spec, sections = parse_holmes_config(source)
    tabs = (
        ("Holmes CLI", _cli_steps(spec, sections, md)),
        ("Holmes Helm Chart", _helm_steps(spec, sections, md)),
    )

    group_name = f"__tabbed_{uuid.uuid4().hex}"
    inputs_html = ""
    labels_html = ""
    blocks_html = ""
    for index, (label, steps) in enumerate(tabs, start=1):
        tab_id = f"{group_name}_{index}"
        checked_attr = ' checked="checked"' if index == 1 else ""
        inputs_html += (
            f'<input{checked_attr} id="{tab_id}" name="{group_name}" type="radio">\n'
        )
        labels_html += f'<label for="{tab_id}">{label}</label>\n'
        blocks_html += f'<div class="tabbed-block">\n{"".join(steps)}</div>\n'

    return (
        f'<div class="tabbed-set" data-tabs="1:{len(tabs)}">\n'
        f"{inputs_html}"
        f'<div class="tabbed-labels">\n{labels_html}</div>\n'
        f'<div class="tabbed-content">\n{blocks_html}</div>\n'
        "</div>"
    )


def robusta_region_fence_format(source, language, css_class, options, md, **kwargs):
    """
    Render the source as three tabs (US, EU, AP), rewriting `api.robusta.dev`,
    `platform.robusta.dev` and `sp.robusta.dev` to the regional subdomain in each tab.

    Auto-detects two input shapes:

    1. A markdown link `[text](url)` (with optional `{...}` attribute list) →
       renders as a clickable link per region.
    2. Anything else → renders as a code block per region. Pass `lang=<name>`
       in the fence options to set syntax highlighting (e.g. `lang=yaml`).

    Usage:

        ```robusta-region
        https://api.robusta.dev/litellm/model_prices_and_context_window.json
        ```

        ```robusta-region
        [platform.robusta.dev](https://platform.robusta.dev/)
        ```

        ````robusta-region lang=yaml
        holmes:
          additionalEnvVars:
            - name: ROBUSTA_API_ENDPOINT
              value: "https://api.robusta.dev"
        ````
    """
    inner = source.strip()
    # Inline `{lang=yaml}` attrs arrive via kwargs['attrs']; config-level options
    # come from mkdocs.yml (currently unused).
    attrs = kwargs.get("attrs") or {}
    inner_lang = attrs.get("lang") or (options or {}).get("lang") or ""
    lang_class_attr = (
        f' class="language-{html.escape(inner_lang)}"' if inner_lang else ""
    )

    link_match = MARKDOWN_LINK_RE.match(inner)

    tab_group_id = str(uuid.uuid4()).replace("-", "_")
    group_name = f"__tabbed_{tab_group_id}"

    inputs_html = ""
    labels_html = ""
    blocks_html = ""

    for index, (region_name, region_infix) in enumerate(ROBUSTA_REGIONS, start=1):
        tab_id = f"{group_name}_{index}"
        checked_attr = ' checked="checked"' if index == 1 else ""
        inputs_html += (
            f'<input{checked_attr} id="{tab_id}" name="{group_name}" type="radio">\n'
        )
        labels_html += f'<label for="{tab_id}">{region_name}</label>\n'

        if link_match:
            link_text, link_url, _attrs = link_match.groups()
            regional_text = _rewrite_robusta_domain(link_text, region_infix)
            regional_url = _rewrite_robusta_domain(link_url, region_infix)
            inner_html = (
                f'<p><a href="{html.escape(regional_url)}">'
                f"{html.escape(regional_text)}</a></p>"
            )
        else:
            regional_content = _rewrite_robusta_domain(inner, region_infix)
            inner_html = (
                f"<pre><code{lang_class_attr}>{html.escape(regional_content)}"
                "</code></pre>"
            )

        blocks_html += f'<div class="tabbed-block">{inner_html}</div>\n'

    return (
        '<div class="tabbed-set" data-tabs="1:3">\n'
        f"{inputs_html}"
        f'<div class="tabbed-labels">\n{labels_html}</div>\n'
        f'<div class="tabbed-content">\n{blocks_html}</div>\n'
        "</div>"
    )


# Central page that documents how multi-instance toolsets work. Linked from every
# rendered ``multi-instance`` block so each toolset page doesn't repeat the prose.
MULTI_INSTANCE_DOC_URL = "/data-sources/multi-instance-toolsets/"


def _reindent(text: str, spaces: int) -> str:
    """Dedent ``text`` to its common leading whitespace, then indent every
    non-empty line by ``spaces``. Used to nest a flat config example under
    ``instances:`` at the correct YAML depth."""
    lines = text.strip("\n").split("\n")
    nonempty = [ln for ln in lines if ln.strip()]
    base = min((len(ln) - len(ln.lstrip()) for ln in nonempty), default=0)
    pad = " " * spaces
    return "\n".join(pad + ln[base:] if ln.strip() else "" for ln in lines)


def multi_instance_fence_format(source, language, css_class, options, md, **kwargs):
    """Render the standard "Multiple Instances" section for a toolset.

    The fence body is YAML with three keys:

        ```multi-instance
        toolset: grafana/dashboards   # the toolset key used in config examples
        name: Grafana                 # human-readable name (optional; derived from toolset)
        config: |                     # a single-instance config example for this toolset
          api_url: <your grafana url>
          api_key: <your api key>
        ```

    It emits a note admonition that:
    - explains the toolset can connect to several instances via ``instances:``;
    - shows the supplied config example nested under ``instances:`` (two entries);
    - notes the auto-injected ``instance`` parameter and ``<toolset>_list_instances``
      tool that appear when more than one instance is configured;
    - links to the central Multiple Instances page for the full behaviour.

    The same component renders identically for every toolset, so each page imports
    it in one fenced block instead of repeating the prose.
    """
    spec = yaml.safe_load(source) or {}
    toolset = str(spec.get("toolset", "")).strip()
    name = str(spec.get("name") or toolset or "this").strip()
    config = str(spec.get("config", "")).strip()
    if not toolset or not config:
        raise ValueError(
            "multi-instance fence requires 'toolset' and 'config' keys in its YAML body"
        )

    # The wrapper names the discovery tool by replacing '/' with '_' in the toolset name.
    list_tool = spec.get("list_tool") or (toolset.replace("/", "_") + "_list_instances")

    fields = _reindent(config, 10)
    yaml_example = (
        "toolsets:\n"
        f"  {toolset}:\n"
        "    enabled: true\n"
        "    config:\n"
        "      instances:\n"
        f"        - name: prod\n{fields}\n"
        f"        - name: staging\n{fields}\n"
    )

    name_e = html.escape(name)
    list_tool_e = html.escape(str(list_tool))
    return (
        f"<p>The {name_e} toolset can connect to more than one {name_e} instance. "
        "List each one under <code>instances:</code> with a unique <code>name</code>. "
        "Any config field set outside <code>instances:</code> becomes a default that "
        "every instance inherits, so shared settings only need to be written once.</p>\n"
        f'<pre><code class="language-yaml">{html.escape(yaml_example)}</code></pre>\n'
        "<p>When more than one instance is configured, HolmesGPT automatically adds an "
        f"<code>instance</code> parameter to every {name_e} tool (so it can pick which "
        f"instance to query) and a <code>{list_tool_e}</code> tool to list the configured "
        "instances. With a single instance — including the flat config without "
        "<code>instances:</code> — the tools are unchanged and fully backwards "
        "compatible.</p>\n"
        f'<p>See <a href="{MULTI_INSTANCE_DOC_URL}">Multiple Instances</a> for the full '
        "behaviour, including global defaults and health reporting.</p>"
    )
