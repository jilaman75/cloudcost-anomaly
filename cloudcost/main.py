"""
CloudCost Anomaly - Main CLI entry point.

Cross-cloud cost monitoring and anomaly detection for AWS, Azure, and GCP.
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
from cloudcost.config import load_config, load_from_env
from cloudcost.providers import AWSProvider, AzureProvider, GCPProvider
from cloudcost.normalizer import CostNormalizer
from cloudcost.detector import AnomalyDetector
from cloudcost.dispatcher import AlertDispatcher

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Cross-cloud cost anomaly detection for AWS, Azure, and GCP'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Run one-time anomaly check and exit'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate provider credentials and exit'
    )
    parser.add_argument(
        '--history-days',
        type=int,
        default=30,
        help='Number of days of historical data for baseline (default: 30)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=None,
        help='Anomaly threshold percentage (overrides config)'
    )
    return parser.parse_args()

def build_providers(config):
    """Build provider instances from config."""
    providers = {}
    
    aws_config = config.providers
    if aws_config.enabled:
        providers['aws'] = AWSProvider(
            access_key_id=aws_config.aws_access_key_id,
            secret_access_key=aws_config.aws_secret_access_key,
            region_name=aws_config.aws_region,
            account_id=aws_config.aws_account_id
        )
    
    azure_config = aws_config
    if azure_config.azure_subscription_id:
        providers['azure'] = AzureProvider(
            subscription_id=azure_config.azure_subscription_id,
            tenant_id=azure_config.azure_tenant_id,
            client_id=azure_config.azure_client_id,
            client_secret=azure_config.azure_client_secret
        )
    
    gcp_config = azure_config
    if gcp_config.gcp_project_id:
        providers['gcp'] = GCPProvider(
            project_id=gcp_config.gcp_project_id,
            credentials_path=gcp_config.gcp_credentials_path,
            billing_account=gcp_config.gcp_billing_account
        )
    
    return providers

def validate_providers(providers):
    """Validate all provider credentials."""
    results = {}
    for name, provider in providers.items():
        results[name] = provider.validate_credentials()
        print(f"{name}: {'OK' if results[name] else 'FAILED'}")
    return results

def fetch_all_costs(providers, start_date, end_date):
    """Fetch cost data from all enabled providers."""
    all_costs = []
    
    if 'aws' in providers:
        print("Fetching AWS cost data...")
        all_costs.extend(providers['aws'].get_cost_data(start_date, end_date))
    
    if 'azure' in providers:
        print("Fetching Azure cost data...")
        all_costs.extend(providers['azure'].get_cost_data(start_date, end_date))
    
    if 'gcp' in providers:
        print("Fetching GCP cost data...")
        all_costs.extend(providers['gcp'].get_cost_data(start_date, end_date))
    
    return all_costs

def run_anomaly_check(config, history_days, threshold=None):
    """Run a single anomaly detection cycle.
    
    Args:
        config: AppConfig instance
        history_days: Number of historical days for baseline
        threshold: Optional threshold override
        
    Returns:
        List of AnomalyAlert objects
    """
    providers = build_providers(config)
    if not providers:
        print("No providers configured. Check your config.yaml file.")
        return []
    
    # Validate credentials first
    valid = validate_providers(providers)
    if not any(valid.values()):
        print("No valid provider credentials found.")
        return []
    
    # Fetch historical data for baseline
    end_date = datetime.now()
    start_date = end_date - timedelta(days=history_days)
    print(f"Fetching {history_days} days of cost data...")
    historical_costs = fetch_all_costs(providers, start_date, end_date)
    
    # Normalize all data
    normalizer = CostNormalizer()
    normalized = normalizer.normalize_provider(historical_costs, 'aws') if historical_costs else []
    
    # Normalize each provider's data separately
    all_normalized = []
    for provider_name, provider in providers.items():
        raw_data = provider.get_cost_data(start_date, end_date)
        normalized_data = normalizer.normalize_provider(raw_data, provider_name)
        all_normalized.extend(normalized_data)
    
    # Initialize detector
    detector = AnomalyDetector(
        threshold_pct=threshold if threshold is not None else config.alert.threshold_pct,
        baseline_days=history_days
    )
    
    # Update baselines with historical data
    detector.update_baseline(all_normalized)
    
    # Fetch current data for anomaly detection
    current_start = end_date - timedelta(days=1)
    print("Fetching current cost data...")
    current_costs = fetch_all_costs(providers, current_start, end_date)
    
    # Normalize current data
    current_normalized = []
    for provider_name, provider in providers.items():
        raw_data = provider.get_cost_data(current_start, end_date)
        current_normalized.extend(normalizer.normalize_provider(raw_data, provider_name))
    
    # Detect anomalies
    alerts = detector.detect(current_normalized)
    
    # Dispatch alerts
    if alerts:
        dispatcher = AlertDispatcher(
            slack_webhook_url=config.alert.slack_webhook_url,
            smtp_host=config.alert.smtp_host,
            smtp_port=config.alert.smtp_port,
            smtp_user=config.alert.smtp_user,
            smtp_password=config.alert.smtp_password,
            email_from=config.alert.email_from,
            email_to=config.alert.email_recipients
        )
        dispatcher.dispatch(alerts)
        print(f"Detected {len(alerts)} anomaly(s). Alerts dispatched.")
    else:
        print("No anomalies detected.")
    
    return alerts

def main():
    """Main entry point."""
    args = parse_args()
    
    # Load config
    if args.config and args.config != 'config.yaml':
        config = load_config(args.config)
    else:
        config = load_from_env()
    
    # Validate mode
    if args.validate:
        providers = build_providers(config)
        if not providers:
            print("No providers configured.")
            sys.exit(1)
        results = validate_providers(providers)
        sys.exit(0 if any(results.values()) else 1)
    
    # One-time check mode
    if args.check:
        alerts = run_anomaly_check(
            config,
            history_days=args.history_days,
            threshold=args.threshold
        )
        sys.exit(0 if alerts else 0)
    
    # Default: run continuous monitoring loop
    print("Starting continuous monitoring...")
    print(f"Check interval: {config.alert.check_interval_minutes} minutes")
    print(f"Anomaly threshold: {config.alert.threshold_pct}%")
    
    while True:
        run_anomaly_check(
            config,
            history_days=args.history_days,
            threshold=args.threshold
        )
        # Sleep for check interval (simplified for now)
        import time
        time.sleep(config.alert.check_interval_minutes * 60)

if __name__ == '__main__':
    main()