# Ollama

--8<-- "_shared/ai-providers/ollama.md"

## Holmes Helm Chart

You'll need to deploy Ollama as a service in your cluster. The `OLLAMA_API_BASE` (or, for the OpenAI-compatible gateway, `OPENAI_API_BASE`) should point to your Ollama service endpoint, for example `http://ollama-service:11434`.

## Holmes CLI

You can also pass the model directly on the command line, or set it with the `MODEL` environment variable:

```bash
export OLLAMA_API_BASE="http://localhost:11434"
holmes ask "what pods are failing?" --model="ollama_chat/<your-ollama-model>"

# Or use MODEL environment variable instead of --model flag
export MODEL="ollama_chat/<your-ollama-model>"
holmes ask "what pods are failing?"
```

With the OpenAI-compatible gateway:

```bash
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_API_KEY="dummy-key"  # Required but can be any value
holmes ask "what pods are failing?" --model="openai/<your-ollama-model>"

# Or use MODEL environment variable instead of --model flag
export MODEL="openai/<your-ollama-model>"
holmes ask "what pods are failing?"
```
