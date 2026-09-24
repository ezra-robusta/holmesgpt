# Azure AI Foundry

--8<-- "_shared/ai-providers/azure-ai-foundry.md"

## Holmes CLI

You can also set the endpoint in the environment and pass the model directly.

**Anthropic models (recommended):**

```bash
export AZURE_API_KEY="your-azure-api-key"
export AZURE_API_BASE="https://XXXX.services.ai.azure.com/anthropic"

holmes ask "what pods are failing?" --model="anthropic/claude-opus-4-7"
```

**Azure OpenAI deployments:**

```bash
export AZURE_API_KEY="your-azure-api-key"
export AZURE_API_BASE="https://YYYY.cognitiveservices.azure.com/"
export AZURE_API_VERSION="2025-04-01-preview"

holmes ask "what pods are failing?" --model="azure/<your-deployment-name>"
```

## Running in Kubernetes with Workload Identity

When running as a pod in AKS, use [AKS Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview){:target="_blank"} so the pod authenticates via a federated credential rather than a stored secret. The managed identity (or service principal) bound to the pod must have the **Cognitive Services OpenAI User** role on the target resource.

=== "Holmes Helm Chart"

    **Prerequisites:**

    - AKS cluster with OIDC issuer and workload identity enabled
    - A managed identity with the **Cognitive Services OpenAI User** role on your Azure AI Foundry resource
    - A federated credential linking the managed identity to the Holmes ServiceAccount

    **Set up the identity and federation:**

    ```bash
    # Get the OIDC issuer URL
    OIDC_ISSUER=$(az aks show -n <cluster> -g <rg> --query "oidcIssuerProfile.issuerUrl" -o tsv)

    # Create a managed identity
    az identity create -n holmes-identity -g <rg>
    IDENTITY_CLIENT_ID=$(az identity show -n holmes-identity -g <rg> --query clientId -o tsv)
    IDENTITY_PRINCIPAL_ID=$(az identity show -n holmes-identity -g <rg> --query principalId -o tsv)

    # Assign the Cognitive Services OpenAI User role
    az role assignment create \
      --assignee "$IDENTITY_PRINCIPAL_ID" \
      --role "Cognitive Services OpenAI User" \
      --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<resource>"

    # Create a federated credential for the Holmes ServiceAccount
    az identity federated-credential create \
      --name holmes-federated \
      --identity-name holmes-identity \
      --resource-group <rg> \
      --issuer "$OIDC_ISSUER" \
      --subject "system:serviceaccount:<namespace>:holmes" \
      --audiences "api://AzureADTokenExchange"
    ```

    **Configure Helm Values:**

    ```yaml
    # values.yaml
    additionalEnvVars:
      - name: AZURE_AD_TOKEN_AUTH
        value: "true"
      - name: AZURE_CLIENT_ID
        value: "<managed-identity-client-id>"
      - name: AZURE_TENANT_ID
        value: "<tenant-id>"

    serviceAccount:
      annotations:
        azure.workload.identity/client-id: "<managed-identity-client-id>"

    podLabels:
      azure.workload.identity/use: "true"

    modelList:
      # Anthropic model on Azure AI Foundry (recommended)
      azure-opus-4-7:
        model: anthropic/claude-opus-4-7
        api_base: https://XXXX.services.ai.azure.com/anthropic
        temperature: 1

      # Azure OpenAI-style deployment (e.g. GPT-5.4)
      azure-gpt-5-4:
        model: azure/my-gpt-5.4-deployment
        api_base: https://YYYY.cognitiveservices.azure.com/
        api_version: "2025-04-01-preview"

    config:
      model: "azure-opus-4-7"
    ```

    Note that `api_key` is omitted from the `modelList` entries — authentication is handled entirely by the workload identity token.

### Troubleshooting

```bash
# Verify the pod has workload identity labels and env vars injected
kubectl describe pod -l app=holmes -n <namespace> | grep -A5 "AZURE_"

# Test that the identity can obtain a token (from inside the pod)
kubectl exec -n <namespace> deploy/holmes -- python -c "
from azure.identity import DefaultAzureCredential
token = DefaultAzureCredential().get_token('https://cognitiveservices.azure.com/.default')
print('Token obtained, expires at:', token.expires_on)
"

# Check role assignment
az role assignment list \
  --assignee "<identity-principal-id>" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<resource>" \
  --output table
```
