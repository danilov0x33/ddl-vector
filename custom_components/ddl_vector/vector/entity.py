from anki_vector.messaging.messages_pb2 import BatteryStateResponse

from custom_components.ddl_vector.const import (
    CONF_VECTOR_SERIAL,
    CONF_VECTOR_NAME,
    CONF_VECTOR_GUID,
    CONF_VECTOR_CERT,
    CONF_VECTOR_IP
)


class VectorConfig(object):
    def __init__(self, data=None):
        data = data if data else {}

        self.serial = data.get(CONF_VECTOR_SERIAL)
        self.name = data.get(CONF_VECTOR_NAME)
        self.guid = data.get(CONF_VECTOR_GUID)
        self.cert = data.get(CONF_VECTOR_CERT)
        self.ip = data.get(CONF_VECTOR_IP)

    def get_api_config(self):
        """Getting config for AsyncRobot/Robot config"""
        config = {
            "name": self.name,
            "ip": self.ip,
            "cert_as_str": self.cert,
            "guid": self.guid,
            "cert": ""  # Remove check by none in Robot API
        }

        return config


class VectorData:
    def __init__(self, battery_state: BatteryStateResponse):
        self.battery_state: BatteryStateResponse = battery_state