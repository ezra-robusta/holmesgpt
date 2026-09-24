Notion Integration for HolmesGPT

Enabling this toolset allows HolmesGPT to fetch pages from Notion, making it useful when providing Notion-based runbooks.

## Setup Instructions

1. **Create a Webhook Integration**

    - Go to the Notion Developer Portal.
    - Create a new integration with **read content** capabilities.

2. **Grant Access to Pages**

    - Open the desired Notion page.
    - Click the three dots in the top right.
    - Select **Connections** and add your integration.

3. **Configure Authentication**

    - Retrieve the **Internal Integration Secret** from Notion.
    - Keep it: the configuration below reads it from the `NOTION_AUTH` environment variable.

## Configuration

```holmes-config
secrets:
  NOTION_AUTH:
    description: Notion internal integration secret
    example: <your Notion integration secret>
secret_name: notion-credentials
toolsets:
  notion:
    enabled: true
    config:
      additional_headers:
        Authorization: Bearer {{ env.NOTION_AUTH }}
```
