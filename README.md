# cortex-xdr-elk-adapter
# Cortex XDR → ECS → Logstash
Fetch incidents/alerts from Cortex XDR REST API, map to ECS, and ship to Logstash.

## Run
```bash
pip install -r requirements.txt
python -m src.adapters.cortex_xdr
```bash
git clone https://github.com/mounyadrk/cortex-xdr-elk-adapter.git
cd cortex-xdr-elk-adapter
pip3 install -r requirements.txt
python3 -m src.adapters.cortex_xdr
