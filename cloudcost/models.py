"""
Data models for cross-cloud cost anomaly detection.

Defines the normalized schema that all providers conform to.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class CostEntry:
    """Normalized cost entry from any cloud provider.
    
    All providers map their raw data to this common schema.
    """
    timestamp: str                    # ISO 8601 date string
    service: str                      # Service name (e.g., "EC2", "Virtual Machines")
    cost: float                       # Normalized cost in USD
    usage_quantity: float = 0.0       # Usage units
    provider: str = ""                # 'aws', 'azure', or 'gcp'
    account_id: Optional[str] = None  # Account/subscription/project ID
    region: Optional[str] = None      # Geographic region
    metadata: Dict[str, Any] = field(default_factory=dict)  # Provider-specific extras

@dataclass
class BaselineProfile:
    """Statistical baseline for a service cost pattern.
    
    Used to determine what's 'normal' for anomaly detection.
    """
    service: str
    provider: str
    mean_cost: float
    std_dev_cost: float
    min_cost: float
    max_cost: float
    sample_count: int
    last_updated: datetime
    
    def is_anomaly(self, cost: float, threshold_pct: float = 30.0) -> bool:
        """Check if a cost value is anomalous.
        
        Args:
            cost: Current cost to evaluate
            threshold_pct: Percentage deviation from mean to trigger anomaly
            
        Returns:
            True if cost exceeds threshold
        """
        if self.mean_cost == 0:
            return cost > 0  # Any cost is anomalous if baseline is zero
        
        deviation = abs(cost - self.mean_cost) / self.mean_cost * 100
        return deviation >= threshold_pct
    
    def update(self, new_cost: float):
        """Update baseline with a new data point (rolling statistics)."""
        self.sample_count += 1
        self.mean_cost = ((self.mean_cost * (self.sample_count - 1)) + new_cost) / self.sample_count
        # Simplified std dev update (full impl would use Welford's algorithm)
        if self.sample_count > 1:
            self.std_dev_cost = abs(new_cost - self.mean_cost)

@dataclass
class AnomalyAlert:
    """Detected cost anomaly with alert metadata."""
    alert_id: str
    service: str
    provider: str
    current_cost: float
    baseline_mean: float
    deviation_pct: float
    threshold_pct: float
    timestamp: str
    account_id: Optional[str] = None
    severity: str = "warning"  # 'warning', 'critical'
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize alert to dictionary for dispatch."""
        return {
            'alert_id': self.alert_id,
            'service': self.service,
            'provider': self.provider,
            'current_cost': self.current_cost,
            'baseline_mean': self.baseline_mean,
            'deviation_pct': round(self.deviation_pct, 2),
            'threshold_pct': self.threshold_pct,
            'timestamp': self.timestamp,
            'account_id': self.account_id,
            'severity': self.severity,
            'message': self.message
        }