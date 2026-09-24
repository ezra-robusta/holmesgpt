# OpenAI-Compatible Models

--8<-- "_shared/ai-providers/openai-compatible.md"

## Custom CA Certificate

If your endpoint uses a custom CA, pass the base64-encoded CA certificate.

**Holmes CLI:**

```bash
export CERTIFICATE="$(cat /path/to/ca.crt | base64)"
```

**Holmes Helm Chart:**

```yaml
# values.yaml
certificate: "LS0tLS1CRUdJTi..."
```
