# Datadog

--8<-- "_shared/toolsets/datadog.md"

## Holmes CLI: Reusing the Configuration

The config file can define the shared settings once with a YAML anchor:

```yaml
# anchors: is ignored by Holmes — use it to define reusable YAML blocks
anchors:
  dd_config: &dd_config
    api_key: "{{ env.DATADOG_API_KEY }}"
    app_key: "{{ env.DATADOG_APP_KEY }}"
    api_url: https://api.datadoghq.com  # Change for EU/other regions
toolsets:
  datadog/general:
    enabled: true
    config: *dd_config
  datadog/logs:
    enabled: true
    config: *dd_config
  datadog/metrics:
    enabled: true
    config: *dd_config
  datadog/traces:
    enabled: true
    config: *dd_config
```

## Multiple Instances

```multi-instance
toolset: datadog/logs
name: Datadog
config: |
  api_key: "{{ env.DATADOG_API_KEY }}"
  app_key: "{{ env.DATADOG_APP_KEY }}"
  api_url: https://api.datadoghq.com
```
