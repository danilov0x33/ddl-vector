import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from anki_vector import AsyncRobot
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import (
    DOMAIN,
    CONF_VECTOR_SERIAL,
    CONF_VECTOR_NAME,
    CONF_VECTOR_IP,
    CONF_VECTOR_CONFIG,
    CONF_VECTOR_CERT,
    CONF_VECTOR_GUID
)
from .vector.entity import VectorConfig
from .vector.utils import get_vector_cert, get_vector_guid

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    vector_config: VectorConfig = None

    async def async_step_user(self, user_input=None):
        """Init by user via GUI"""

        if user_input is None:
            return self.async_show_form(
                step_id='user',
                data_schema=vol.Schema({
                    vol.Required('method', default='get_guid_and_cert'): vol.In({
                        "get_guid_and_cert": "Get from server with email and password",
                        "write_guid_and_cert": "Write GUID and certificate",
                    })
                }),
                description_placeholders={}
            )

        return self._get_connect_form(user_input)

    async def async_step_get_guid_and_cert(self, user_input=None):
        """ Action for get_guid_and_cert form """

        user_input["method"] = "get_guid_and_cert"
        self.vector_config = VectorConfig(user_input)
        error_message: str = None

        try:
            cert = await self.hass.async_add_executor_job(get_vector_cert, self.vector_config)
            self.vector_config.cert = cert.decode("utf-8")

            guid = await self.hass.async_add_executor_job(get_vector_guid, self.vector_config, user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
            self.vector_config.guid = guid.decode("utf-8")

            error_message = await self._check_connected()
        except Exception as e:
            _LOGGER.exception(e)
            error_message = str(e)

        if error_message:
            return self._get_connect_form(user_input, error_message)

        return self.async_create_entry(title=self.vector_config.name, data={CONF_VECTOR_CONFIG: self.vector_config.__dict__})

    async def async_step_write_guid_and_cert(self, user_input):
        """ Action for write_guid_and_cert form """

        user_input["method"] = "write_guid_and_cert"
        self.vector_config = VectorConfig(user_input)

        if self.vector_config.cert:
            self.vector_config.cert = self.vector_config.cert.replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "")
            self.vector_config.cert = "-----BEGIN CERTIFICATE-----" + self.vector_config.cert.replace(' ', "\n") + "-----END CERTIFICATE-----"

        error_message = await self._check_connected()
        if error_message:
            return self._get_connect_form(user_input, error_message)

        return self.async_create_entry(title=self.vector_config.name, data={CONF_VECTOR_CONFIG: self.vector_config.__dict__})

    def _get_connect_form(self, user_input, error_message=None):
        method = user_input["method"]

        user_input[CONF_VECTOR_IP] = "192.168.3.59"
        user_input[CONF_VECTOR_NAME] = "Vector-F2B1"
        user_input[CONF_VECTOR_SERIAL] = "00508740"

        if method == "get_guid_and_cert":
            return self.async_show_form(
                step_id='get_guid_and_cert',
                data_schema=vol.Schema({
                    vol.Required(schema=CONF_VECTOR_IP, default=user_input.get(CONF_VECTOR_IP) if user_input.get(CONF_VECTOR_IP) else ""): cv.string,
                    vol.Required(schema=CONF_VECTOR_NAME, default=user_input.get(CONF_VECTOR_NAME) if user_input.get(CONF_VECTOR_NAME) else "Vector-XXXX"): cv.string,
                    vol.Required(schema=CONF_VECTOR_SERIAL, default=user_input.get(CONF_VECTOR_SERIAL) if user_input.get(CONF_VECTOR_SERIAL) else ""): cv.string,
                    vol.Required(schema=CONF_EMAIL, default=user_input.get(CONF_EMAIL) if user_input.get(CONF_EMAIL) else ""): cv.string,
                    vol.Required(schema=CONF_PASSWORD, default=user_input.get(CONF_PASSWORD) if user_input.get(CONF_PASSWORD) else ""): cv.string
                }),
                errors=None if error_message is None else {"base": "common"},
                description_placeholders={
                    'common_error_message': error_message
                },
                last_step=True
            )

        if method == "write_guid_and_cert":
            return self.async_show_form(
                step_id='write_guid_and_cert',
                data_schema=vol.Schema({
                    vol.Required(schema=CONF_VECTOR_IP, default=user_input.get(CONF_VECTOR_IP) if user_input.get(CONF_VECTOR_IP) else ""): cv.string,
                    vol.Required(schema=CONF_VECTOR_NAME, default=user_input.get(CONF_VECTOR_NAME) if user_input.get(CONF_VECTOR_NAME) else "Vector-XXXX"): cv.string,
                    vol.Required(schema=CONF_VECTOR_SERIAL, default=user_input.get(CONF_VECTOR_SERIAL) if user_input.get(CONF_VECTOR_SERIAL) else ""): cv.string,
                    vol.Required(schema=CONF_VECTOR_GUID, default=user_input.get(CONF_VECTOR_GUID) if user_input.get(CONF_VECTOR_GUID) else ""): cv.string,
                    vol.Required(schema=CONF_VECTOR_CERT, default=user_input.get(CONF_VECTOR_CERT) if user_input.get(CONF_VECTOR_CERT) else ""): cv.string
                }),
                errors=None if error_message is None else {"base": "common"},
                description_placeholders={
                    'common_error_message': error_message
                },
                last_step=True
            )

    async def _check_connected(self):
        is_connected: bool = False
        vector_robot_async_api = AsyncRobot(
            serial=self.vector_config.serial,
            config=self.vector_config.get_api_config(),
            behavior_activation_timeout=1000,
            cache_animation_lists=False,
            behavior_control_level=None
        )

        try:
            await self.hass.async_add_executor_job(vector_robot_async_api.connect, 30)
            is_connected = True
            return None
        except Exception as e:
            _LOGGER.exception(e)
            return str(e)
        finally:
            if is_connected:
                await self.hass.async_add_executor_job(vector_robot_async_api.disconnect)

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_show_form(
            step_id='init',
            data_schema=vol.Schema({
            })
        )
