# Kafka

--8<-- "_shared/toolsets/kafka.md"

## mTLS — certificate files (Kubernetes mounted secrets)

Use this approach when certificates are mounted into the Holmes pod as Kubernetes secrets.

=== "Holmes CLI"

    ```yaml
    toolsets:
        kafka/admin:
            enabled: true
            config:
                clusters:
                    - name: prod-kafka
                      broker: kafka.prod.example.com:9093
                      security_protocol: SSL
                      ssl_ca_cert_path: /etc/kafka-tls/ca.crt
                      ssl_client_cert_path: /etc/kafka-tls/client.pem
                      ssl_client_key_path: /etc/kafka-tls/client.key
    ```

    For SASL+TLS (`SASL_SSL`) combine both sets of fields:

    ```yaml
    toolsets:
        kafka/admin:
            enabled: true
            config:
                clusters:
                    - name: prod-kafka
                      broker: kafka.prod.example.com:9093
                      security_protocol: SASL_SSL
                      sasl_mechanism: SCRAM-SHA-512
                      username: "{{ env.KAFKA_USERNAME }}"
                      password: "{{ env.KAFKA_PASSWORD }}"
                      ssl_ca_cert_path: /etc/kafka-tls/ca.crt
                      ssl_client_cert_path: /etc/kafka-tls/client.pem
                      ssl_client_key_path: /etc/kafka-tls/client.key
    ```

=== "Holmes Helm Chart"

    Create a Kubernetes secret containing the certificate files:

    ```bash
    kubectl create secret generic kafka-tls-certs \
      --from-file=ca.crt=/path/to/ca.crt \
      --from-file=client.pem=/path/to/client.pem \
      --from-file=client.key=/path/to/client.key
    ```

    --8<-- "snippets/secret_namespace_note.md"

    Then mount the secret and reference the paths in your Helm values:

    ```yaml
    additionalVolumes:
      - name: kafka-tls
        secret:
          secretName: kafka-tls-certs

    additionalVolumeMounts:
      - name: kafka-tls
        mountPath: /etc/kafka-tls
        readOnly: true

    toolsets:
      kafka/admin:
        enabled: true
        config:
          clusters:
            - name: prod-kafka
              broker: kafka.prod.example.com:9093
              security_protocol: SSL
              ssl_ca_cert_path: /etc/kafka-tls/ca.crt
              ssl_client_cert_path: /etc/kafka-tls/client.pem
              ssl_client_key_path: /etc/kafka-tls/client.key
    ```

    For SASL+TLS (`SASL_SSL`) add SASL credentials alongside the cert paths:

    ```yaml
    additionalEnvVars:
      - name: KAFKA_USERNAME
        valueFrom:
          secretKeyRef:
            name: kafka-credentials
            key: kafka-username
      - name: KAFKA_PASSWORD
        valueFrom:
          secretKeyRef:
            name: kafka-credentials
            key: kafka-password

    additionalVolumes:
      - name: kafka-tls
        secret:
          secretName: kafka-tls-certs

    additionalVolumeMounts:
      - name: kafka-tls
        mountPath: /etc/kafka-tls
        readOnly: true

    toolsets:
      kafka/admin:
        enabled: true
        config:
          clusters:
            - name: prod-kafka
              broker: kafka.prod.example.com:9093
              security_protocol: SASL_SSL
              sasl_mechanism: SCRAM-SHA-512
              username: "{{ env.KAFKA_USERNAME }}"
              password: "{{ env.KAFKA_PASSWORD }}"
              ssl_ca_cert_path: /etc/kafka-tls/ca.crt
              ssl_client_cert_path: /etc/kafka-tls/client.pem
              ssl_client_key_path: /etc/kafka-tls/client.key
    ```

    Apply the configuration:

    ```bash
    helm upgrade holmesgpt robusta/holmes -f values.yaml
    ```

## Capabilities

--8<-- "snippets/toolset_capabilities_intro.md"

| Tool Name | Description |
|-----------|-------------|
| kafka_list_topics | List all Kafka topics |
| kafka_describe_topic | Get detailed information about a specific topic |
| kafka_list_consumers | List all consumer groups |
| kafka_describe_consumer | Get detailed information about a consumer group |
| kafka_consumer_lag | Check consumer lag for a consumer group |
