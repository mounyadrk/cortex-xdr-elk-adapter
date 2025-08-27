# Cortex XDR → ECS → Logstash

Collect **alerts/incidents from Palo Alto Cortex XDR**, map them to the **Elastic Common Schema (ECS)**, and ship to **Logstash** for ingestion into **Elasticsearch/Kibana**.

---

## Features
- **Automated Collection** – Pulls incidents and/or alerts from the Cortex XDR **REST API**
- **ECS Normalization** – Transforms raw fields to **ECS** for easy search & dashboards
- **Secure Delivery** – Optional **SSL/TLS** when sending to Logstash
- **Config-Driven** – **YAML** configuration & mapping files
- **Resilient** – Supports a `since` cursor to avoid duplicates/gaps

---

## Prerequisites
- **Python 3.8+**
- **Cortex XDR** tenant with **API Key** and **API Key ID**
- **Logstash** (TCP input with `json_lines` codec)
- (Optional) **Elasticsearch/Kibana** reachable from Logstash

---

## Quick Start

### 1) Install dependencies
```bash
pip install -r requirements.txt
