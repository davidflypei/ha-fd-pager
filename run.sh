#!/usr/bin/with-contenv bashio

echo "Hello world!"

MQTT_HOST=$(bashio::services mqtt "host")
MQTT_USER=$(bashio::services mqtt "username")
MQTT_PASSWORD=$(bashio::services mqtt "password")

pip3 install -r requirements.txt

python3 main.py