import socket
import ssl
import json
import logging

class LogstashSender:
    def __init__(self, config):
        self.config = config['logstash']
        self.logger = logging.getLogger(__name__)
        self.ssl_context = ssl.create_default_context()
        if not self.config['ssl_verify']:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def send(self, event):
        try:
            # OPTION 1 : Envoi réel à Logstash (décommentez pour production)
            with socket.create_connection(
                (self.config['host'], self.config['port'])
            ) as sock:
                if self.config['use_ssl']:
                    with self.ssl_context.wrap_socket(
                        sock, server_hostname=self.config['host']
                    ) as ssock:
                        ssock.sendall(json.dumps(event).encode('utf-8'))
                else:
                    sock.sendall(json.dumps(event).encode('utf-8'))
            
            # OPTION 2 : Écriture dans fichier (pour debug)
            print(json.dumps(event, indent=2))
            with open("elk_output.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to send to Logstash: {str(e)}")
            return False