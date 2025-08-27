import json, socket, ssl, logging
from datetime import datetime, timezone
from pathlib import Path
import requests, yaml

log = logging.getLogger("cortex_xdr")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SEV_MAP = {"informational":20,"low":30,"medium":60,"med":60,"high":80,"critical":90}

def to_epoch_ms(dt_str): return int(datetime.fromisoformat(dt_str.replace("Z","+00:00")).timestamp()*1000)
def ms_to_iso(ms): return datetime.fromtimestamp(ms/1000, tz=timezone.utc).isoformat()
def sev_num(v): return int(v) if isinstance(v,(int,float)) else SEV_MAP.get(str(v).lower(),60)

def load_yaml(p):
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class LogstashSender:
    def __init__(self, host, port, ssl_enabled=False, ssl_ca=None):
        self.host, self.port, self.ssl_enabled, self.ssl_ca = host, port, ssl_enabled, ssl_ca
    def send_batch(self, docs):
        if not docs: return
        s = socket.create_connection((self.host, self.port), timeout=15)
        try:
            if self.ssl_enabled:
                ctx = ssl.create_default_context(cafile=self.ssl_ca) if self.ssl_ca else ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            for d in docs:
                s.sendall((json.dumps(d, ensure_ascii=False)+"\n").encode("utf-8"))
        finally:
            s.close()

class CortexXDR:
    def __init__(self, cfg):
        self.base = f"https://{cfg['api_fqdn']}/public_api/v1"
        self.headers = {
            "Authorization": cfg["api_key"],
            "x-xdr-auth-id": str(cfg["api_key_id"]),
            "Content-Type": "application/json",
            "Accept": "application/json", "Accept-Encoding": "gzip",
        }
        self.verify = bool(cfg.get("verify_ssl", True))
        self.page = int(cfg.get("page_size", 200))
        self.mode = cfg.get("mode","incidents")
    def _post(self, path, body):
        r = requests.post(f"{self.base}{path}", headers=self.headers, json=body, timeout=60, verify=self.verify)
        r.raise_for_status(); return r.json()
    def _paged(self, path, since_ms, key):
        frm=0; out=[]
        while True:
            body={"request_data":{
                "filters":[{"field":"creation_time","operator":"gte","value":since_ms}],
                "search_from":frm,"search_to":frm+self.page,
                "sort":{"field":"creation_time","keyword":"asc"}}}
            data=self._post(path, body); items=(data.get("reply") or {}).get(key) or []
            out.extend(items)
            if len(items)<self.page: break
            frm+=self.page
        return out
    def get_incidents_since(self, since_ms): return self._paged("/incidents/get_incidents", since_ms, "incidents")
    def get_alerts_since(self, since_ms):    return self._paged("/alerts/get_alerts", since_ms, "alerts")

def apply_mapping(doc, mapping):
    out={}
    for ecs_field, src in mapping["mappings"].items():
        is_array = ecs_field.endswith("[]")
        ecs_key   = ecs_field[:-2] if is_array else ecs_field
        value = doc.get(src)
        if ecs_key=="@timestamp" and value is not None: value = ms_to_iso(value)
        elif ecs_key=="event.severity" and value is not None: value = sev_num(value)
        if value is not None:
            if is_array and not isinstance(value, list): value=[value]
            out[ecs_key]=value
    out["panw.cortex_xdr.raw"]=doc
    return out

def run_once():
    root = Path(__file__).resolve().parents[1]
    cfg = load_yaml(root/"config"/"cortex_xdr.yaml")
    mapping = load_yaml(root/"config"/"ecs_mapping_cortexxdr.yaml")
    since_ms = to_epoch_ms(cfg.get("since","1970-01-01T00:00:00Z"))

    xdr = CortexXDR(cfg)
    docs=[]
    if cfg.get("mode","incidents") in ("incidents","both"):
        incs=xdr.get_incidents_since(since_ms); log.info("Incidents: %d", len(incs))
        docs += [apply_mapping(i, mapping) for i in incs]
    if cfg.get("mode","incidents") in ("alerts","both"):
        alrts=xdr.get_alerts_since(since_ms); log.info("Alerts: %d", len(alrts))
        docs += [apply_mapping(a, mapping) for a in alrts]

    lscfg=cfg["logstash"]
    sender=LogstashSender(lscfg["host"], int(lscfg["port"]),
                          ssl_enabled=bool(lscfg.get("ssl",False)), ssl_ca=lscfg.get("ssl_ca") or None)
    sender.send_batch(docs); log.info("Sent to Logstash: %d docs", len(docs))

if __name__=="__main__": run_once()
