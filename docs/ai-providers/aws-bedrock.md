# AWS Bedrock

--8<-- "_shared/ai-providers/aws-bedrock.md"

## Holmes CLI

You can also set the credentials in the environment and pass the Bedrock model directly:

```bash
export AWS_REGION_NAME="us-east-1"  # Replace with your region
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

holmes ask "what pods are failing?" --model="bedrock/<your-bedrock-model>"
```

**For Claude Sonnet with 1M context window:**

```bash
export AWS_REGION_NAME="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export EXTRA_HEADERS="{\"anthropic-beta\": \"context-1m-2025-08-07\"}"
export OVERRIDE_MAX_CONTENT_SIZE="1000000"

holmes ask "what pods are failing?" --model="bedrock/eu.anthropic.claude-sonnet-4-20250514-v1:0"
```

Without a model list, the CLI takes extra headers from the `EXTRA_HEADERS` environment variable:

```bash
export EXTRA_HEADERS="{\"anthropic-beta\": \"context-1m-2025-08-07\"}"
```

## Using IRSA (IAM Roles for Service Accounts)

If you're running HolmesGPT on Kubernetes with IRSA, you can authenticate without static credentials. The AWS SDK picks up the role automatically when the pod's service account is annotated with the role ARN and the following environment variables are injected into the pod:

| Variable | Description |
|---|---|
| `AWS_ROLE_ARN` | ARN of the IAM role to assume |
| `AWS_WEB_IDENTITY_TOKEN_FILE` | Path to the projected service account token |

=== "Holmes Helm Chart"

    **Configure Helm Values:**
    ```yaml
    # values.yaml
    serviceAccount:
      annotations:
        eks.amazonaws.com/role-arn: "arn:aws:iam::<account-id>:role/<role-name>"

    # Configure at least one model using modelList (no credentials needed)
    modelList:
      bedrock-claude-sonnet-4:
        aws_region_name: eu-west-3
        model: bedrock/eu.anthropic.claude-sonnet-4-20250514-v1:0
        temperature: 1
        thinking:
          budget_tokens: 10000
          type: enabled

    # Optional: Set default model (use modelList key name)
    config:
      model: "bedrock-claude-sonnet-4"
    ```


**Note:** With IRSA, you do not need `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`. The AWS SDK picks up the injected token automatically.
