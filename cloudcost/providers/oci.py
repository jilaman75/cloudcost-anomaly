"""
Oracle Cloud Infrastructure Cost Management API integration for cloud cost anomaly detection.
"""

from oracle_cloud_agent import OCISignInInterceptor
from oracle_cloud_cost_management import CostManagementClient
from oracle_cloud_identity import IdentityClient
from datetime import datetime, timedelta
from typing import List, Dict, Any

class OCIProvider:
    """Oracle Cloud Infrastructure Cost Management integration for cross-cloud cost normalization."""
    
    def __init__(self, tenant_ocid: str = None, user_ocid: str = None,
                 fingerprint: str = None, private_key_path: str = None,
                 compartment_ocid: str = None, region: str = None):
        """Initialize OCI Cost Management client.
        
        Args:
            tenant_ocid: OCID of the tenancy
            user_ocid: OCID of the user
            fingerprint: User's key fingerprint
            private_key_path: Path to private key file for authentication
            compartment_ocid: OCID of the compartment to query costs for
            region: OCI region (e.g., "us-ashburn-1")
        """
        self.tenant_ocid = tenant_ocid
        self.user_ocid = user_ocid
        self.fingerprint = fingerprint
        self.private_key_path = private_key_path
        self.compartment_ocid = compartment_ocid
        self.region = region
        self._cost_client = None
        self._identity_client = None
        
    @property
    def cost_client(self):
        """Lazy-load OCI Cost Management client."""
        if self._cost_client is None:
            interceptor = OCISignInInterceptor(
                auth_type="api_key",
                tenant_id=self.tenant_ocid,
                user_id=self.user_ocid,
                fingerprint=self.fingerprint,
                private_key=self.private_key_path
            )
            self._cost_client = CostManagementClient(
                region=self.region,
                interceptors=[interceptor]
            )
        return self._cost_client
    
    @property
    def identity_client(self):
        """Lazy-load OCI Identity client."""
        if self._identity_client is None:
            interceptor = OCISignInInterceptor(
                auth_type="api_key",
                tenant_id=self.tenant_ocid,
                user_id=self.user_ocid,
                fingerprint=self.fingerprint,
                private_key=self.private_key_path
            )
            self._identity_client = IdentityClient(
                region=self.region,
                interceptors=[interceptor]
            )
        return self._identity_client
    
    def get_cost_data(self, start_date: datetime, end_date: datetime,
                     compartment_ocid: str = None) -> List[Dict]:
        """Get cost data from OCI Cost Management.
n        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            compartment_ocid: Optional compartment OCID to filter by
            
        Returns:
            List of cost data with resource compartment breakdown
        """
        target_compartment = compartment_ocid or self.compartment_ocid
        if not target_compartment:
            print("No OCI compartment OCID provided")
            return []
            
        try:
            # Get cost analysis for the specified compartment and time period
            response = self.cost_client.summarize_cost_analysis(
                cost_analysis_details={
                    "time_period": {
                        "start_time": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "end_time": end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                    },
                    "compartment_level_ancestors": [
                        {"id": target_compartment, "type": "COMPARTMENT"}
                    ],
                    "granularity": "MONTHLY",
                    "aggregation": {
                        "total_cost": {
                            "name": "cost",
                            "function": "sum"
                        }
                    },
                    "group_by": [
                        {"key": "COMPARTMENT", "type": "TAG"},
                        {"key": "SERVICE", "type": "DIMENSION"},
                        {"key": "RESOURCE_TYPE", "type": "DIMENSION"}
                    ]
                }
            )
            
            cost_data = []
            for summary in response.data:
                for group in summary.groups:
                    cost_entry = {
                        'timestamp': start_date.strftime('%Y-%m-%d'),
                        'service': group['service'] or 'Unknown',
                        'resource_type': group['resource_type'] or 'Unknown',
                        'compartment': group['compartment'] or 'Unknown',
                        'cost': float(group['total_cost']['value']) if group['total_cost'] else 0.0,
                        'currency': group['total_cost']['currency'] if group['total_cost'] else 'USD',
                        'provider': 'oci',
                        'tenant_ocid': self.tenant_ocid
                    }
                    cost_data.append(cost_entry)
                    
            return cost_data
            
        except Exception as e:
            print(f"Error fetching OCI cost data: {e}")
            return []
    
    def get_tenancy_costs(self) -> List[Dict]:
        """Get cost breakdown by tenancy.
        
        Returns:
            List of tenancy cost data
        """
        try:
            response = self.cost_client.summarize_cost_analysis(
                cost_analysis_details={
                    "time_period": {
                        "start_time": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "end_time": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                    },
                    "aggregation": {
                        "total_cost": {
                            "name": "cost",
                            "function": "sum"
                        }
                    },
                    "group_by": [
                        {"key": "TENANCY", "type": "DIMENSION"}
                    ]
                }
            )
            
            tenancy_costs = []
            for summary in response.data:
                for group in summary.groups:
                    cost_entry = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d'),
                        'service': 'All Services',
                        'tenancy': group['tenancy'] or 'Unknown',
                        'cost': float(group['total_cost']['value']) if group['total_cost'] else 0.0,
                        'provider': 'oci'
                    }
                    tenancy_costs.append(cost_entry)
                    
            return tenancy_costs
            
        except Exception as e:
            print(f"Error fetching OCI tenancy costs: {e}")
            return []
    
    def get_resource_costs(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get cost breakdown by specific resources.
        
        Args:
            start_date: Start date for resource costs
            end_date: End date for resource costs
            
        Returns:
            List of resource cost data
        """
        try:
            response = self.cost_client.summarize_cost_analysis(
                cost_analysis_details={
                    "time_period": {
                        "start_time": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "end_time": end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                    },
                    "aggregation": {
                        "total_cost": {
                            "name": "cost",
                            "function": "sum"
                        }
                    },
                    "group_by": [
                        {"key": "COMPARTMENT", "type": "TAG"},
                        {"key": "SERVICE", "type": "DIMENSION"},
                        {"key": "RESOURCE_ID", "type": "DIMENSION"},
                        {"key": "RESOURCE_NAME", "type": "DIMENSION"}
                    ]
                }
            )
            
            resource_costs = []
            for summary in response.data:
                for group in summary.groups:
                    cost_entry = {
                        'timestamp': start_date.strftime('%Y-%m-%d'),
                        'service': group['service'] or 'Unknown',
                        'resource_id': group['resource_id'] or 'Unknown',
                        'resource_name': group['resource_name'] or 'Unknown',
                        'compartment': group['compartment'] or 'Unknown',
                        'cost': float(group['total_cost']['value']) if group['total_cost'] else 0.0,
                        'provider': 'oci'
                    }
                    resource_costs.append(cost_entry)
                    
            return resource_costs
            
        except Exception as e:
            print(f"Error fetching OCI resource costs: {e}")
            return []
    
    def validate_credentials(self) -> bool:
        """Validate OCI credentials and permissions.
        
        Returns:
            True if credentials are valid and Cost Management access is available
        """
        try:
            # Test with a simple query
            response = self.cost_client.summarize_cost_analysis(
                cost_analysis_details={
                    "time_period": {
                        "start_time": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "end_time": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                    },
                    "aggregation": {
                        "total_cost": {
                            "name": "cost",
                            "function": "sum"
                        }
                    },
                    "group_by": [
                        {"key": "SERVICE", "type": "DIMENSION"}
                    ]
                }
            )
            return True
        except Exception as e:
            print(f"OCI credential validation failed: {e}")
            return False