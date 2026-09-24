# Other

--8<-- "_shared/ai-providers/other.md"

## Holmes CLI

Without a model list, set the API key and token limits in the environment:

```bash
export NOVITA_API_KEY="your-novita-api-key"

# Override the default token limits with correct values
export OVERRIDE_MAX_CONTENT_SIZE=98304  # 98k context window
export OVERRIDE_MAX_OUTPUT_TOKEN=32768   # 32k max output
```

**Use the model:**

```bash
holmes ask "what pods are failing?" --model="novita/deepseek/deepseek-v3.1-terminus"
```

**Or pass the API key directly:**

```bash
OVERRIDE_MAX_CONTENT_SIZE=98304 OVERRIDE_MAX_OUTPUT_TOKEN=32768 \
holmes ask "what pods are failing?" \
  --model="novita/deepseek/deepseek-v3.1-terminus" \
  --api-key="your-novita-api-key"
```

## Holmes Helm Chart: API Key in Values

!!! warning
    This method stores the API key in plain text in your values file. Use Kubernetes Secrets for production environments.

```yaml
# values.yaml
additionalEnvVars:
  - name: NOVITA_API_KEY
    value: "your-novita-api-key"  # API key directly in values file

modelList:
  deepseek-terminus:
    model: novita/deepseek/deepseek-v3.1-terminus
    api_key: "{{ env.NOVITA_API_KEY }}"
    custom_args:
      max_context_size: 98304  # Override context window to 98k tokens
```
