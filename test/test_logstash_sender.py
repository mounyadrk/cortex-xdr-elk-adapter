# test/test_logstash_sender.py
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from logstash_sender import LogstashSender

class FakeSender:
    def __init__(self, config):
        self.sent = []
    def send(self, event):
        self.sent.append(event)
        return True

def test_logstash_send():
    fake_config = {"logstash": {"host": "localhost", "port": 5044}}
    sender = FakeSender(fake_config)

    sample_event = {"event": {"id": "E1", "action": "Test"}}
    result = sender.send(sample_event)

    assert result is True
    assert sender.sent[0]["event"]["id"] == "E1"
