# Using Multiple Providers

--8<-- "_shared/ai-providers/using-multiple-providers.md"

## Holmes CLI

Models can be used by name:

```bash
holmes ask "what pods are failing?" --model=sonnet --no-interactive
holmes ask "analyze deployment" --model=azure-5 --no-interactive
```

A model list file can also hold credentials directly:

```yaml
sonnet:
    aws_access_key_id: "your-access-key"
    aws_region_name: us-east-1
    aws_secret_access_key: "your-secret-key"
    model: bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0
    temperature: 1
    thinking:
        budget_tokens: 10000
        type: enabled

azure-5:
    api_base: https://your-resource.openai.azure.com
    api_key: "your-api-key"
    api_version: 2025-01-01-preview
    model: azure/gpt-5
    temperature: 0
```

**Custom path:** To load the model list from a different location, set `MODEL_LIST_FILE_LOCATION=/path/to/model_list.yaml`.
