Define multiple model configurations and switch between them by name. This is useful when you work with different AI providers, API keys, endpoints, or parameters.

## Configuration

```holmes-config
# Only include the providers you're using
secrets:
  AZURE_API_KEY:
    description: Azure API key
    example: "..."
  ANTHROPIC_API_KEY:
    description: Anthropic API key
    example: sk-ant-...
  AWS_ACCESS_KEY_ID:
    description: AWS access key ID
    example: AKIA...
  AWS_SECRET_ACCESS_KEY:
    description: AWS secret access key
    example: "..."
  OPENAI_API_KEY:
    description: OpenAI API key
    example: sk-...
# Configure the model list using the environment variables
models:
  # Standard OpenAI
  openai-4.1:
    api_key: "{{ env.OPENAI_API_KEY }}"
    model: openai/gpt-4.1
    temperature: 0

  # Azure AI Foundry Models
  azure-41:
    api_key: "{{ env.AZURE_API_KEY }}"
    model: azure/gpt-4.1
    api_base: https://your-resource.openai.azure.com/
    api_version: "2025-01-01-preview"
    temperature: 0

  azure-gpt-5:
    api_key: "{{ env.AZURE_API_KEY }}"
    model: azure/gpt-5
    api_base: https://your-resource.openai.azure.com/
    api_version: "2025-01-01-preview"
    temperature: 1 # only 1 is supported for gpt-5 models

  # Anthropic Models
  claude-sonnet-4:
    api_key: "{{ env.ANTHROPIC_API_KEY }}"
    model: claude-sonnet-4-20250514
    temperature: 1
    thinking:
      budget_tokens: 10000
      type: enabled

  claude-opus-4-1:
    api_key: "{{ env.ANTHROPIC_API_KEY }}"
    model: claude-opus-4-1-20250805
    temperature: 0

  # AWS Bedrock
  bedrock-claude:
    aws_access_key_id: "{{ env.AWS_ACCESS_KEY_ID }}"
    aws_region_name: us-east-1
    aws_secret_access_key: "{{ env.AWS_SECRET_ACCESS_KEY }}"
    model: bedrock/anthropic.claude-sonnet-4-20250514-v1:0
    temperature: 1
    thinking:
      budget_tokens: 10000
      type: enabled
```

Use a model by its name (key) in the list, not the underlying model identifier. All configuration (API keys, endpoints, temperature, etc.) is loaded from the model list, and environment variable substitution is supported using `{{ env.VARIABLE_NAME }}` syntax. When multiple models are defined, clients can specify the `model` parameter via the HTTP API. If deployed with Robusta, a model selector dropdown is also available in the UI.

## Model Parameters

Each model in the list can accept any parameter supported by LiteLLM for that provider. The `model` parameter is required, while authentication requirements vary by provider. Any additional LiteLLM parameters will be passed directly through to the provider.

**Required Parameter:**

- `model`: Model identifier (provider-specific format)

**Common Parameters:**

- `api_key`: API key for authentication where required (can use `{{ env.VAR_NAME }}` syntax)
- `temperature`: Creativity level (0-2, lower is more deterministic)

**Additional Parameters:**

You can pass any LiteLLM-supported parameter for your provider. Examples include:

- **Azure**: `api_base`, `api_version`, `deployment_id`
- **Anthropic**: `thinking` (with `budget_tokens` and `type`)
- **AWS Bedrock**: `aws_access_key_id`, `aws_secret_access_key`, `aws_region_name`, `aws_session_token`
- **Google Vertex**: `vertex_project`, `vertex_location`

Refer to [LiteLLM documentation](https://docs.litellm.ai/docs/providers) for the complete list of parameters supported by each provider.

## User Experience

When multiple models are configured:

### HTTP API
Clients can specify the model in their API requests:
```json
{
  "ask": "What pods are failing?",
  "model": "claude-sonnet-4"
}
```

## Custom Model Pricing

HolmesGPT reports per-call LLM cost in its usage events. The cost number comes from LiteLLM's bundled cost map. For first-party names (`gpt-5`, `claude-opus-4-5-20251101`) and standard Bedrock IDs LiteLLM already has prices, so the cost field is populated automatically. Robusta-hosted models also work without configuration: Holmes looks up pricing for the *real* upstream model name (e.g. `bedrock/us.anthropic.claude-opus-4-6-v1`) in LiteLLM's bundled map and registers it under the internal routing name automatically.

You only need to add per-token pricing yourself if you're pointing Holmes at a model LiteLLM doesn't recognise — an internal OpenAI-compatible endpoint, a private-preview model, or a fork. In that case, add `input_cost_per_token` and `output_cost_per_token` (and optionally Anthropic cache pricing) to the model's entry:

```yaml
my-internal-opus:
    model: openai/opus-4.6
    api_base: https://llm.internal.example.com/v1
    api_key: "{{ env.INTERNAL_LLM_KEY }}"
    input_cost_per_token: 0.000003
    output_cost_per_token: 0.000015
    # Optional Anthropic prompt-cache pricing
    cache_creation_input_token_cost: 0.00000375
    cache_read_input_token_cost: 0.0000003
```

Values are USD per token. Both `input_cost_per_token` and `output_cost_per_token` must be set — configuring only one is ignored. User-configured pricing always wins over the auto-lookup.

If Holmes can't find pricing through any mechanism, it logs one `INFO` line at startup naming the model so you know its usage-event costs will be `0`.

## See Also

- [Environment Variables Reference](https://holmesgpt.dev/reference/environment-variables/)
- [Helm Configuration](https://holmesgpt.dev/reference/helm-configuration/)
- Individual provider documentation for specific configuration details
