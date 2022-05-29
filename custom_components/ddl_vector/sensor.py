import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
)
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    DATA_COORDINATOR
)
from .coordinator import (VectorDataUpdateCoordinator)
from .entity import VectorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    vector_data_coordinator: VectorDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entity = BatterySensor(vector_data_coordinator)
    async_add_entities([entity])

    # platform = entity_platform.async_get_current_platform()
    # platform.async_register_entity_service(
    #     "say_text",
    #     {vol.Required("text"): cv.string},
    #     "perform_say_text",
    # )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class BatterySensor(VectorEntity, SensorEntity):

    device_class = DEVICE_CLASS_BATTERY

    def __init__(self, coordinator: VectorDataUpdateCoordinator):
        super().__init__(coordinator)

        self._attr_unique_id = f"{self.coordinator.device_name}_battery"
        self.entity_id = f"sensor.{self._attr_unique_id}"
        self._attr_name = f"Battery"

    @property
    def extra_state_attributes(self):
        battery_state = self.coordinator.data.get("battery_state")
        if battery_state is None:
            return None

        return {
            "voltage": battery_state.battery_volts,
            "is_charging": battery_state.is_charging
        }

    @property
    def native_value(self):
        if self.coordinator.data and self.coordinator.data.get("battery_state"):
            return self.coordinator.data["battery_state"].battery_level
        else:
            return None

    # async def perform_say_text(self, text) -> None:
    #     _LOGGER.info("SERVICE:")
    #     _LOGGER.info(text)
    #
    #     await self.hass.async_add_executor_job(self.coordinator.vector_robot_sync_api.connect, 30)
    #     try:
    #         await self.hass.async_add_executor_job(self.coordinator.vector_robot_sync_api.behavior.say_text, text)
    #     except Exception as e:
    #         _LOGGER.exception(e)
    #     finally:
    #         await self.hass.async_add_executor_job(self.coordinator.vector_robot_sync_api.disconnect)
