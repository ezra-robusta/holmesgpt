HolmesGPT supports all AI providers available through [LiteLLM](https://litellm.vercel.app/docs/providers), including 100+ different LLM providers. This guide shows how to configure any LiteLLM-supported provider using DeepSeek via Novita as an example.

## Example: DeepSeek 3.1 Terminus via Novita

Let's walk through setting up DeepSeek 3.1 Terminus using the Novita AI provider.

### Step 1: Check LiteLLM Documentation

First, visit the [LiteLLM Novita documentation](https://litellm.vercel.app/docs/providers/novita) to understand the provider requirements:

- Model naming format: `novita/<model-name>`
- Required environment variable: `NOVITA_API_KEY`

### Step 2: Get Your API Key

Sign up at [Novita AI](https://novita.ai) to obtain your API key.

### Step 3: Configure HolmesGPT

> **Model Not in LiteLLM Registry**
>
> Since DeepSeek 3.1 Terminus via Novita isn't in LiteLLM's model registry, you'll see warnings about using default token limits (200K input, 4k output). To fix this, set the correct values based on the model's actual capabilities when run via Novita:
>
> - **Context window**: 98,304 tokens
> - **Max output**: 32,768 tokens

```holmes-config
secrets:
  NOVITA_API_KEY:
    description: Novita API key
    example: your-novita-api-key
models:
  deepseek-terminus:
    model: novita/deepseek/deepseek-v3.1-terminus
    api_key: "{{ env.NOVITA_API_KEY }}"
    custom_args:
      max_context_size: 98304  # Override context window to 98k tokens
```

## General Model Configuration Parameters

When configuring models in `modelList`, you can use these parameters:

**Core Parameters:**
```yaml
modelList:
  my-model:
    # Required: LiteLLM model identifier
    model: "provider/model-name"

    # Optional: Authentication
    api_key: "{{ env.API_KEY }}"  # Supports environment variables

    # Optional: Custom endpoints
    api_base: "https://custom-endpoint.example.com/v1"  # Custom API URL
    api_version: "2024-01-01"  # API version (e.g., for Azure)
```

**Advanced Parameters:**
```yaml
modelList:
  advanced-model:
    model: "provider/model-name"
    api_key: "{{ env.API_KEY }}"

    # GPT-5 specific
    reasoning_effort: "medium"  # Options: minimal, low, medium, high

    # Thinking mode (experimental, model-specific)
    thinking: true  # Enable thinking mode if supported by the model

    # Override context window size for any model
    custom_args:
      max_context_size: 1000000  # Override the model's context window
```

> **Context Window Override**
>
> The `custom_args.max_context_size` parameter can be used with **any model** to override its default context window size. This is particularly useful when the model's actual context window is different from what LiteLLM reports.
>
> This parameter takes precedence over the `OVERRIDE_MAX_CONTENT_SIZE` environment variable, giving you per-model control when using modelList configuration.
>
> Example: If your model isn't recognized by LiteLLM and defaults to 200k tokens, but it actually supports 1M tokens:
> ```yaml
> modelList:
>   my-model:
>     model: provider/model-name
>     api_key: "{{ env.API_KEY }}"
>     custom_args:
>       max_context_size: 1000000  # Override to 1M tokens
> ```

> **Parameter Passthrough**
>
> Any additional parameters not listed here (like `temperature`, `max_tokens`, etc.) are passed directly to the LiteLLM completion API. Refer to your provider's documentation for supported parameters.

## Finding Other Providers

To use any other LiteLLM-supported provider, follow the same pattern:

1. Check the provider's page in [LiteLLM documentation](https://litellm.vercel.app/docs/providers)
2. Note the required environment variables and model naming format
3. Configure using the same structure shown above

## Additional Resources

- **LiteLLM Providers:** Full list at [LiteLLM Providers](https://litellm.vercel.app/docs/providers)
