from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN,
    CONF_VECTOR_CONFIG,
    DATA_COORDINATOR
)
from .coordinator import (VectorDataUpdateCoordinator)
from .vector.entity import VectorConfig

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.CAMERA,
]


async def async_setup(hass: HomeAssistant, hass_config: dict):
    _LOGGER.info("SETUP: \n")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    vector_config = VectorConfig(entry.data[CONF_VECTOR_CONFIG])
    vector_data_coordinator = VectorDataUpdateCoordinator(hass, vector_config)

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: vector_data_coordinator
    }

    await vector_data_coordinator.async_config_entry_first_refresh()

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def perform_say_text(call: ServiceCall):
        await hass.async_add_executor_job(vector_data_coordinator.vector_robot_sync_api.connect, 30)
        try:
            await hass.async_add_executor_job(vector_data_coordinator.vector_robot_sync_api.behavior.say_text, call.data.get('text'))
        except Exception as e:
            _LOGGER.exception(e)
        finally:
            await hass.async_add_executor_job(vector_data_coordinator.vector_robot_sync_api.disconnect)

    hass.services.async_register(DOMAIN, 'say_text', perform_say_text)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
