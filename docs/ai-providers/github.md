# GitHub Models

--8<-- "_shared/ai-providers/github.md"

## Holmes CLI

You can also pass the model and token directly on the command line:

```bash
export GITHUB_API_KEY="your-github-token"
holmes ask "what pods are failing?" --model="github/gpt-4.1"
```

```bash
holmes ask "what pods are failing?" --model="github/gpt-4.1" --api-key="your-github-token"
```
