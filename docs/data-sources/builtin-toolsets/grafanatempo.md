# Tempo

--8<-- "_shared/toolsets/grafanatempo.md"

## Holmes CLI

To test, run:

```bash
holmes ask "The payments DB is very slow, check tempo for any trace data"
```

## Multiple Instances

```multi-instance
toolset: grafana/tempo
name: Grafana Tempo
config: |
  api_url: <your grafana url>
  api_key: <your grafana service account token>
  grafana_datasource_uid: <the UID of the Tempo datasource>
```
