# Anthropic

--8<-- "_shared/ai-providers/anthropic.md"

## Holmes CLI Without a Model List

The Holmes CLI can also take the model name and API key directly:

```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
holmes ask "what pods are failing?" --model="anthropic/claude-sonnet-4-5"
```

You can also pass the API key directly as a command-line parameter:

```bash
holmes ask "what pods are failing?" --model="anthropic/claude-sonnet-4-5" --api-key="your-api-key"
```
