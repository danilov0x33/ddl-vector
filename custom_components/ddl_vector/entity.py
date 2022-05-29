from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import VectorDataUpdateCoordinator
from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL
)


class VectorEntity(CoordinatorEntity[VectorDataUpdateCoordinator], Entity):
    """Vector as device"""

    def __init__(self, coordinator: VectorDataUpdateCoordinator):
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vector_config.serial)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=coordinator.vector_config.name,
            sw_version="0.1.0",
            hw_version=coordinator.data["version_state"].os_version
        )
