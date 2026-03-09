# Secret Management for ShipFlow

**Do NOT commit plaintext secrets to Git.** The `secret.yaml` template contains
placeholders only. Choose one of the approaches below for production.

## Option A: Bitnami Sealed Secrets

1. Install the Sealed Secrets controller in your cluster:
   ```bash
   helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
   helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system
   ```

2. Install `kubeseal` CLI locally.

3. Create a regular Secret, then seal it:
   ```bash
   kubectl create secret generic shipflow-secrets \
     --namespace shipflow \
     --from-literal=DATABASE_URL='postgresql+asyncpg://...' \
     --from-literal=REDIS_URL='redis://...' \
     --dry-run=client -o yaml \
     | kubeseal --format yaml > k8s/base/sealed-secret.yaml
   ```

4. Commit `sealed-secret.yaml` instead of `secret.yaml`.

## Option B: External Secrets Operator (ESO)

1. Install ESO:
   ```bash
   helm repo add external-secrets https://charts.external-secrets.io
   helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace
   ```

2. Configure a `SecretStore` pointing to your vault (AWS Secrets Manager,
   HashiCorp Vault, GCP Secret Manager, Azure Key Vault, etc.).

3. Create an `ExternalSecret` resource that references your secret store:
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: ExternalSecret
   metadata:
     name: shipflow-secrets
     namespace: shipflow
   spec:
     refreshInterval: 1h
     secretStoreRef:
       name: cluster-secret-store
       kind: ClusterSecretStore
     target:
       name: shipflow-secrets
     data:
       - secretKey: DATABASE_URL
         remoteRef:
           key: shipflow/production/DATABASE_URL
       # ... repeat for each key
   ```

4. ESO will sync secrets into Kubernetes automatically.
