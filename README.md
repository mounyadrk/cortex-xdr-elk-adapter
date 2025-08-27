# cortex-xdr-elk-adapter
# Cortex XDR → ECS → Logstash
Fetch incidents/alerts from Cortex XDR REST API, map to ECS, and ship to Logstash.

## Run
```bash
pip install -r requirements.txt
python -m src.adapters.cortex_xdr
