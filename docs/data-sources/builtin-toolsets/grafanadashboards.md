# Grafana Dashboards

--8<-- "_shared/toolsets/grafanadashboards.md"

## Holmes CLI

To test, run:

```bash
holmes ask "Show me all dashboards tagged with 'kubernetes'"
```

## Multiple Instances

```multi-instance
toolset: grafana/dashboards
name: Grafana
config: |
  api_url: <your grafana url>
  api_key: <your grafana service account token>
```
