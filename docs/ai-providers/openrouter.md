# OpenRouter

--8<-- "_shared/ai-providers/openrouter.md"

## Holmes CLI

You can also pass the model directly on the command line.

**Method 1:**

```bash
export OPENROUTER_API_KEY="sk-or-..."  # your OpenRouter key
holmes ask "hello" --model="openrouter/anthropic/claude-sonnet-4.5" --no-interactive
```

**Method 2:**

```bash
export OPENAI_API_BASE="https://openrouter.ai/api/v1"
export OPENAI_API_KEY="sk-or-..."  # your OpenRouter key
holmes ask "hello" --model="openai/anthropic/claude-sonnet-4.5" --no-interactive
```
