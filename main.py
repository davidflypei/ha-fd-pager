import logging
import os
import signal
import sys

import helpers.config as cnf
import helpers.info as i
import helpers.mqtt_client as m

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

def main():
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

    # Shutdown
    shutdown(
        mqtt_client = mqtt_client,
        base_topic=config['mqtt']['base_topic'],
        offline=True
    )