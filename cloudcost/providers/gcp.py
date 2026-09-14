"""
GCP Cloud Billing API integration for cloud cost anomaly detection.
"""

from google.cloud import billing_v1
from google.oauth2 import service_account
from datetime import datetime, timedelta
from typing import List, Dict, Any

class GCPProvider:
    """GCP Cloud Billing integration for cross-cloud cost normalization."""
    
    def __init__(self, project_id: str = None, credentials_path: str = None,
                 billing_account: str = None):
        """Initialize GCP Cloud Billing client.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON key
            billing_account: GCP billing account ID
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.billing_account = billing_account
        self._client = None
        self._billing_client = None
        
    @property
    def client(self):
        """Lazy-load GCP Cloud Billing client."""
        if self._client is None:
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self._client = billing_v1.CloudBillingClient(credentials=credentials)
            else:
                # Use default application credentials
                self._client = billing_v1.CloudBillingClient()
        return self._client
    
    @property
    def billing_client(self):
        """Lazy-load GCP Billing Account client."""
        if self._billing_client is None:
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self._billing_client = billing_v1.CloudBillingClient(credentials=credentials)
            else:
                self._billing_client = billing_v1.CloudBillingClient()
        return self._billing_client
    
    def get_cost_data(self, start_date: datetime, end_date: datetime,
                      project_id: str = None) -> List[Dict]:
        """Get cost data from GCP Cloud Billing.
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            project_id: GCP project ID (overrides instance default)
            
        Returns:
            List of cost data with service-level breakdown
        """
        target_project = project_id or self.project_id
        if not target_project:
            print("No GCP project ID provided")
            return []
            
        try:
            # Use Cloud Billing Export or BigQuery for detailed cost data
            # Alternatively, use the Cloud Billing Budgets API
            budget = self.billing_client.get_billing_account(
                name=f"billingAccounts/{self.billing_account}"
            ) if self.billing_account else None
            
            # For detailed cost data, use the Cloud Billing export to BigQuery
            # or the Cloud Cost Management API
            
            # Simulated cost data retrieval (actual implementation would use
            # BigQuery export or Cloud Billing API v1)
            cost_data = self._fetch_billing_data(target_project, start_date, end_date)
            
            return cost_data
            
        except Exception as e:
            print(f"Error fetching GCP cost data: {e}")
            return []
    
    def _fetch_billing_data(self, project_id: str, start_date: datetime,
                            end_date: datetime) -> List[Dict]:
        """Fetch billing data from GCP BigQuery export or API.
        
        Args:
            project_id: GCP project ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of cost data entries
        """
        # This is a placeholder for the actual implementation
        # In production, this would use:
        # 1. BigQuery export from Cloud Billing
        # 2. Cloud Billing API v1 with appropriate queries
        # 3. Cloud Cost Management API
        
        try:
            # Simulated response structure
            # Actual implementation would query BigQuery or the billing export
            cost_data = [
                {
                    'timestamp': start_date.strftime('%Y-%m-%d'),
                    'service': 'Compute Engine',
                    'sku': 'N1 Standard',
                    'cost': 45.67,
                    'usage_quantity': 100,
                    'provider': 'gcp',
                    'project_id': project_id,
                    'location': 'us-central1'
                }
            ]
            
            return cost_data
            
        except Exception as e:
            print(f"Error fetching GCP billing data: {e}")
            return []
    
    def get_project_costs(self, project_id: str, days: int = 30) -> List[Dict]:
        """Get cost breakdown by project.
        
        Args:
            project_id: GCP project ID
            days: Number of days to retrieve
            
        Returns:
            List of project cost data
        """
        start_date = datetime.now() - timedelta(days=days)
        return self.get_cost_data(start_date, datetime.now(), project_id)
    
    def get_billing_accounts(self) -> List[Dict[str, Any]]:
        """List all billing accounts accessible to the project.
        
        Returns:
            List of billing account information
        """
        try:
            accounts = self.billing_client.list_billing_accounts()
            
            billing_accounts = []
            for account in accounts:
                billing_accounts.append({
                    'name': account.name,
                    'display_name': account.display_name,
                    'open': account.open,
                    'provider': 'gcp'
                })
                
            return billing_accounts
            
        except Exception as e:
            print(f"Error fetching GCP billing accounts: {e}")
            return []
    
    def validate_credentials(self) -> bool:
        """Validate GCP credentials and permissions.
        
        Returns:
            True if credentials are valid and Cloud Billing access is available
        """
        try:
            # Test with a simple API call
            if self.billing_account:
                self.billing_client.get_billing_account(
                    name=f"billingAccounts/{self.billing_account}"
                )
            else:
                self.billing_client.list_billing_accounts()
            return True
        except Exception as e:
            print(f"GCP credential validation failed: {e}")
            return False
    
    def get_reservations(self, project_id: str = None) -> List[Dict]:
        """Get committed use discounts for the project.
        
        Args:
            project_id: Optional project ID to filter
            
        Returns:
            List of committed use discount data
        """
        try:
            # Get committed use discounts
            discounts = self.client.list_commitments(
                name=f"billingAccounts/{self.billing_account}"
            ) if self.billing_account else []
            
            reservation_data = []
            for discount in discounts:
                reservation_data.append({
                    'name': discount.name,
                    'plan': discount.plan,
                    'state': discount.state,
                    'amount': discount.amount,
                    'provider': 'gcp'
                })
                
            return reservation_data
            
        except Exception as e:
            print(f"Error fetching GCP reservations: {e}")
            return []