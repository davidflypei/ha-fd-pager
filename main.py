import asyncio
import logging
import os
import signal
import sys
from asyncio import sleep
from json import dumps

import httpx
from httpx_sse import aconnect_sse

import helpers.config as cnf
import helpers.info as i
import helpers.mqtt_client as m
import helpers.ha_messages as ha_msgs

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)
LOG_LEVEL = 0
logger.info('Starting FD Pager %s', i.version())

def shutdown(mqtt_client=None, base_topic='fd-pager', offline=False):
    """ Shutdown function to terminate processes and clean up """
    if LOG_LEVEL >= 3:
        logger.info('Shutting down...')
    if mqtt_client is not None and offline:
        mqtt_client.publish(
            topic=f'{base_topic}/status',
            payload='offline',
            qos=1,
            retain=False
        )
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    if LOG_LEVEL >= 3:
        logger.info('All done. Bye!')

def signal_handler(signum, frame):
    """ Signal handler for SIGINT and SIGTERM """
    raise RuntimeError(f'Signal {signum} received.')

async def main():
    # Signal handlers/call back
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Load the configuration file
    if len(sys.argv) == 2:
        config_path = os.path.join(os.path.dirname(__file__), sys.argv[1])
    else:
        config_path = None
    err, msg, config = cnf.load_config(config_path)

    if err != 'success':
        # Error loading configuration file
        logger.critical(msg)
        sys.exit(1)
    # Configuration file loaded successfully
    # Use LOG_LEVEL as a global variable
    global LOG_LEVEL
    # Convert verbosity to a number and store as LOG_LEVEL
    LOG_LEVEL = ['none', 'error', 'warning', 'info', 'debug'].index(config['general']['verbosity'])
    if LOG_LEVEL >= 3:
        logger.info(msg)
    ##################################################################

    mqtt_client = m.MQTTClient(
        broker=config['mqtt']['host'],
        port=config['mqtt']['port'],
        username=config['mqtt']['user'],
        password=config['mqtt']['password'],
        tls_enabled=config['mqtt']['tls_enabled'],
        tls_insecure=config['mqtt']['tls_insecure'],
        ca_cert=config['mqtt']['tls_ca'],
        client_cert=config['mqtt']['tls_cert'],
        client_key=config['mqtt']['tls_keyfile'],
        log_level=LOG_LEVEL,
        logger=logger,
    )

    logger.info("test1")

    # Set Last Will and Testament
    mqtt_client.set_last_will(
        topic=f'{config["mqtt"]["base_topic"]}/status',
        payload="offline",
        qos=1,
        retain=False
    )

    logger.info("test2")

    try:
        mqtt_client.connect()
    except Exception as e:
        logger.critical('Failed to connect to MQTT broker: %s', e)
        sys.exit(1)

    logger.info("test3")
    # Subscribe to Home Assistant status topic
    mqtt_client.subscribe(config['mqtt']['ha_status_topic'], qos=1)
    logger.info("test4")

    # Start the MQTT client loop
    mqtt_client.loop_start()

    logger.info("test5")

    discovery_payload = ha_msgs.pager_discover_payload(config["mqtt"]["base_topic"], {
        "id": "pager1",
        "name": "pager"
    })
    logger.info("test6")
    mqtt_client.publish(
        topic=f'{config["mqtt"]["ha_autodiscovery_topic"]}/device_automation/pager1/config',
        payload=dumps(discovery_payload),
        qos=1,
        retain=False
    )
    logger.info("test7")

    # Publish the initial status
    mqtt_client.publish(
        topic=f'{config["mqtt"]["base_topic"]}/status',
        payload='online',
        qos=1,
        retain=False
    )

    logger.info("test8")

    async with httpx.AsyncClient(timeout=httpx.Timeout(60)) as client:
        url = config['general']['api_url']
        token = config['general']['api_token']
        async with aconnect_sse(client, "GET", f"{url}?api_key={token}") as event_source:
            events = [sse async for sse in event_source.aiter_sse()]
            (sse,) = events
            print(sse.event, sse.json())

    mqtt_client.publish(
        topic=f'{config["mqtt"]["base_topic"]}/pager1',
        payload="page",
        qos=1,
        retain=False
    )

    # Shutdown
    shutdown(
        mqtt_client = mqtt_client,
        base_topic=config['mqtt']['base_topic'],
        offline=True
    )



if __name__ == '__main__':
    # Call main function
    asyncio.run(main())