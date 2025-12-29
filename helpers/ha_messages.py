"""
Helper functions for writing MQTT payloads
"""

import helpers.info as i

def pager_discover_payload(base_topic, meter_config):
    """
    Returns the discovery payload for Home Assistant.
    """
    print("test")

    if 'id' in meter_config:
        print("test")
        meter_id = meter_config['id']
        meter_name = meter_config.get('name', 'Unknown Meter')

    template_payload = {
        "device": {
            "identifiers": f"pager_{meter_id}",
            "name": meter_name
        },
        "origin": {
            "name":f"{base_topic}",
        },
        "automation_type": "trigger",
        "topic": f"{base_topic}/triggers/page",
        "type": "button_short_press",
        "subtype": "button_1"
    }
    return template_payload