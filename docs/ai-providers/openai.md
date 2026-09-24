# OpenAI

--8<-- "_shared/ai-providers/openai.md"

## Holmes CLI

**Using Environment Variables:**

```bash
export OPENAI_API_KEY="your-openai-api-key"
holmes ask "what pods are failing?"
```

**Using Command Line Parameters:**

You can also pass the API key directly as a command-line parameter:

```bash
holmes ask "what pods are failing?" --api-key="your-api-key"
```

**GPT-5 reasoning effort from the environment:**

```bash
# Use minimal reasoning effort for faster responses
export REASONING_EFFORT="minimal"
holmes ask "what pods are failing?" --model="gpt-5"

# Use default reasoning effort
export REASONING_EFFORT="medium"
holmes ask "what pods are failing?" --model="gpt-5"

# Use high reasoning effort for complex investigations
export REASONING_EFFORT="high"
holmes ask "what pods are failing?" --model="gpt-5"
```
