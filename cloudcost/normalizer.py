"""
Normalization engine: converts raw provider data into a common schema.
"""

from typing import List, Dict, Any
from datetime import datetime
from cloudcost.models import CostEntry

class CostNormalizer:
    """Normalizes cost data from any provider to a common schema.
    
    Each provider returns different field names, currencies, and formats.
    This engine maps them to a unified CostEntry schema.
    """
    
    # Service name mapping for cross-provider consistency
    SERVICE_MAP = {
        # AWS -> Standard name
        'Amazon Elastic Compute Cloud - Compute': 'Compute',
        'Amazon EC2': 'Compute',
        'Amazon S3': 'Storage',
        'Amazon Relational Database Service': 'Database',
        'Amazon Lambda': 'Serverless',
        'Amazon CloudFront': 'CDN',
        'Amazon RDS': 'Database',
        'Amazon Redshift': 'Data Warehouse',
        # Azure -> Standard name
        'Virtual Machines': 'Compute',
        'Azure Blob Storage': 'Storage',
        'Azure SQL Database': 'Database',
        'Azure Cosmos DB': 'Database',
        'Azure App Service': 'PaaS',
        'Azure Kubernetes Service': 'Kubernetes',
        'Azure Functions': 'Serverless',
        'Azure CDN': 'CDN',
        # GCP -> Standard name
        'Compute Engine': 'Compute',
        'Cloud Storage': 'Storage',
        'Cloud SQL': 'Database',
        'BigQuery': 'Data Warehouse',
        'Cloud Functions': 'Serverless',
        'Cloud CDN': 'CDN',
        'Google Kubernetes Engine': 'Kubernetes',
        'Cloud Pub/Sub': 'Messaging'
    }
    
    def normalize_provider(self, raw_data: List[Dict], 
                           provider: str) -> List[CostEntry]:
        """Normalize raw provider data to CostEntry schema.
        
        Args:
            raw_data: List of raw cost entries from provider
            provider: 'aws', 'azure', or 'gcp'
            
        Returns:
            List of normalized CostEntry objects
        """
        normalized = []
        
        for entry in raw_data:
            try:
                cost_entry = self._map_entry(entry, provider)
                if cost_entry:
                    normalized.append(cost_entry)
            except (KeyError, ValueError, TypeError) as e:
                # Skip malformed entries, log for debugging
                continue
                
        return normalized
    
    def _map_entry(self, entry: Dict, provider: str) -> CostEntry:
        """Map a single raw entry to CostEntry schema.
        
        Args:
            entry: Raw cost entry dict
            provider: Provider identifier
            
        Returns:
            Normalized CostEntry or None if mapping fails
        """
        # Extract common fields with provider-specific key mapping
        service = entry.get('service', entry.get('Service', 'Unknown'))
        cost = entry.get('cost', entry.get('Cost', 0))
        usage = entry.get('usage_quantity', entry.get('UsageQuantity', 0))
        timestamp = entry.get('timestamp', entry.get('Timestamp', 
                         datetime.now().strftime('%Y-%m-%d')))
        account_id = entry.get('account_id', entry.get('AccountId', 
                        entry.get('subscription_id', None)))
        region = entry.get('region', entry.get('Location', None))
        
        # Normalize service name
        service = self.SERVICE_MAP.get(service, service)
        
        # Ensure cost is a float
        try:
            cost = float(cost)
        except (ValueError, TypeError):
            cost = 0.0
        
        # Ensure usage is a float
        try:
            usage = float(usage)
        except (ValueError, TypeError):
            usage = 0.0
        
        # Extract metadata for provider-specific fields
        metadata = {k: v for k, v in entry.items() 
                   if k not in ['service', 'cost', 'usage_quantity', 'timestamp', 
                               'account_id', 'region', 'provider']}
        
        return CostEntry(
            timestamp=timestamp,
            service=service,
            cost=cost,
            usage_quantity=usage,
            provider=provider,
            account_id=account_id,
            region=region,
            metadata=metadata
        )