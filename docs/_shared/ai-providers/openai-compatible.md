HolmesGPT works with **any OpenAI-compatible API endpoint**. This includes [**LiteLLM Proxy**](https://docs.litellm.ai/docs/simple_proxy), other API gateways and proxy servers, and local inference servers — as long as they expose an OpenAI-compatible interface with function calling support.

> **Using LiteLLM Proxy (or another proxy)?**
>
> This is the right page. Configure your proxy's URL as `OPENAI_API_BASE`, the proxy token as `OPENAI_API_KEY`, and set `model: openai/<name-your-proxy-exposes>` in `modelList`. See the example below.

> **Function Calling Required**
>
> Your model and inference server must support function calling (tool calling). Models that lack this capability may produce incorrect results.

## Quick Start

Point HolmesGPT at your OpenAI-compatible endpoint:

- Set `OPENAI_API_BASE` to your endpoint URL
- Set `OPENAI_API_KEY` to your endpoint's API key, or any placeholder value like `"none"` if your endpoint doesn't require authentication (this parameter is always required by LiteLLM)
- Use `openai/<model-name>` format for the model parameter, where `<model-name>` matches what your endpoint expects
- Optional: Set `CERTIFICATE` to a base64-encoded CA certificate if your endpoint uses a custom CA

```holmes-config
secrets:
  OPENAI_API_BASE:
    description: URL of your OpenAI-compatible endpoint
    example: http://localhost:8000/v1
  OPENAI_API_KEY:
    description: API key of your endpoint, or any placeholder if it doesn't need auth
    example: none
models:
  my-model:
    api_key: "{{ env.OPENAI_API_KEY }}"
    api_base: "{{ env.OPENAI_API_BASE }}"
    model: openai/your-model-name
    temperature: 1
default_model: my-model
```

## Known Limitations

- **Some models**: May hallucinate responses instead of reporting function calling limitations. See [benchmark results](https://holmesgpt.dev/development/evaluations/latest-results/) for recommended models.

## Additional Resources

HolmesGPT uses the LiteLLM API to support OpenAI-compatible providers. Refer to [LiteLLM OpenAI-compatible docs](https://litellm.vercel.app/docs/providers/openai_compatible) for more details.
