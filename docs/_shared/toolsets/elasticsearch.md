By enabling these toolsets, HolmesGPT can query Elasticsearch and OpenSearch clusters to investigate issues, search logs, analyze cluster health, and more.

These toolsets work with both **Elasticsearch** (including Elastic Cloud) and **OpenSearch** since they share the same REST API.

## Two Toolsets

HolmesGPT provides two separate Elasticsearch toolsets with different permission requirements:

| Toolset | Description | Permissions Required |
|---------|-------------|---------------------|
| `elasticsearch/data` | Search logs, metrics, and documents | Index-level read access |
| `elasticsearch/cluster` | Troubleshoot cluster health issues | Cluster-level monitor access |

Enable only the toolset(s) you need. Most users who just want to search logs only need `elasticsearch/data`.

## Configuration

```holmes-config
secrets:
  ELASTICSEARCH_API_KEY:
    description: Elasticsearch API key
    example: your-api-key
toolsets:
  elasticsearch/data:
    enabled: true
    config:
      api_url: "https://your-cluster.es.cloud.io:443"
      api_key: "{{ env.ELASTICSEARCH_API_KEY }}"
      # Alternative: use basic auth instead of api_key
      # username: "{{ env.ELASTICSEARCH_USERNAME }}"
      # password: "{{ env.ELASTICSEARCH_PASSWORD }}"
  elasticsearch/cluster:
    enabled: true
    config:
      api_url: "https://your-cluster.es.cloud.io:443"
      api_key: "{{ env.ELASTICSEARCH_API_KEY }}"
      # Alternative: use basic auth instead of api_key
      # username: "{{ env.ELASTICSEARCH_USERNAME }}"
      # password: "{{ env.ELASTICSEARCH_PASSWORD }}"
```

> **Enable only what you need**
>
> You can enable just `elasticsearch/data` or `elasticsearch/cluster` depending on your needs. Most users who just want to search logs only need `elasticsearch/data`.

## Authentication

The toolsets support multiple authentication methods:

| Method | Config Fields | Description |
|--------|--------------|-------------|
| API Key | `api_key` | Recommended for Elastic Cloud |
| Basic Auth | `username`, `password` | Username and password |
| mTLS | `client_cert`, `client_key` | Client certificate authentication (e.g., OpenShift Jaeger operator) |
| None | - | For clusters without authentication |

### Other Options

| Option | Default | Description |
|--------|---------|-------------|
| `verify_ssl` | `true` | Verify SSL certificates. For custom CAs, use the global `CERTIFICATE` env var instead. |
| `timeout_seconds` | `10` | Request timeout in seconds |

## Example Queries

- "Search for ERROR logs in the application-logs index from the last hour"
- "What are the field mappings for the metrics index?"
- "List all indices starting with 'logs-'"
- "What is the cluster health status?"
- "Why are shards unassigned?"
- "Which nodes have high disk usage?"
- "Show me the shards for the logs-* indices"

## OpenSearch Compatibility

These toolsets are fully compatible with OpenSearch clusters. Simply point the `api_url` to your OpenSearch endpoint:

```yaml
toolsets:
  elasticsearch/data:
    enabled: true
    config:
      api_url: "https://your-opensearch-cluster:9200"
      username: "admin"
      password: "your-password"
      verify_ssl: true
```
