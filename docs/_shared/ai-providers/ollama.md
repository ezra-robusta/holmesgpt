Configure HolmesGPT to use local models with Ollama.

> **Warning**
>
> Ollama support is experimental and can be tricky to configure correctly. We recommend trying HolmesGPT with a hosted model first (like Claude or OpenAI) to ensure everything works before switching to Ollama. Tool-calling capabilities are limited and may produce inconsistent results. Only [LiteLLM supported Ollama models](https://docs.litellm.ai/docs/providers/ollama#ollama-models) work with HolmesGPT.

## Setup

1. Download Ollama from [ollama.com](https://ollama.com/)
2. Start Ollama: `ollama serve`
3. Download models: `ollama pull <model-name>`

## Configuration

```holmes-config
secrets:
  OLLAMA_API_BASE:
    description: URL of your Ollama server
    example: http://localhost:11434
secret_name: ollama-credentials
# Configure at least one model
models:
  ollama-llama3:
    api_base: "{{ env.OLLAMA_API_BASE }}"
    model: ollama_chat/llama3
    temperature: 1

  ollama-codellama:
    api_base: "{{ env.OLLAMA_API_BASE }}"
    model: ollama_chat/codellama
    temperature: 1
default_model: ollama-llama3
```

**Alternative (OpenAI-compatible gateway)**

If you hit compatibility issues with certain Ollama models via LiteLLM, you can use Ollama's OpenAI-compatible API endpoint:

```holmes-config
secrets:
  OPENAI_API_BASE:
    description: URL of Ollama's OpenAI-compatible endpoint
    example: http://localhost:11434/v1
  OPENAI_API_KEY:
    description: Bearer token, or any value if Ollama doesn't require one
    example: dummy-key
secret_name: ollama-openai-credentials
models:
  ollama-alt:
    api_base: "{{ env.OPENAI_API_BASE }}"
    api_key: "{{ env.OPENAI_API_KEY }}"
    model: openai/OLLAMA_MODEL_NAME
default_model: ollama-alt
```

## Additional Resources

HolmesGPT uses the LiteLLM API to support Ollama provider. Refer to [LiteLLM Ollama docs](https://docs.litellm.ai/docs/providers/ollama) for more details.
