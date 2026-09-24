By enabling this toolset, HolmesGPT will be able to consult runbooks from Slab pages.

Retrieve your Slab [API token](https://help.slab.com/en/articles/6545629-developer-tools-api-webhooks) prior to configuring this toolset. Do note that Slab API is only available for Slab premium users. See [here](https://help.slab.com/en/articles/6545629-developer-tools-api-webhooks).

## Configuration

```holmes-config
secrets:
  SLAB_API_KEY:
    description: Slab API key
    example: <your Slab API key>
toolsets:
  slab:
    enabled: true
```

To test, run:

```bash
holmes ask "Why is my pod failing, if it's a crashloopbackoff use the runbooks from Slab"
```
