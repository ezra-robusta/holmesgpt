# GitHub Copilot

--8<-- "_shared/ai-providers/github-copilot.md"

## Holmes CLI

On first run, LiteLLM will prompt you to authorize the device via a GitHub URL. After authorization, the token is cached locally.

**Alternative — environment variable:**

```bash
export EXTRA_HEADERS='{"Editor-Version": "vscode/1.85.1", "Editor-Plugin-Version": "copilot-chat/0.26.7", "Copilot-Integration-Id": "vscode-chat", "User-Agent": "GithubCopilot/1.155.0"}'

holmes ask "what pods are failing?" --model="github_copilot/claude-sonnet-4.5"
```
