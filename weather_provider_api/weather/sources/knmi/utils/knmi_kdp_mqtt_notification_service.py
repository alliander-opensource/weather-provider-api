from queue import Queue

import paho.mqtt.client as mqtt_client
import paho.mqtt.properties as mqtt_properties
from loguru import logger

# Settings
BROKER_DOMAIN: str = "mqtt.dataplatform.knmi.nl"
CLIENT_ID: str = "..."
TOKEN: str = "..."
