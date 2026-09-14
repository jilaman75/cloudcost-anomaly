# CloudCost Anomaly

Cross-cloud cost monitoring and anomaly detection for AWS, Azure, and GCP.

## Overview

CloudCost Anomaly pulls billing data from all three major cloud providers, normalizes the data into a common schema, builds statistical baselines per service, and sends real-time alerts when costs deviate beyond a configurable threshold (default: 30%).

## Features

- **Multi-provider support**: AWS Cost Explorer, Azure Cost Management, GCP Cloud Billing
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

```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_ACCOUNT_ID="123456789012"
export AZURE_SUBSCRIPTION_ID="your-sub"
export GCP_PROJECT_ID="your-project"
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

## Architecture

```
providers/
  aws.py          → AWS Cost Explorer API
  azure.py        → Azure Cost Management API  
  gcp.py          → GCP Cloud Billing API
normalizer.py     → Maps provider data to CostEntry schema
detector.py       → Statistical baseline tracking & anomaly detection
dispatcher.py     → Slack/Email alert delivery
config.py         → YAML + env var configuration loading
main.py           → CLI entry point
models.py         → Data models (CostEntry, BaselineProfile, AnomalyAlert)
```

## License

MIT