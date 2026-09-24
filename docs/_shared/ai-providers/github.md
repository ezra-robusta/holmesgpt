Configure HolmesGPT to use [GitHub Models](https://github.com/marketplace/models).

## Setup

Create a [GitHub Personal Access Token](https://github.com/settings/tokens) (fine-grained) with the **Models** permission ([screenshot](https://github.com/HolmesGPT/holmesgpt/blob/master/docs/assets/github-models-pat-permissions.png)).

Browse the full list of available models at [github.com/marketplace/models](https://github.com/marketplace/models).

> **Verify model availability before configuring**
>
> Some models are listed in the GitHub Models catalog but are not actually available for your account. Before configuring a model in HolmesGPT, open the model's page in the [GitHub Models playground](https://github.com/marketplace/models), send it any message (e.g. "hello"), and verify you get a response. If the model doesn't respond, it won't work with HolmesGPT either.

## Configuration

```holmes-config
secrets:
  GITHUB_API_KEY:
    description: GitHub personal access token with the Models permission
    example: your-github-token
secret_name: github-models-credentials
models:
  gpt-4-1:
    api_key: "{{ env.GITHUB_API_KEY }}"
    model: github/gpt-4.1
    temperature: 0
default_model: gpt-4-1
```

> **Model Naming**
>
> Use `github/` prefix followed by the model name, dropping the company prefix. For example, `openai/gpt-4.1` in the catalog becomes `github/gpt-4.1`.

## Additional Resources

- [GitHub Models Catalog](https://github.com/marketplace/models) - browse all available models
- [LiteLLM GitHub provider docs](https://docs.litellm.ai/docs/providers/github)
