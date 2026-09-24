# Loki

--8<-- "_shared/toolsets/grafanaloki.md"

--8<-- "snippets/toolsets_that_provide_logging.md"

## Multiple Instances

```multi-instance
toolset: grafana/loki
name: Grafana Loki
config: |
  api_url: http://grafana.monitoring.svc.cluster.local
  api_key: <your grafana API key>
  grafana_datasource_uid: <the UID of the Loki datasource>
```
