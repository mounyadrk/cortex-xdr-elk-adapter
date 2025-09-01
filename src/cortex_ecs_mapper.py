from datetime import datetime, timezone
import yaml


# Helper to convert milliseconds to ECS-compliant ISO8601 timestamp
def ms_to_iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


class CortexECSMapper:
    def __init__(self, mapping_file=None):
        # If no mapping file is provided, just skip
        if mapping_file:
            with open(mapping_file) as f:
                self.mappings = yaml.safe_load(f).get("field_mappings", [])
        else:
            self.mappings = []

    def map_to_ecs(self, alert):
        ts = (
            ms_to_iso(alert["creation_time"])
            if "creation_time" in alert
            else datetime.now(timezone.utc).isoformat()
        )

        ecs_event = {
            "@timestamp": ts,
            "event": {
                "id": alert.get("alert_id"),
                "action": alert.get("name"),
                "severity": alert.get("severity"),
                "category": self._determine_category(alert),
                "kind": "alert",
                "outcome": "unknown",
            },
            "tags": ["cortex-xdr", "alert"],
            "observer": {
                "product": "Cortex XDR",
                "vendor": "Palo Alto Networks",
                "type": alert.get("category", "XDR"),
            },
        }

        # Only set nested fields if values exist
        if alert.get("source_ip"):
            ecs_event.setdefault("source", {})["ip"] = alert["source_ip"]

        if alert.get("user_name"):
            ecs_event.setdefault("user", {})["name"] = alert["user_name"]

        if alert.get("host_name"):
            ecs_event.setdefault("host", {})["name"] = alert["host_name"]

        # Apply YAML mappings dynamically
        for mapping in self.mappings:
            value = alert
            for key in mapping["cortex_field"].split("."):
                value = value.get(key) if isinstance(value, dict) else None
            if value is not None:
                self._set_nested_field(ecs_event, mapping["ecs_field"], value)

        return ecs_event

    def _determine_category(self, alert):
        """Normalize Cortex categories to ECS categories"""
        cat = alert.get("category", "").lower()
        if cat in ["execution", "process", "script"]:
            return ["intrusion_detection"]
        elif cat in ["network", "connection"]:
            return ["network_traffic"]
        elif cat in ["file", "malware"]:
            return ["malware"]
        return ["unknown"]

    def _set_nested_field(self, obj, field_path, value):
        keys = field_path.split(".")
        for key in keys[:-1]:
            obj = obj.setdefault(key, {})
        obj[keys[-1]] = value
