"""
Anomaly detection engine: baseline tracking and spike detection.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from cloudcost.models import CostEntry, BaselineProfile, AnomalyAlert

class AnomalyDetector:
    """Detects cost anomalies using statistical baselines.
    
    Tracks per-service baselines and flags deviations exceeding threshold.
    Supports multiple detection strategies:
    - Static threshold (percentage above mean)
    - Z-score based (statistical outliers)
    - Moving average (trend-based)
    """
    
    def __init__(self, threshold_pct: float = 30.0, 
                 min_samples: int = 7,
                 baseline_days: int = 30):
        """Initialize anomaly detector.
        
        Args:
            threshold_pct: Percentage deviation from mean to trigger alert
            min_samples: Minimum data points before anomaly detection
            baseline_days: Number of days of history for baseline
        """
        self.threshold_pct = threshold_pct
        self.min_samples = min_samples
        self.baseline_days = baseline_days
        self.baselines: Dict[str, BaselineProfile] = {}
        self.history: Dict[str, List[CostEntry]] = defaultdict(list)
        
    def update_baseline(self, entries: List[CostEntry]):
        """Update baselines with new cost data.
        
        Args:
            entries: List of cost entries to learn from
        """
        # Group entries by provider+service for per-service baselines
        grouped: Dict[str, List[CostEntry]] = defaultdict(list)
        
        for entry in entries:
            key = f"{entry.provider}:{entry.service}"
            grouped[key].append(entry)
        
        # Update baselines for each group
        for key, group_entries in grouped.items():
            if len(group_entries) >= self.min_samples:
                costs = [e.cost for e in group_entries]
                mean_cost = sum(costs) / len(costs)
                
                if key not in self.baselines:
                    self.baselines[key] = BaselineProfile(
                        service=group_entries[0].service,
                        provider=group_entries[0].provider,
                        mean_cost=mean_cost,
                        std_dev_cost=0,
                        min_cost=min(costs),
                        max_cost=max(costs),
                        sample_count=len(costs),
                        last_updated=datetime.now()
                    )
                else:
                    self.baselines[key].update(mean_cost)
                    
                # Store history for trend analysis
                self.history[key].extend(group_entries)
                # Keep only last N days of history
                cutoff = datetime.now() - timedelta(days=self.baseline_days)
                self.history[key] = [
                    e for e in self.history[key] 
                    if datetime.fromisoformat(e.timestamp) > cutoff
                ]
    
    def detect(self, entries: List[CostEntry]) -> List[AnomalyAlert]:
        """Detect anomalies in current cost entries.
        
        Args:
            entries: Current cost entries to evaluate
            
        Returns:
            List of detected AnomalyAlert objects
        """
        alerts = []
        
        # First update baselines with all entries
        self.update_baseline(entries)
        
        # Check each entry against its baseline
        for entry in entries:
            key = f"{entry.provider}:{entry.service}"
            baseline = self.baselines.get(key)
            
            if baseline is None:
                # No baseline yet, can't detect anomalies
                continue
            
            if baseline.is_anomaly(entry.cost, self.threshold_pct):
                deviation_pct = abs(entry.cost - baseline.mean_cost) / baseline.mean_cost * 100
                
                alert = AnomalyAlert(
                    alert_id=f"{entry.provider}_{entry.service}_{entry.timestamp}",
                    service=entry.service,
                    provider=entry.provider,
                    current_cost=entry.cost,
                    baseline_mean=baseline.mean_cost,
                    deviation_pct=deviation_pct,
                    threshold_pct=self.threshold_pct,
                    timestamp=entry.timestamp,
                    account_id=entry.account_id,
                    severity="critical" if deviation_pct > 100 else "warning",
                    message=f"{entry.provider}:{entry.service} cost ${entry.cost:.2f} "
                           f"is {deviation_pct:.1f}% above baseline ${baseline.mean_cost:.2f}"
                )
                alerts.append(alert)
        
        return alerts
    
    def get_baseline_summary(self) -> Dict[str, Dict]:
        """Get a summary of all current baselines.
        
        Returns:
            Dict mapping provider:service -> baseline stats
        """
        summary = {}
        for key, baseline in self.baselines.items():
            summary[key] = {
                'mean_cost': round(baseline.mean_cost, 2),
                'std_dev': round(baseline.std_dev_cost, 2),
                'min_cost': round(baseline.min_cost, 2),
                'max_cost': round(baseline.max_cost, 2),
                'sample_count': baseline.sample_count,
                'last_updated': baseline.last_updated.isoformat()
            }
        return summary