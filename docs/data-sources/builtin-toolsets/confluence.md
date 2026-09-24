# Confluence

--8<-- "_shared/toolsets/confluence.md"

## Holmes CLI

To test, run:

```bash
holmes ask "search Confluence for runbooks about database issues"
```

## Multiple Instances

```multi-instance
toolset: confluence
name: Confluence
config: |
  api_url: "https://yourcompany.atlassian.net"
  user: "your-email@example.com"
  api_key: "your-api-token"
```

## Tools

--8<-- "snippets/toolset_capabilities_intro.md"

| Tool Name | Description |
|-----------|-------------|
| confluence_request | Make HTTP GET requests to the Confluence REST API. Supports fetching pages, searching with CQL, listing spaces, and retrieving child pages or comments. |
