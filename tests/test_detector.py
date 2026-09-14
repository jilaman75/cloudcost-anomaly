"""
Tests for anomaly detection engine.
"""

import pytest
from datetime import datetime, timedelta
from cloudcost.models import CostEntry, BaselineProfile, AnomalyAlert
from cloudcost.detector import AnomalyDetector

def test_baseline_creation():
    """Test baseline profile creation and anomaly detection."""
    baseline = BaselineProfile(
        service="Compute",
        provider="aws",
        mean_cost=100.0,
        std_dev_cost=10.0,
        min_cost=80.0,
        max_cost=120.0,
        sample_count=30,
        last_updated=datetime.now()
    )
    
    # 30% deviation should trigger
    assert baseline.is_anomaly(130.0, threshold_pct=30.0) == True
    # 29% deviation should NOT trigger
    assert baseline.is_anomaly(129.0, threshold_pct=30.0) == False
    

def test_zero_baseline():
    """Test that any cost is anomalous when baseline is zero."""
    baseline = BaselineProfile(
        service="NewService",
        provider="aws",
        mean_cost=0.0,
        std_dev_cost=0.0,
        min_cost=0.0,
        max_cost=0.0,
        sample_count=1,
        last_updated=datetime.now()
    )
    
    assert baseline.is_anomaly(1.0, threshold_pct=30.0) == True


def test_detector_basic():
    """Test anomaly detector with synthetic data."""
    detector = AnomalyDetector(threshold_pct=30.0, min_samples=3)
    
    # Create normal data
    entries = [
        CostEntry(timestamp=(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                  service="Compute", provider="aws", cost=100.0)
        for i in range(10)
    ]
    
    detector.update_baseline(entries)
    assert "aws:Compute" in detector.baselines
    
    baseline = detector.baselines["aws:Compute"]
    assert abs(baseline.mean_cost - 100.0) < 1.0


def test_detector_anomaly():
    """Test that anomalies are detected correctly."""
    detector = AnomalyDetector(threshold_pct=30.0, min_samples=3)
    
    # Normal baseline
    normal_entries = [
        CostEntry(timestamp=(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                  service="Compute", provider="aws", cost=100.0)
        for i in range(10)
    ]
    
    detector.update_baseline(normal_entries)
    
    # Anomalous entry (30-100% deviation → warning severity)
    anomalous_entries = [
        CostEntry(timestamp=datetime.now().strftime('%Y-%m-%d'),
                  service="Compute", provider="aws", cost=150.0)
    ]
    
    alerts = detector.detect(anomalous_entries)
    
    assert len(alerts) > 0
    assert alerts[0].deviation_pct > 30.0
    assert alerts[0].severity == "warning"


def test_detector_critical():
    """Test critical severity detection."""
    detector = AnomalyDetector(threshold_pct=30.0, min_samples=3)
    
    # Normal baseline
    normal_entries = [
        CostEntry(timestamp=(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                  service="Compute", provider="aws", cost=100.0)
        for i in range(10)
    ]
    
    detector.update_baseline(normal_entries)
    
    # Very anomalous entry (>100% deviation)
    anomalous_entries = [
        CostEntry(timestamp=datetime.now().strftime('%Y-%m-%d'),
                  service="Compute", provider="aws", cost=1000.0)
    ]
    
    alerts = detector.detect(anomalous_entries)
    
    assert len(alerts) > 0
    assert alerts[0].severity == "critical"


def test_normalizer_svc_map():
    """Test service name normalization."""
    from cloudcost.normalizer import CostNormalizer
    
    normalizer = CostNormalizer()
    
    raw_entry = {
        'service': 'Amazon Elastic Compute Cloud - Compute',
        'cost': 50.0,
        'usage_quantity': 100,
        'timestamp': '2026-09-14'
    }
    
    entry = normalizer._map_entry(raw_entry, 'aws')
    assert entry.service == "Compute"
    assert entry.cost == 50.0
    assert entry.provider == "aws"