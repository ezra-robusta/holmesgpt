# Notion

--8<-- "_shared/toolsets/notion.md"

## Timeout Configuration

By default, the Notion toolset uses a 5-second timeout for webpage requests. If you need to increase the timeout for slower Notion API responses, you can set the `INTERNET_TOOLSET_TIMEOUT_SECONDS` environment variable:

=== "Holmes CLI"

    ```bash
    export INTERNET_TOOLSET_TIMEOUT_SECONDS=30
    ```

## Capabilities

--8<-- "snippets/toolset_capabilities_intro.md"

| Tool Name | Description |
|-----------|-------------|
| fetch_notion_webpage | Fetch a Notion webpage. Use this to fetch Notion runbooks if they are present before starting your investigation |
