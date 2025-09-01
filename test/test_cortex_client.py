# test/test_cortex_client.py
import os
import sys
import pytest
from unittest.mock import MagicMock
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from cortex_client import CortexXDR 

@pytest.fixture
def fake_config():
    return {
        'cortex': {
            'url': 'https://fake.cortex',
            'api_key': 'FAKE_KEY',
            'api_key_id': 123
        },
        'settings': {
            'initial_lookback_hours': 1
        }
    }

def test_get_alerts(monkeypatch, fake_config):
    # Mock requests.Session.post to return fake alerts
    class FakeResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "reply": {
                    "alerts": [
                        {"alert_id": "A1", "creation_time": int(datetime.utcnow().timestamp()*1000)}
                    ]
                }
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    client = CortexXDR(fake_config)
    monkeypatch.setattr(client.session, "post", fake_post)

    alerts = client.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["alert_id"] == "A1"
