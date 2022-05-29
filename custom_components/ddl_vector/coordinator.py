import logging
from datetime import timedelta

import anki_vector
from anki_vector.exceptions import VectorAsyncException
from async_timeout import timeout
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN
)
from .vector.entity import VectorConfig

_LOGGER = logging.getLogger(__name__)


class VectorDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, vector_config: VectorConfig) -> None:
        self.vector_config = vector_config
        self.vector_robot_async_api = anki_vector.AsyncRobot(
            serial=vector_config.serial,
            config=vector_config.get_api_config(),
            behavior_activation_timeout=1000,
            cache_animation_lists=False,
            behavior_control_level=None
        )

        self.device_name = vector_config.name.replace('-', '_').lower()

        update_interval = timedelta(seconds=3)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    def _update_data(self) -> dict:
        battery_state = self.vector_robot_async_api.get_battery_state()
        version_state = self.vector_robot_async_api.get_version_state()
        latest_attention_transfer = self.vector_robot_async_api.get_latest_attention_transfer()

        result = {
            "battery_state": battery_state.result(),
            "version_state": version_state.result(),
            "latest_attention_transfer": latest_attention_transfer.result(),
            "status": self.vector_robot_async_api.status
        }

        return result

    async def _async_update_data(self) -> dict:
        try:
            async with timeout(10):
                return await self.hass.async_add_executor_job(self._update_data)
        except Exception as error:
            raise UpdateFailed(f"Can't get vector status: {error}") from error

    async def async_config_entry_first_refresh(self) -> None:
        await self.hass.async_add_executor_job(self.vector_robot_async_api.connect, 30)
        #self.vector_robot_async_api.world.connect_cube()
        _LOGGER.info(f"Vector '{self.vector_config.name}' is connected!")
        return await super().async_config_entry_first_refresh()

    @callback
    def _async_stop_refresh(self, _: Event) -> None:
        _LOGGER.info("DISCONNECTED")

        connected = True
        try:
            thread = self.vector_robot_async_api.conn.thread
        except VectorAsyncException:
            connected = False

        if connected:
            self.vector_robot_async_api.disconnect()

        super(VectorDataUpdateCoordinator, self)._async_stop_refresh()


