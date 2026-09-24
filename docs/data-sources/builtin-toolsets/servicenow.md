# ServiceNow

--8<-- "_shared/toolsets/servicenow.md"

## Holmes CLI

To test, run:

```bash
holmes ask "Show me all change requests from the last 24 hours"
```

## Multiple Instances

```multi-instance
toolset: servicenow/tables
name: ServiceNow
config: |
  api_url: <your servicenow instance URL>
  api_key: <your servicenow API key>
```
