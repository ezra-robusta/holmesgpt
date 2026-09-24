Configure HolmesGPT to use AI models through your [GitHub Copilot](https://github.com/features/copilot) subscription.

> **GitHub Copilot vs GitHub Models**
>
> This page covers **GitHub Copilot** (subscription-based, uses `github_copilot/` prefix). For **GitHub Models** (token-based, uses `github/` prefix), see the [GitHub Models](https://holmesgpt.dev/ai-providers/github/) page.

## Prerequisites

- A GitHub Copilot subscription (individual, business, or enterprise)
- LiteLLM handles authentication automatically via OAuth device flow — no API key needed

## Required Headers

GitHub Copilot's API requires IDE-identifying headers (`Editor-Version`, `Editor-Plugin-Version`, `Copilot-Integration-Id`, `User-Agent`) on every request. Without them, requests fail with `"missing Editor-Version header for IDE auth"`.

Configure them via the `extra_headers` field in your model list configuration, or the `EXTRA_HEADERS` environment variable — see the examples below.

## Configuration

```holmes-config
models:
  copilot-claude:
    model: github_copilot/claude-sonnet-4.5
    extra_headers:
      Editor-Version: "vscode/1.85.1"
      Editor-Plugin-Version: "copilot-chat/0.26.7"
      Copilot-Integration-Id: "vscode-chat"
      User-Agent: "GithubCopilot/1.155.0"
default_model: copilot-claude
```

## Additional Resources

- [LiteLLM GitHub Copilot docs](https://docs.litellm.ai/docs/providers/github_copilot)
- [GitHub Copilot plans](https://github.com/features/copilot)
