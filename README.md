# CloudCost Anomaly

Cross-cloud cost monitoring and anomaly detection for AWS, Azure, GCP, and OCI.

## Overview

CloudCost Anomaly pulls billing data from all major cloud providers (AWS, Azure, GCP, and OCI), normalizes the data into a common schema, builds statistical baselines per service, and sends real-time alerts when costs deviate beyond a configurable threshold (default: 30%).

## Features

- **Multi-provider support**: AWS Cost Explorer, Azure Cost Management, GCP Cloud Billing, OCI Cost Management
- **Unified schema**: Normalizes all provider data to a common CostEntry model
- **Statistical baselines**: Rolling averages per service for anomaly detection
- **Configurable thresholds**: Default 30% deviation, fully customizable
- **Multi-channel alerts**: Slack webhooks + SMTP email
- **Credential validation**: Test provider access before running detection

## Installation

```bash
pip install -e .
```

## Quick Start

1. Configure `config.yaml` with your cloud credentials
2. Validate credentials:
   ```bash
   cloudcost --validate
   ```
3. Run a one-time check:
   ```bash
   cloudcost --check
   ```
4. Start continuous monitoring:
   ```bash
   cloudcost
   ```

## Environment Variables

For production deployments, use environment variables instead of config.yaml:

### AWS
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_ACCOUNT_ID="123456789012"
```

### Azure
```bash
export AZURE_SUBSCRIPTION_ID="your-sub"
export AZURE_TENANT_ID="your-tenant"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-secret"
```

### GCP
```bash
export GCP_PROJECT_ID="your-project"
export GCP_CREDENTIALS_PATH="/path/to/service-account.json"
```

### OCI
```bash
export OCI_TENANCY_OCID="your-tenancy-ocid"
export OCI_USER_OCID="your-user-ocid"
export OCI_KEY_FINGERPRINT="your-key-fingerprint"
export OCI_PRIVATE_KEY_PATH="/path/to/oci_private_key.pem"
export OCI_COMPARTMENT_OCID="your-compartment-ocid"
```

### General
```bash
export ANOMALY_THRESHOLD_PCT="30"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--config PATH` | Path to YAML config file | `config.yaml` |
| `--check` | Run one-time check and exit | - |
| `--validate` | Validate provider credentials | - |
| `--history-days N` | Days of history for baseline | 30 |
| `--threshold PCT` | Override anomaly threshold | From config |

## OCI Configuration Details

To enable Oracle Cloud Infrastructure monitoring:

1. **Generate API Signing Key**:
   ```bash
   openssl genrsa -out oci_api_key.pem 2048
   openssl rsa -pubout -in oci_api_key.pem -out oci_api_key_public.pem
   ```

2. **Get Required OCIDs**:
   - Tenancy OCID: Profile → Tenancy: <your-tenancy-name>
   - User OCID: Profile → User Settings
   - Compartment OCID: Identity → Compartments

3. **Add Public Key to OCI**:
   - Go to Identity → Users → <your-user> → API Keys → Add Public Key
   - Paste contents of `oci_api_key_public.pem`

4. **Note the Fingerprint**:
   - The fingerprint is displayed in the API Keys section

5. **Add to config.yaml or environment variables**:
   ```yaml
   oci:
     tenant_ocid: "ocid1.tenancy.oc1..aaaaaaaaxxxxxxxxxxxxxxxxxxxxxxxx"
     user_ocid: "ocid1.user.oc1..aaaaaaaayyyyyyyyyyyyyyyyyyyyyyyy"
     fingerprint: "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
     private_key_path: "/path/to/oci_api_key.pem"
     compartment_ocid: "ocid1.compartment.oc1..aaaaaaaazzzzzzzzzzzzzzzzzzzzzzzz"
     region: "us-ashburn-1"
   ```

## Architecture

```
providers/
  aws.py          → AWS Cost Explorer API
  azure.py        → Azure Cost Management API  
  gcp.py          → GCP Cloud Billing API
  oci.py          → OCI Cost Management API
normalizer.py     → Maps provider data to CostEntry schema
detector.py       → Statistical baseline tracking & anomaly detection
dispatcher.py     → Slack/Email alert delivery
config.py         → YAML + env var configuration loading
main.py           → CLI entry point
models.py         → Data models (CostEntry, BaselineProfile, AnomalyAlert)
```

## Supported OCI Services

- **Compute**: Bare Metal, Virtual Machines, Oracle Compute Units (OCUs)
- **Storage**: Block Volumes, Object Storage, Archive Storage, File Storage
- **Database**: Autonomous Database, Exadata, Bare Metal DB Systems
- **Networking**: VCN, Load Balancer, DNS, FastConnect
- **Containers**: OKE (Kubernetes), Container Instances, Functions
- **Analytics**: Big Data, Data Flow, Streaming
- **Migration**: Application Migration Service
- **Management**: Monitoring, Logging, Vault, Identity

## License

MIT