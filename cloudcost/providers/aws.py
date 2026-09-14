"""
AWS Cost Explorer API integration for cloud cost anomaly detection.
"""

import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AWSProvider:
    """AWS Cost Explorer integration for cross-cloud cost normalization."""
    
    def __init__(self, access_key_id: str = None, secret_access_key: str = None, 
                 region_name: str = "us-east-1", account_id: str = None):
        """Initialize AWS Cost Explorer client.
        
        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key  
            region_name: AWS region for Cost Explorer
            account_id: AWS account ID for grouping
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region_name = region_name
        self.account_id = account_id
        self._client = None
        
    @property
    def client(self):
        """Lazy-load AWS Cost Explorer client."""
        if self._client is None:
            if self.access_key_id and self.secret_access_key:
                self._client = boto3.client(
                    'ce',
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name=self.region_name
                )
            else:
                # Use default AWS profile/credentials
                self._client = boto3.client('ce', region_name=self.region_name)
        return self._client
    
    def get_cost_data(self, start_date: datetime, end_date: datetime, 
                     granularity: str = "DAILY", metrics: List[str] = None) -> List[Dict]:
        """Get cost data from AWS Cost Explorer.
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: Data granularity (HOURLY, DAILY, MONTHLY)
            metrics: List of metrics to retrieve (e.g., ['BlendedCost', 'UsageQuantity'])
            
        Returns:
            List of cost data with service-level breakdown
        """
        if metrics is None:
            metrics = ['BlendedCost']
            
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity=granularity,
                Metrics=metrics,
                GroupBy=[
                    {'Key': 'SERVICE', 'Type': 'DIMENSION'},
                    {'Key': 'USAGE_TYPE', 'Type': 'DIMENSION'}
                ]
            )
            
            cost_data = []
            for result in response['ResultsByTime']:
                time_period = result['TimePeriod']
                for group in result['Groups']:
                    cost_entry = {
                        'timestamp': time_period['Start'],
                        'service': group['Keys'][0],
                        'usage_type': group['Keys'][1],
                        'cost': float(group['Total'][metrics[0]]['Amount']),
                        'usage_quantity': float(group['Total'].get('UsageQuantity', 0)),
                        'provider': 'aws',
                        'account_id': self.account_id,
                        'region': self.region_name
                    }
                    cost_data.append(cost_entry)
                    
            return cost_data
            
        except Exception as e:
            print(f"Error fetching AWS cost data: {e}")
            return []
    
    def get_cost_tags(self, service: str = None, tag_key: str = None) -> Dict[str, Any]:
        """Get cost breakdown by tags for specific services.
        
        Args:
            service: Optional service name to filter by
            tag_key: Optional tag key to group by
            
        Returns:
            Dict with tag-based cost breakdown
        """
        try:
            group_by = [{'Key': 'SERVICE', 'Type': 'DIMENSION'}]
            if tag_key:
                group_by.append({'Key': f'TAG {tag_key}', 'Type': 'TAG_KEY'})
                
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'End': datetime.now().strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=group_by
            )
            
            tag_costs = {}
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    if service and service != service_name:
                        continue
                        
                    cost = float(group['Total']['BlendedCost']['Amount'])
                    
                    if len(group['Keys']) > 1:
                        tag_value = group['Keys'][1]
                        tag_costs[tag_value] = tag_costs.get(tag_value, 0) + cost
                    else:
                        tag_costs[service_name] = tag_costs.get(service_name, 0) + cost
                        
            return tag_costs
            
        except Exception as e:
            print(f"Error fetching AWS cost tags: {e}")
            return {}
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials and permissions.
        
        Returns:
            True if credentials are valid and Cost Explorer access is available
        """
        try:
            # Test with a simple API call
            self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'End': datetime.now().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[{'Key': 'SERVICE', 'Type': 'DIMENSION'}]
            )
            return True
        except Exception as e:
            print(f"AWS credential validation failed: {e}")
            return False