!!! note "Namespace must match Holmes' deployment"
    Create the secret in the namespace where Holmes runs; run the `kubectl` and `helm` commands in the same namespace, adding the same `-n <namespace>` to each if it is not your current one. If a secret or key that `secretKeyRef` names is missing from that namespace, the Holmes pod does not start and reports `CreateContainerConfigError`.
