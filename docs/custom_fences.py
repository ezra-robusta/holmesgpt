"""
Custom fence processors for MkDocs documentation.

Fences available:
- yaml-toolset-config: Creates 3 tabs (Holmes CLI, Holmes Helm Chart, Robusta Helm Chart) for toolset configurations
- yaml-helm-values: Creates 2 tabs (Holmes Helm Chart, Robusta Helm Chart) for Helm-only configurations like permissions
- holmes-config: Renders deployment-neutral Holmes configuration (secrets, toolsets, mcp_servers, models,
  default_model) as Holmes CLI and Holmes Helm Chart tabs. Blocks are validated against
  docs/_shared/holmes-config.schema.json.
- robusta-region: Creates 3 tabs (US, EU, AP) for any text containing api.robusta.dev, platform.robusta.dev, or
  sp.robusta.dev. Plain URLs render as code blocks; markdown links `[text](url)` render as clickable links.
"""

import html
import json
import re
import uuid
from pathlib import Path
from typing import Optional

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
HOLMES_SECRET_NAME = "holmes-secrets"
HOLMES_NAMESPACE = "holmes"
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$")


class _IndentedListDumper(yaml.SafeDumper):
    """Indent list items under their key, as the hand-written examples do."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


class HolmesConfigError(SuperFencesException):
    """An invalid `holmes-config` block. Superfences swallows any other exception
    from a fence and renders the block as plain code; this one fails the build."""


def validate_holmes_config(spec) -> None:
    """Raise HolmesConfigError when a `holmes-config` block does not match its schema."""
    problems = [
        f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
        for error in sorted(
            HOLMES_CONFIG_VALIDATOR.iter_errors(spec), key=lambda e: list(e.path)
        )
    ]
    if isinstance(spec, dict) and "default_model" in spec:
        if spec["default_model"] not in (spec.get("models") or {}):
            problems.append(f"default_model {spec['default_model']!r} is not in models")
    if problems:
        raise HolmesConfigError(f"invalid holmes-config block: {'; '.join(problems)}")


def _top_level_sections(source: str) -> dict:
    """Split the block's YAML text at its top-level keys.

    Rendering slices the author's text instead of re-dumping the parsed data, so
    comments and key order survive into every tab. Column-0 comments and blank
    lines go with the key that follows them.
    """
    sections: dict = {}
    current = None
    pending: list = []
    for line in source.splitlines():
        match = TOP_LEVEL_KEY_RE.match(line)
        if match:
            current = match.group(1)
            sections[current] = pending + [line]
            pending = []
        elif not line.strip() or line.startswith("#"):
            pending.append(line)
        elif current is not None:
            sections[current].extend(pending + [line])
            pending = []
    return {key: "\n".join(lines).strip("\n") for key, lines in sections.items()}


def _section_body(section: str) -> Optional[str]:
    """The indented body of a block-style section, dedented to column 0; None for
    a flow-style section such as `models: {...}`."""
    lines = section.split("\n")
    key_line = next(i for i, ln in enumerate(lines) if TOP_LEVEL_KEY_RE.match(ln))
    if TOP_LEVEL_KEY_RE.match(lines[key_line]).group(2).split("#")[0].strip():
        return None
    body = lines[key_line + 1 :]
    indents = [
        len(ln) - len(ln.lstrip())
        for ln in body
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    base = min(indents, default=0)
    return "\n".join(ln[base:] if ln.strip() else "" for ln in body).strip("\n")


def _rename_section(section: str, old: str, new: str) -> str:
    return re.sub(rf"^{old}:", f"{new}:", section, count=1, flags=re.MULTILINE)


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
    config = [sections[k] for k in ("toolsets", "mcp_servers") if k in sections]
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
            _section_body(sections["models"]) or _dump(spec["models"]),
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
        literals = [
            f"  --from-literal={_secret_key(name)}={_shell_quoted_example(name, s)} \\"
            for name, s in secrets.items()
        ]
        yield _code_step(
            md,
            "Create a Kubernetes secret:",
            "bash",
            "\n".join(
                [
                    f"kubectl create secret generic {HOLMES_SECRET_NAME} \\",
                    *literals,
                    f"  -n {HOLMES_NAMESPACE}",
                ]
            ),
        )
        yield (
            '<div class="admonition note">\n'
            '<p class="admonition-title">Namespace must match Holmes\' deployment</p>\n'
            "<p>Create the secret in the namespace where Holmes runs "
            f"(<code>{HOLMES_NAMESPACE}</code> here; change it to match your "
            "installation). A secret in the wrong namespace silently resolves to an "
            "empty environment variable, and authentication fails with no clear "
            "error.</p>\n</div>\n"
        )
        env_vars = [
            {
                "name": name,
                "valueFrom": {
                    "secretKeyRef": {
                        "name": HOLMES_SECRET_NAME,
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
    values += [sections[k] for k in ("toolsets", "mcp_servers") if k in sections]
    if "models" in sections:
        values.append(_rename_section(sections["models"], "models", "modelList"))
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
        "helm upgrade --install holmes robusta/holmes -f values.yaml",
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
    spec = yaml.safe_load(source)
    validate_holmes_config(spec)
    sections = _top_level_sections(source)
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


def toolset_config_fence_format(source, language, css_class, options, md, **kwargs):
    """
    Format YAML content into Holmes CLI, Holmes Helm Chart, and Robusta Helm Chart tabs for toolset configuration.
    This fence does NOT process Jinja2, so {{ env.VAR }} stays as-is.
    """
    # Generate unique IDs for this tab group to prevent conflicts
    tab_group_id = str(uuid.uuid4()).replace("-", "_")
    tab_id_1 = f"__tabbed_{tab_group_id}_1"
    tab_id_2 = f"__tabbed_{tab_group_id}_2"
    group_name = f"__tabbed_{tab_group_id}"

    # Escape HTML in the source to prevent XSS
    escaped_source = html.escape(source)

    # Build the tabbed HTML structure for CLI, Holmes Helm, and Robusta
    tabs_html = f"""
<div class="tabbed-set" data-tabs="1:3">
<input checked="checked" id="{tab_id_1}" name="{group_name}" type="radio">
<input id="{tab_id_2}" name="{group_name}" type="radio">
<div class="tabbed-labels">
<label for="{tab_id_1}">Holmes CLI</label>
<label for="{tab_id_2}">Holmes Helm Chart</label>
</div>
<div class="tabbed-content">
<div class="tabbed-block">
<p>Add the following to <strong>~/.holmes/config.yaml</strong>. Create the file if it doesn't exist:</p>
<pre><code class="language-yaml">{escaped_source}</code></pre>
</div>
<div class="tabbed-block">
<p>When using the <strong>standalone Holmes Helm Chart</strong>, update your <code>values.yaml</code>:</p>
<pre><code class="language-yaml">{escaped_source}</code></pre>
<p>Apply the configuration:</p>
<pre><code class="language-bash">helm upgrade holmes holmes/holmes --values=values.yaml</code></pre>
</div>
</div>
</div>"""

    return tabs_html


def helm_tabs_fence_format(source, language, css_class, options, md, **kwargs):
    """
    Format YAML content into Holmes and Robusta Helm Chart tabs.
    This fence does NOT process Jinja2, so {{ env.VAR }} stays as-is.
    """
    # Generate unique IDs for this tab group to prevent conflicts
    tab_group_id = str(uuid.uuid4()).replace("-", "_")
    tab_id_1 = f"__tabbed_{tab_group_id}_1"
    group_name = f"__tabbed_{tab_group_id}"

    # Escape HTML in the source to prevent XSS
    escaped_source = html.escape(source)

    # Build the tabbed HTML structure
    tabs_html = f"""
<div class="tabbed-set" data-tabs="1:2">
<input checked="checked" id="{tab_id_1}" name="{group_name}" type="radio">
<div class="tabbed-labels">
<label for="{tab_id_1}">Holmes Helm Chart</label>
</div>
<div class="tabbed-content">
<div class="tabbed-block">
<p>When using the <strong>standalone Holmes Helm Chart</strong>, update your <code>values.yaml</code>:</p>
<pre><code class="language-yaml">{escaped_source}</code></pre>
<p>Apply the configuration:</p>
<pre><code class="language-bash">helm upgrade holmes holmes/holmes --values=values.yaml</code></pre>
</div>
</div>
</div>"""

    return tabs_html


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
