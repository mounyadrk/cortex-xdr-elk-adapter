import requests
import logging
from datetime import datetime, timedelta


class CortexXDR:
    def __init__(self, config):
        self.base_url = config['cortex']['url']
        self.api_key = config['cortex']['api_key']
        self.api_key_id = config['cortex']['api_key_id']
        self.mode = config.get('settings', {}).get('mode', 'alerts')  # "alerts", "incidents", or "both"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "x-xdr-auth-id": str(self.api_key_id),
            "Content-Type": "application/json"
        })
        self.logger = logging.getLogger(__name__)
        self.last_fetch_time = datetime.utcnow() - timedelta(
            hours=config['settings'].get('initial_lookback_hours', 24)
        )

    def get_alerts(self, max_results=100):
        """
        Fetch alerts from Cortex XDR API since last_fetch_time.
        """
        url = f"{self.base_url}/public_api/v1/alerts/get_alerts"
        payload = {
            "request_data": {
                "search_from": 0,
                "search_to": max_results,
                "filters": [{
                    "field": "creation_time",
                    "operator": "gte",
                    "value": int(self.last_fetch_time.timestamp() * 1000)
                }]
            }
        }
        try:
            r = self.session.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            alerts = data.get("reply", {}).get("alerts", [])

            if alerts:
                latest_ts = max(a["creation_time"] for a in alerts)
                self.last_fetch_time = datetime.utcfromtimestamp(latest_ts / 1000)

            return alerts

        except Exception as e:
            self.logger.error(f"Failed to fetch alerts: {str(e)}")
            return []

    def get_incidents(self, max_results=100):
        """
        Optional: fetch incidents from Cortex XDR API since last_fetch_time.
        Returns empty list if API endpoint or incidents not used.
        """
        url = f"{self.base_url}/public_api/v1/incidents/get_incidents"
        payload = {
            "request_data": {
                "search_from": 0,
                "search_to": max_results,
                "filters": [{
                    "field": "creation_time",
                    "operator": "gte",
                    "value": int(self.last_fetch_time.timestamp() * 1000)
                }]
            }
        }
        try:
            r = self.session.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            incidents = data.get("reply", {}).get("incidents", [])

            if incidents:
                latest_ts = max(i["creation_time"] for i in incidents)
                self.last_fetch_time = datetime.utcfromtimestamp(latest_ts / 1000)

            return incidents

        except Exception as e:
            self.logger.error(f"Failed to fetch incidents: {str(e)}")
            return []
        
class MockCortexClient:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def get_alerts(self, max_results=100):
        """Simule l'API Cortex avec des données fictives"""
        import json
        from pathlib import Path
        
        try:
            alerts_file = Path(__file__).parent.parent / "data" / "fake_cortex_alerts.json"
            with open(alerts_file) as f:
                alerts = json.load(f)
                return alerts[:max_results]
        except Exception as e:
            self.logger.error(f"Failed to load fake alerts: {str(e)}")
            return []
    
    def get_incidents(self, max_results=100):
        """Simule l'API Cortex avec des données fictives"""
        import json
        from pathlib import Path
        
        try:
            incidents_file = Path(__file__).parent.parent / "data" / "fake_cortex_incidents.json"
            with open(incidents_file) as f:
                incidents = json.load(f)
                return incidents[:max_results]
        except Exception as e:
            self.logger.error(f"Failed to load fake incidents: {str(e)}")
            return []
