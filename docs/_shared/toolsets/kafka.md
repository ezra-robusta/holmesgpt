By enabling this toolset, HolmesGPT will be able to fetch metadata from Kafka. This provides Holmes the ability to introspect into Kafka by listing consumers and topics or finding lagging consumer groups.

This toolset uses the AdminClient of the [confluent-kafka python library](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#pythonclient-adminclient). Kafka's [Java API](https://docs.confluent.io/platform/current/installation/configuration/admin-configs.html) is also a good source of documentation.

## Configuration

### SASL authentication

```holmes-config
secrets:
  KAFKA_USERNAME:
    description: Kafka username
    example: kafka-plaintext-user
  KAFKA_PASSWORD:
    description: Kafka password
    example: <your-password>
secret_name: kafka-credentials
toolsets:
  kafka/admin:
    enabled: true
    config:
      clusters:
        - name: prod-kafka
          broker: kafka.prod.example.com:9095
          username: "{{ env.KAFKA_USERNAME }}"
          password: "{{ env.KAFKA_PASSWORD }}"
          sasl_mechanism: SCRAM-SHA-512
          security_protocol: SASL_PLAINTEXT
```

### mTLS — base64-encoded inline certificates

Use this approach when certificates are passed as environment variables (e.g., from a secret manager or Kubernetes secret).

```holmes-config
secrets:
  KAFKA_CA_CERT_BASE64:
    description: Base64-encoded CA certificate
    example: $(base64 < /path/to/ca.crt | tr -d '\n')
  KAFKA_CLIENT_CERT_BASE64:
    description: Base64-encoded client certificate
    example: $(base64 < /path/to/client.pem | tr -d '\n')
  KAFKA_CLIENT_KEY_BASE64:
    description: Base64-encoded client key
    example: $(base64 < /path/to/client.key | tr -d '\n')
secret_name: kafka-tls-certs
toolsets:
  kafka/admin:
    enabled: true
    config:
      clusters:
        - name: prod-kafka
          broker: kafka.prod.example.com:9093
          security_protocol: SSL
          ssl_ca_cert: "{{ env.KAFKA_CA_CERT_BASE64 }}"
          ssl_client_cert: "{{ env.KAFKA_CLIENT_CERT_BASE64 }}"
          ssl_client_key: "{{ env.KAFKA_CLIENT_KEY_BASE64 }}"
```

## Configuration fields

Below is a description of the configuration fields for each cluster entry:

| Config key | Required | Description |
|---|---|---|
| `name` | Yes | Unique name for this cluster. Holmes uses it to decide which cluster to query. |
| `broker` | Yes | Comma-separated list of `host:port` pairs for the initial broker connection. |
| `security_protocol` | No | Security protocol: `PLAINTEXT`, `SSL`, `SASL_PLAINTEXT`, or `SASL_SSL`. |
| `sasl_mechanism` | No | SASL mechanism: `PLAIN`, `SCRAM-SHA-256`, or `SCRAM-SHA-512`. |
| `username` | No | Username for SASL authentication. |
| `password` | No | Password for SASL authentication. |
| `client_id` | No | Kafka client ID (default: `holmes-kafka-client`). |
| `ssl_ca_cert_path` | No | Path to the CA certificate file (PEM). Use when certs are mounted as Kubernetes secrets. |
| `ssl_client_cert_path` | No | Path to the client certificate file (PEM) for mTLS. |
| `ssl_client_key_path` | No | Path to the client private key file (PEM) for mTLS. |
| `ssl_ca_cert` | No | Base64-encoded CA certificate (PEM). Alternative to `ssl_ca_cert_path`. |
| `ssl_client_cert` | No | Base64-encoded client certificate (PEM) for mTLS. Alternative to `ssl_client_cert_path`. |
| `ssl_client_key` | No | Base64-encoded client private key (PEM) for mTLS. Alternative to `ssl_client_key_path`. |

When both a path field and its inline base64 counterpart are set, the path field takes precedence.
