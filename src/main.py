import json
import logging
import time
from pathlib import Path

# -------------------- Imports adaptatifs --------------------
try:
    # Pour l'exécution en tant que module (python -m src.main)
    from .cortex_ecs_mapper import CortexECSMapper
    from .logstash_sender import LogstashSender
except ImportError:
    # Pour l'exécution directe (python src/main.py)
    from cortex_ecs_mapper import CortexECSMapper
    from logstash_sender import LogstashSender

# Cortex client optionnel avec fallback complet
try:
    # Essayer d'importer la vraie classe CortexXDR
    from cortex_client import CortexXDR as CortexClient
except ImportError:
    try:
        # Fallback 1: Essayer MockCortexClient si disponible
        from cortex_client import MockCortexClient as CortexClient
    except ImportError:
        try:
            # Fallback 2: Créer un mock minimal si rien n'existe
            class MockCortexClient:
                def __init__(self, config):
                    self.config = config
                    self.logger = logging.getLogger(__name__)
                
                def get_alerts(self, max_results=100):
                    self.logger.warning("Using fallback mock client - no alerts available")
                    return []
                
                def get_incidents(self, max_results=100):
                    self.logger.warning("Using fallback mock client - no incidents available")
                    return []
            
            CortexClient = MockCortexClient
        except:
            CortexClient = None

# -------------------- Setup Logging --------------------
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

# -------------------- Load Config --------------------
def load_config():
    config_path = Path(__file__).parent.parent / "config/config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)

# -------------------- Fake Logstash Sender --------------------
class FakeLogstashSender:
    def send(self, event):
        # Pretty-print the full ECS event
        import json
        print(json.dumps(event, indent=2))
        return True

# -------------------- Main Function --------------------
def main(test_mode=False):
    setup_logging()
    logger = logging.getLogger(__name__)
    config = load_config()
    
    # Définir les chemins corrects
    base_dir = Path(__file__).parent.parent
    fake_alerts_file = base_dir / "data" / "fake_cortex_alerts.json"
    fake_incidents_file = base_dir / "data" / "fake_cortex_incidents.json"
    
    # ECS mapper
    mapper = CortexECSMapper(base_dir / "config" / "cortex_ecs_mapping.yaml")
    
    if test_mode:
        logstash = FakeLogstashSender()
        events = []
        
        # Charger les alertes fictives
        logger.info(f"Loading fake Cortex alerts from {fake_alerts_file}")
        try:
            with open(fake_alerts_file) as f:
                alerts = json.load(f)
                events.extend(alerts)
                logger.info(f"Loaded {len(alerts)} fake alerts")
        except FileNotFoundError:
            logger.error(f"Fake alerts file not found: {fake_alerts_file}")
            return
        
        # Charger les incidents fictifs (si configuré)
        mode = config.get('settings', {}).get('mode', 'alerts')
        if mode in ['incidents', 'both']:
            logger.info(f"Loading fake Cortex incidents from {fake_incidents_file}")
            try:
                with open(fake_incidents_file) as f:
                    incidents = json.load(f)
                    events.extend(incidents)
                    logger.info(f"Loaded {len(incidents)} fake incidents")
            except FileNotFoundError:
                logger.error(f"Fake incidents file not found: {fake_incidents_file}")
        
        # Traiter tous les événements
        for event in events:
            ecs_event = mapper.map_to_ecs(event)
            logstash.send(ecs_event)
        
        logger.info(f"Finished sending {len(events)} fake events")
        
    else:
        if CortexClient is None:
            logger.error("CortexClient not available. Install or configure it to run in production mode.")
            return

        cortex = CortexClient(config)
        logstash = LogstashSender(config)
        logger.info("Starting Cortex XDR Collector")

        try:
            while True:
                events = []
                
                # Récupérer les alertes
                alerts = cortex.get_alerts()
                logger.info(f"Fetched {len(alerts)} alerts")
                events.extend(alerts)

                # Récupérer les incidents (si configuré)
                mode = config.get('settings', {}).get('mode', 'alerts')
                if mode in ['incidents', 'both']:
                    incidents = cortex.get_incidents()
                    logger.info(f"Fetched {len(incidents)} incidents")
                    events.extend(incidents)

                for event in events:
                    ecs_event = mapper.map_to_ecs(event)
                    if not logstash.send(ecs_event):
                        logger.error(f"Failed to send event: {event.get('alert_id', event.get('incident_id', 'unknown'))}")

                time.sleep(config['settings']['polling_interval'])
        except KeyboardInterrupt:
            logger.info("Shutting down Cortex XDR Collector")

# -------------------- CLI Argument Handling --------------------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cortex XDR to ELK Adapter')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with fake data')
    parser.add_argument('--mode', choices=['alerts', 'incidents', 'both'], 
                       help='Override config mode for testing')
    
    args = parser.parse_args()
    
    main(test_mode=args.test_mode)