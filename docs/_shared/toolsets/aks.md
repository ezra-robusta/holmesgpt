> **Consider Azure MCP instead**
>
> Most users should start with the built-in [Kubernetes](https://holmesgpt.dev/data-sources/builtin-toolsets/kubernetes/) integration and the [Azure MCP](https://holmesgpt.dev/data-sources/builtin-toolsets/azure-mcp/) integration. Together, these provide broad access to Kubernetes resources and all Azure APIs including AKS. This standalone toolset is only needed if you require specific AKS CLI commands that aren't available through the MCP server.

By enabling this toolset, HolmesGPT will be able to interact with Azure Kubernetes Service clusters, providing Azure-specific troubleshooting capabilities and cluster management.

## Prerequisites

1. Azure CLI installed and configured
2. Appropriate Azure RBAC permissions for AKS clusters
3. Access to the target AKS cluster

## Configuration

```holmes-config
toolsets:
  aks/core:
    enabled: true
    config:
      subscription_id: "<your Azure subscription ID>" # Optional
      resource_group: "<your AKS resource group>" # Optional
      cluster_name: "<your AKS cluster name>" # Optional
```

## Advanced Configuration

You can configure additional Azure settings:

```yaml
toolsets:
  aks/core:
    enabled: true
    config:
      subscription_id: "<your Azure subscription ID>"
      resource_group: "<your AKS resource group>"
      cluster_name: "<your AKS cluster name>"
      location: "eastus"  # Azure region
      timeout: 60  # Request timeout in seconds
```

## Capabilities

| Tool Name | Description |
|-----------|-------------|
| aks_get_cluster_info | Get detailed information about the AKS cluster |
| aks_get_node_pools | List and describe AKS node pools |
| aks_get_cluster_credentials | Get cluster credentials for kubectl access |
| aks_scale_node_pool | Scale a specific node pool |
| aks_get_cluster_logs | Fetch AKS cluster logs |
| aks_get_addon_status | Get status of AKS addons |
