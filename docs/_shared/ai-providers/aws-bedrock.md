Configure HolmesGPT to use AWS Bedrock foundation models.

## Setup

### Prerequisites

1. **Install boto3**: AWS Bedrock requires boto3 version 1.28.57 or higher:
   ```bash
   pip install "boto3>=1.28.57"
   ```

2. **AWS credentials**: Ensure you have AWS credentials configured with access to Bedrock models. See [AWS Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html).

## Configuration

```holmes-config
secrets:
  AWS_ACCESS_KEY_ID:
    description: AWS access key ID
    example: AKIA...
  AWS_SECRET_ACCESS_KEY:
    description: AWS secret access key
    example: your-secret-key
# Configure at least one model
models:
  bedrock-claude-sonnet-4:
    aws_access_key_id: "{{ env.AWS_ACCESS_KEY_ID }}"
    aws_secret_access_key: "{{ env.AWS_SECRET_ACCESS_KEY }}"
    aws_region_name: eu-south-2
    model: bedrock/eu.anthropic.claude-sonnet-4-20250514-v1:0
    temperature: 1
    thinking:
      budget_tokens: 10000
      type: enabled

  bedrock-claude-sonnet-4-1M-context:
    aws_access_key_id: "{{ env.AWS_ACCESS_KEY_ID }}"
    aws_secret_access_key: "{{ env.AWS_SECRET_ACCESS_KEY }}"
    aws_region_name: eu-south-2
    model: bedrock/eu.anthropic.claude-sonnet-4-20250514-v1:0
    temperature: 1
    thinking:
      budget_tokens: 10000
      type: enabled
    extra_headers:
      anthropic-beta: context-1m-2025-08-07
    custom_args:
      max_context_size: 1000000
default_model: bedrock-claude-sonnet-4
```

### Using Claude Sonnet with 1M Context Window

The `bedrock-claude-sonnet-4-1M-context` example above demonstrates how to enable the extended 1 million token context window for Claude Sonnet. This requires two configuration parameters:

**1. Beta Feature Header:**
```yaml
extra_headers:
  anthropic-beta: context-1m-2025-08-07
```
This enables Anthropic's beta 1M context window feature.

**2. Context Size Override:**
```yaml
custom_args:
  max_context_size: 1000000
```
This tells HolmesGPT the actual context window size (1M tokens) so it can properly manage conversation history.

> **Both Parameters Required**
>
> You must include **both** `extra_headers` and `custom_args` to use the 1M context window. The `extra_headers` enables the feature, while `custom_args.max_context_size` ensures HolmesGPT knows the correct window size.

### Using Bearer Token Authentication (IAM Identity Center)

If you're using AWS IAM Identity Center (SSO) with Bedrock, you can authenticate via bearer token instead of access/secret keys.

Set the environment variable:
```bash
export AWS_BEARER_TOKEN_BEDROCK="your-bearer-token"
```

Or use `api_key` in the `modelList` config:
```yaml
modelList:
  bedrock-claude-sonnet-4:
    api_key: "{{ env.AWS_BEARER_TOKEN_BEDROCK }}"
    aws_region_name: us-east-1
    model: bedrock/anthropic.claude-sonnet-4-20250514-v1:0
```

### Finding Your AWS Credentials

If the AWS CLI is already configured on your machine, you may be able to find the above values with:

```bash
cat ~/.aws/credentials ~/.aws/config
```

### Finding Available Models

To list models your account can access (replacing `us-east-1` with the relevant region):

```bash
aws bedrock list-foundation-models --region=us-east-1 | grep modelId
```

**Important**: Different models are available in different regions. For example, Claude Opus is only available in us-west-2.

### Model Name Examples
Be sure to replace `<your-bedrock-model>` with a model you have access to, such as `anthropic.claude-opus-4-1-20250805-v1:0` or `anthropic.claude-sonnet-4-20250514-v1:0`

## Setting Extra Headers
You can enable various beta features in AWS Bedrock by setting custom headers.

For example, to enable 1M context windows.

You can enable ``Extra Headers`` in both the CLI (via env vars) and the Helm charts options.

For the CLI:
```bash
export EXTRA_HEADERS="{\"anthropic-beta\": \"context-1m-2025-08-07\"}"
```

Or, for Helm:

    # values.yaml
    holmes:
      ...
      modelList:
        ...
        bedrock-claude-sonnet-4-1M-context:
          aws_access_key_id: "{{ env.AWS_ACCESS_KEY_ID }}"
          aws_secret_access_key: "{{ env.AWS_SECRET_ACCESS_KEY }}"
          aws_region_name: eu-south-2
          model: bedrock/eu.anthropic.claude-sonnet-4-20250514-v1:0
          temperature: 1
          thinking:
            budget_tokens: 10000
            type: enabled
          extra_headers:
            anthropic-beta: context-1m-2025-08-07

## Additional Resources

HolmesGPT uses the LiteLLM API to support AWS Bedrock provider. Refer to [LiteLLM Bedrock docs](https://litellm.vercel.app/docs/providers/bedrock) for more details.
