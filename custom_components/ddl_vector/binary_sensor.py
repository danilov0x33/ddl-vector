import logging

from anki_vector.messaging import protocol
from anki_vector.status import RobotStatus
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DATA_COORDINATOR
)
from .coordinator import (VectorDataUpdateCoordinator)
from .entity import VectorEntity

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES: dict[str, BinarySensorEntityDescription] = {
    "IS_MOTION_DETECTED": BinarySensorEntityDescription(
        key="IS_MOTION_DETECTED",
        device_class=BinarySensorDeviceClass.MOTION,
    )
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    vector_data_coordinator: VectorDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    async_add_entities(
        [
            VectorBinarySensor(vector_data_coordinator, i)
            for i in protocol.RobotStatus.items()
            if i[0] != "ROBOT_STATUS_NONE"
        ]
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class VectorBinarySensor(VectorEntity, BinarySensorEntity):

    def __init__(self, coordinator: VectorDataUpdateCoordinator, status_descriptor):
        super().__init__(coordinator)

        self.status_descriptor = status_descriptor
        self.status_name = status_descriptor[0].replace("ROBOT_STATUS_", "")
        self._attr_unique_id = self.coordinator.device_name + "_" + self.status_name.lower()
        self.entity_id = f"sensor.{self._attr_unique_id}"
        self._attr_name = self.status_name

    @property
    def is_on(self):
        status: RobotStatus = self.coordinator.data.get("status")
        if status:
            return status.__getattribute__("_status") & self.status_descriptor[1] != 0
        else:
            return None

    @property
    def device_class(self):
        sensor_type = BINARY_SENSOR_TYPES.get(self.status_name)
        if sensor_type:
            return sensor_type.device_class
        else:
            return super(VectorBinarySensor, self).device_class



