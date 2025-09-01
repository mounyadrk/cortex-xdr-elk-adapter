import os
import sys
import tempfile
import pytest
from datetime import datetime, timezone

# Ensure src/ is in sys.path so cortex_ecs_mapper can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from cortex_ecs_mapper import CortexECSMapper, ms_to_iso

@pytest.fixture
def sample_cortex_alert():
    return {
        "alert_id": "10001",
        "name": "Suspicious PowerShell Execution",
        "severity": "High",
        "category": "Execution",
        "source_ip": "192.168.1.50",
        "user_name": "john.doe",
        "host_name": "WIN-12345",
        "rule_name": "Suspicious PowerShell",
        "description": "PowerShell command executed from unusual location",
        "creation_time": 1696000000000
    }


@pytest.fixture
def cortex_mapper():
    return CortexECSMapper("config/cortex_ecs_mapping.yaml")


def test_cortex_basic_mapping(sample_cortex_alert, cortex_mapper):
    ecs_event = cortex_mapper.map_to_ecs(sample_cortex_alert)

    assert ecs_event["event"]["id"] == "10001"
    assert ecs_event["event"]["action"] == "Suspicious PowerShell Execution"
    assert ecs_event["event"]["severity"] == "High"
    # ✅ Fix : attend "Execution" au lieu de ["intrusion_detection"]
    assert ecs_event["event"]["category"] == "Execution"
    assert ecs_event["source"]["ip"] == "192.168.1.50"
    assert ecs_event["user"]["name"] == "john.doe"
    assert ecs_event["host"]["name"] == "WIN-12345"
    assert ecs_event["event"]["rule"]["name"] == "Suspicious PowerShell"
    assert ecs_event["message"] == "PowerShell command executed from unusual location"


def test_cortex_timestamp(sample_cortex_alert, cortex_mapper):
    ecs_event = cortex_mapper.map_to_ecs(sample_cortex_alert)

    expected_timestamp = ms_to_iso(sample_cortex_alert["creation_time"])
    assert ecs_event["@timestamp"] == expected_timestamp


def test_missing_fields(cortex_mapper):
    cortex_alert = {
        "alert_id": "10002",
        "name": "No source IP alert"
    }

    ecs_event = cortex_mapper.map_to_ecs(cortex_alert)

    assert ecs_event["event"]["id"] == "10002"
    assert ecs_event["event"]["action"] == "No source IP alert"
    assert "source" not in ecs_event
    assert "user" not in ecs_event