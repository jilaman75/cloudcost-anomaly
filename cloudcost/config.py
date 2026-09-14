"""
Configuration management for CloudCost Anomaly.

Loads settings from YAML config file and environment variables.
"""

import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ProviderConfig:
    """Configuration for a single cloud provider."""
    enabled: bool = True
    # AWS
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_account_id: Optional[str] = None
    # Azure
    azure_subscription_id: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    # GCP
    gcp_project_id: Optional[str] = None
    gcp_credentials_path: Optional[str] = None
    gcp_billing_account: Optional[str] = None

@dataclass
class AlertConfig:
    """Configuration for anomaly alerts."""
    threshold_pct: float = 30.0       # Cost deviation threshold
    check_interval_minutes: int = 60   # How often to check
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_recipients: list = None     # List of email addresses
    severity_levels: list = None      # ['warning', 'critical']

@dataclass
class AppConfig:
    """Main application configuration."""
    providers: ProviderConfig = field(default_factory=ProviderConfig)
    alert: AlertConfig = field(default_factory=AlertConfig)
    history_days: int = 30             # Days of historical data for baseline
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'providers': {
                'aws': {
                    'enabled': self.providers.enabled,
                    'region': self.providers.aws_region,
                    'account_id': self.providers.aws_account_id
                },
                'azure': {
                    'enabled': True,  # Simplified
                    'subscription_id': self.providers.azure_subscription_id
                },
                'gcp': {
                    'enabled': True,
                    'project_id': self.providers.gcp_project_id
                }
            },
            'alert': {
                'threshold_pct': self.alert.threshold_pct,
                'slack_webhook_url': self.alert.slack_webhook_url,
                'email_recipients': self.alert.email_recipients or []
            }
        }

def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        AppConfig instance with loaded settings
    """
    if not os.path.exists(config_path):
        # Return default config if file doesn't exist
        return AppConfig()
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return AppConfig()
    
    # Parse provider config
    providers_data = data.get('providers', {})
    aws_data = providers_data.get('aws', {})
    azure_data = providers_data.get('azure', {})
    gcp_data = providers_data.get('gcp', {})
    
    provider_config = ProviderConfig(
        enabled=providers_data.get('enabled', True),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', aws_data.get('access_key_id')),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', aws_data.get('secret_access_key')),
        aws_region=aws_data.get('region', 'us-east-1'),
        aws_account_id=aws_data.get('account_id'),
        azure_subscription_id=azure_data.get('subscription_id'),
        azure_tenant_id=azure_data.get('tenant_id'),
        azure_client_id=azure_data.get('client_id'),
        azure_client_secret=azure_data.get('client_secret'),
        gcp_project_id=gcp_data.get('project_id'),
        gcp_credentials_path=gcp_data.get('credentials_path'),
        gcp_billing_account=gcp_data.get('billing_account')
    )
    
    # Parse alert config
    alert_data = data.get('alert', {})
    alert_config = AlertConfig(
        threshold_pct=alert_data.get('threshold_pct', 30.0),
        check_interval_minutes=alert_data.get('check_interval_minutes', 60),
        slack_webhook_url=alert_data.get('slack_webhook_url'),
        slack_channel=alert_data.get('slack_channel'),
        smtp_host=alert_data.get('smtp_host'),
        smtp_port=alert_data.get('smtp_port', 587),
        smtp_user=alert_data.get('smtp_user'),
        smtp_password=alert_data.get('smtp_password'),
        email_recipients=alert_data.get('email_recipients', []),
        severity_levels=alert_data.get('severity_levels', ['warning', 'critical'])
    )
    
    return AppConfig(providers=provider_config, alert=alert_config)

def load_from_env() -> AppConfig:
    """Load configuration from environment variables only."""
    return AppConfig(
        providers=ProviderConfig(
            enabled=True,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_region=os.getenv('AWS_REGION', 'us-east-1'),
            aws_account_id=os.getenv('AWS_ACCOUNT_ID'),
            azure_subscription_id=os.getenv('AZURE_SUBSCRIPTION_ID'),
            gcp_project_id=os.getenv('GCP_PROJECT_ID'),
            gcp_credentials_path=os.getenv('GCP_CREDENTIALS_PATH')
        ),
        alert=AlertConfig(
            threshold_pct=float(os.getenv('ANOMALY_THRESHOLD_PCT', '30')),
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            smtp_host=os.getenv('SMTP_HOST'),
            smtp_user=os.getenv('SMTP_USER')
        )
    )