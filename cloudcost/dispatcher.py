"""
Alert dispatcher: sends notifications via Slack and email.
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
from cloudcost.models import AnomalyAlert

class AlertDispatcher:
    """Dispatches anomaly alerts to configured channels."""
    
    def __init__(self, slack_webhook_url: Optional[str] = None,
                 smtp_host: Optional[str] = None, smtp_port: int = 587,
                 smtp_user: Optional[str] = None, 
                 smtp_password: Optional[str] = None,
                 email_from: Optional[str] = None,
                 email_to: Optional[List[str]] = None):
        """Initialize alert dispatcher.
        
        Args:
            slack_webhook_url: Slack incoming webhook URL
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            email_from: Sender email address
            email_to: List of recipient email addresses
        """
        self.slack_webhook_url = slack_webhook_url
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.email_from = email_from
        self.email_to = email_to or []
        
    def dispatch(self, alerts: List[AnomalyAlert], 
                 channels: List[str] = None):
        """Send alerts to configured channels.
        
        Args:
            alerts: List of AnomalyAlert objects to dispatch
            channels: Override default channels (['slack', 'email'])
        """
        if not channels:
            channels = []
            if self.slack_webhook_url:
                channels.append('slack')
            if self.smtp_host and self.email_to:
                channels.append('email')
        
        for alert in alerts:
            for channel in channels:
                if channel == 'slack':
                    self._send_slack(alert)
                elif channel == 'email':
                    self._send_email(alert)
    
    def _send_slack(self, alert: AnomalyAlert):
        """Send alert to Slack via webhook.
        
        Args:
            alert: Alert to send
        """
        if not self.slack_webhook_url:
            return
            
        try:
            import requests
            
            severity_icon = "🔴" if alert.severity == "critical" else "🟡"
            
            payload = {
                "text": f"{severity_icon} *Cloud Cost Anomaly Detected*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"Cloud Cost Anomaly Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Provider:*\n{alert.provider.upper()}"},
                            {"type": "mrkdwn", "text": f"*Service:*\n{alert.service}"},
                            {"type": "mrkdwn", "text": f"*Current Cost:*\n${alert.current_cost:.2f}"},
                            {"type": "mrkdwn", "text": f"*Baseline:*\n${alert.baseline_mean:.2f}"},
                            {"type": "mrkdwn", "text": f"*Deviation:*\n{alert.deviation_pct:.1f}%"},
                            {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity.upper()}"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": alert.message
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Timestamp: {alert.timestamp} | Account: {alert.account_id or 'N/A'}"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Slack dispatch failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error sending Slack alert: {e}")
    
    def _send_email(self, alert: AnomalyAlert):
        """Send alert via SMTP email.
        
        Args:
            alert: Alert to send
        """
        if not all([self.smtp_host, self.smtp_user, self.email_to]):
            return
            
        try:
            severity_color = "#FF0000" if alert.severity == "critical" else "#FFA500"
            
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            msg['Subject'] = f"[{alert.severity.upper()}] Cloud Cost Anomaly: {alert.service}"
            
            body = f"""
Cloud Cost Anomaly Detected

Provider: {alert.provider.upper()}
Service: {alert.service}
Current Cost: ${alert.current_cost:.2f}
Baseline: ${alert.baseline_mean:.2f}
Deviation: {alert.deviation_pct:.1f}%
Threshold: {alert.threshold_pct}%
Severity: {alert.severity.upper()}
Timestamp: {alert.timestamp}
Account: {alert.account_id or 'N/A'}

{alert.message}

Action Required: Review cost and investigate unexpected spike.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.email_from, self.email_to, msg.as_string())
                
        except Exception as e:
            print(f"Error sending email alert: {e}")
    
    def format_summary(self, alerts: List[AnomalyAlert]) -> str:
        """Format alerts as a human-readable summary.
        
        Args:
            alerts: List of alerts to format
            
        Returns:
            Formatted summary string
        """
        if not alerts:
            return "No anomalies detected."
            
        lines = [f"Cloud Cost Anomaly Report ({datetime.now().isoformat()})", "=" * 50]
        
        for alert in alerts:
            lines.append(f"\n[{alert.severity.upper()}] {alert.provider}:{alert.service}")
            lines.append(f"  Current: ${alert.current_cost:.2f}")
            lines.append(f"  Baseline: ${alert.baseline_mean:.2f}")
            lines.append(f"  Deviation: {alert.deviation_pct:.1f}%")
            lines.append(f"  Message: {alert.message}")
            
        return "\n".join(lines)