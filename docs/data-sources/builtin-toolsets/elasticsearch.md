# Elasticsearch / OpenSearch

--8<-- "_shared/toolsets/elasticsearch.md"

## Multiple Instances

```multi-instance
toolset: elasticsearch/data
name: Elasticsearch
config: |
  api_url: "https://your-cluster.es.cloud.io:443"
  api_key: "your-api-key"
```

## mTLS (Mutual TLS)

For Elasticsearch clusters that require client certificate authentication (common with the OpenShift Jaeger operator), configure the certificate paths:

=== "Holmes CLI"

    ```yaml
    toolsets:
      elasticsearch/data:
        enabled: true
        config:
          api_url: "https://elasticsearch.jaeger.svc:9200"
          client_cert: "/path/to/client.crt"
          client_key: "/path/to/client.key"
    ```

=== "Holmes Helm Chart"

    Create a Kubernetes secret containing the client certificates:

    ```bash
    kubectl create secret generic elasticsearch-client-certs \
      --from-file=tls.crt=/path/to/client.crt \
      --from-file=tls.key=/path/to/client.key
    ```

    --8<-- "snippets/secret_namespace_note.md"

    Then mount the secret into the Holmes container using `additionalVolumes` and `additionalVolumeMounts`:

    ```yaml
    additionalEnvVars:
      - name: ELASTICSEARCH_URL
        value: "https://elasticsearch.jaeger.svc:9200"

    additionalVolumes:
      - name: es-certs
        secret:
          secretName: elasticsearch-client-certs

    additionalVolumeMounts:
      - name: es-certs
        mountPath: /etc/elasticsearch/certs
        readOnly: true

    toolsets:
      elasticsearch/data:
        enabled: true
        config:
          api_url: "{{ env.ELASTICSEARCH_URL }}"
          client_cert: "/etc/elasticsearch/certs/tls.crt"
          client_key: "/etc/elasticsearch/certs/tls.key"
    ```


If Elasticsearch uses a private CA, use the global [`certificate`](../../reference/helm-configuration.md) Helm value (or `CERTIFICATE` env var for CLI) to trust it. This applies to all outbound HTTPS requests, not just Elasticsearch. See [Environment Variables](../../reference/environment-variables.md#certificate) for details.

## Tools

--8<-- "snippets/toolset_capabilities_intro.md"

| Toolset | Tool Name | Description |
|---------|-----------|-------------|
| `elasticsearch/data` | elasticsearch_search | Search documents using Elasticsearch Query DSL |
| `elasticsearch/data` | elasticsearch_mappings | Get field mappings for an index |
| `elasticsearch/data` | elasticsearch_list_indices | List indices matching a pattern |
| `elasticsearch/cluster` | elasticsearch_cat | Query _cat APIs (indices, shards, nodes, etc.) |
| `elasticsearch/cluster` | elasticsearch_cluster_health | Get cluster health status |
| `elasticsearch/cluster` | elasticsearch_allocation_explain | Explain shard allocation decisions |
| `elasticsearch/cluster` | elasticsearch_nodes_stats | Get node-level statistics |
| `elasticsearch/cluster` | elasticsearch_index_stats | Get statistics for an index |
