"""
Azure Cost Management API integration for cloud cost anomaly detection.
"""

from azure.mgmt.costmanagement import CostManagementClient
from azure.identity import DefaultAzureCredential
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AzureProvider:
    """Azure Cost Management integration for cross-cloud cost normalization."""
    
    def __init__(self, subscription_id: str = None, tenant_id: str = None,
                 client_id: str = None, client_secret: str = None,
                 scope: str = None):
        """Initialize Azure Cost Management client.
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID
            client_id: Azure client ID for service principal
            client_secret: Azure client secret for service principal
            scope: Resource scope (subscription or management group)
        """
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope or f"subscriptions/{subscription_id}" if subscription_id else None
        self._client = None
        
    @property
    def client(self):
        """Lazy-load Azure Cost Management client."""
        if self._client is None:
            credential = DefaultAzureCredential()
            self._client = CostManagementClient(credential, self.subscription_id)
        return self._client
    
    def get_cost_data(self, start_date: datetime, end_date: datetime,
                     granularity: str = "Daily", metric: str = "Cost") -> List[Dict]:
        """Get cost data from Azure Cost Management.
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: Time granularity (Hourly, Daily, Monthly)
            metric: Metric type (Cost, Usage, PreTaxCost, etc.)
            
        Returns:
            List of cost data with resource group/service breakdown
        """
        try:
            query = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "to": end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                "dataset": {
                    "granularity": granularity,
                    "aggregation": {
                        "totalCost": {
                            "name": metric,
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {"type": "Dimension", "name": "ServiceName"},
                        {"type": "Dimension", "name": "ResourceGroup"},
                        {"type": "Dimension", "name": "ResourceLocation"}
                    ],
                    "filter": {
                        "and": [
                            {
                                "dimensions": {
                                    "name": "ChargeType",
                                    "operator": "In",
                                    "values": ["Purchase", "Usage", "Refund", "Adjustment"]
                                }
                            }
                        ]
                    }
                }
            }
            
            response = self.client.query.usage(
                scope=self.scope,
                parameters=query
            )
            
            cost_data = []
            for row in response.rows:
                cost_entry = {
                    'timestamp': start_date.strftime('%Y-%m-%d'),  # Query returns aggregated data
                    'service': row[0] if len(row) > 0 else 'Unknown',
                    'resource_group': row[1] if len(row) > 1 else 'Unknown',
                    'location': row[2] if len(row) > 2 else 'Unknown',
                    'cost': float(row[3]) if len(row) > 3 else 0.0,
                    'provider': 'azure',
                    'subscription_id': self.subscription_id
                }
                cost_data.append(cost_entry)
                
            return cost_data
            
        except Exception as e:
            print(f"Error fetching Azure cost data: {e}")
            return []
    
    def get_cost_benefits(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get Azure reserved instance and other cost benefits.
        
        Args:
            start_date: Start date for benefits query
            end_date: End date for benefits query
            
        Returns:
            List of cost savings data
        """
        try:
            query = {
                "type": "AmortizedCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "to": end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {
                        "amortizedCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {"type": "Dimension", "name": "ServiceName"},
                        {"type": "Dimension", "name": "ReservationId"}
                    ]
                }
            }
            
            response = self.client.query.usage(
                scope=self.scope,
                parameters=query
            )
            
            benefits = []
            for row in response.rows:
                benefit_entry = {
                    'timestamp': start_date.strftime('%Y-%m-%d'),
                    'service': row[0] if len(row) > 0 else 'Unknown',
                    'reservation_id': row[1] if len(row) > 1 else 'OnDemand',
                    'amortized_cost': float(row[2]) if len(row) > 2 else 0.0,
                    'provider': 'azure'
                }
                benefits.append(benefit_entry)
                
            return benefits
            
        except Exception as e:
            print(f"Error fetching Azure cost benefits: {e}")
            return []
    
    def validate_credentials(self) -> bool:
        """Validate Azure credentials and permissions.
        
        Returns:
            True if credentials are valid and Cost Management access is available
        """
        try:
            # Test with a simple query
            self.client.query.usage(
                scope=self.scope,
                parameters={
                    "type": "ActualCost",
                    "timeframe": "MonthToDate",
                    "dataset": {"granularity": "Daily", "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}}}
                }
            )
            return True
        except Exception as e:
            print(f"Azure credential validation failed: {e}")
            return False
    
    def get_reservation_recommendations(self) -> List[Dict]:
        """Get Azure reservation recommendations for cost optimization.
        
        Returns:
            List of reservation recommendations with potential savings
        """
        try:
            # Get recommendations from the Recommendations API
            response = self.client.reservation_recommendations.get(
                scope=self.scope,
                parameters={
                    "properties": {
                        "addedServices": ["virtualMachines", "storage", "database"],
                        "location": "All",
                        "term": "P1Y",  # 1-year term
                        "model": "Standard"
                    },
                    "type": "Microsoft.Compute/virtualMachines"
                }
            )
            
            recommendations = []
            for rec in response.value or []:
                rec_entry = {
                    'resource_type': rec.name if rec.name else 'Unknown',
                    'urn': rec.id,
                    'current_usage': rec.properties.current_usages if hasattr(rec.properties, 'current_usages') else 0,
                    'recommended_quantity': rec.properties.recommended_quantity if hasattr(rec.properties, 'recommended_quantity') else 0,
                    'currency': rec.properties.currency if hasattr(rec.properties, 'currency') else 'USD',
                    'savings_percent': rec.properties.savings_percent if hasattr(rec.properties, 'savings_percent') else 0,
                    'provider': 'azure'
                }
                recommendations.append(rec_entry)
                
            return recommendations
            
        except Exception as e:
            print(f"Error fetching Azure reservation recommendations: {e}")
            return []