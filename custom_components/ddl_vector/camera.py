import asyncio
import io
import logging

from anki_vector.camera import CameraImage, _convert_to_pillow_image
from anki_vector.events import Events
from anki_vector.messaging import protocol
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
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

    entity = VectorCamera(vector_data_coordinator)
    async_add_entities([entity])


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class VectorCamera(VectorEntity, Camera):
    global_vector_camera = None

    def __init__(self, coordinator: VectorDataUpdateCoordinator):
        super().__init__(coordinator)
        Camera.__init__(self)

        self._attr_unique_id = f"{self.coordinator.device_name}"
        self.entity_id = f"camera.{self._attr_unique_id}"
        self._attr_name = f"Camera"
        self.vector_camera: CameraImage = None
        self.read_image_from_camera_task = False
        #self._supported_features = CameraEntityFeature.ON_OFF
        self.enable_getting_image = False

    async def async_camera_image(self, width: int = None, height: int = None):
        if self.read_image_from_camera_task is False:
            self.coordinator.vector_robot_async_api.camera.init_camera_feed()
            self.coordinator.vector_robot_async_api.events.subscribe(unpack_robot_state,
                                                                     Events.new_camera_image,
                                                                     _on_connection_thread=True)
            self.read_image_from_camera_task = True

        if VectorCamera.global_vector_camera:
            img_byte_arr = io.BytesIO()
            self.enable_getting_image = True
            VectorCamera.global_vector_camera.raw_image.convert("RGB").save(img_byte_arr, format='JPEG')
            self.enable_getting_image = False
            return img_byte_arr.getvalue()

        return None

    # def turn_off(self) -> None:
    #     _LOGGER.info("CAMERA turn_off")
    #
    # def turn_on(self) -> None:
    #     _LOGGER.info("CAMERA turn_on")


async def wait_task(task):
    try:
        await asyncio.wait(task)
    except Exception as e:
        _LOGGER.exception(e)
        task.cancel()


def unpack_robot_state(robot, event_type, event, done=None):
    VectorCamera.global_vector_camera = event.image


async def read_image_from_camera(vector_camera: VectorCamera):
    req = protocol.CameraFeedRequest()
    try:
        async for evt in vector_camera.coordinator.vector_robot_async_api.conn.grpc_interface.CameraFeed(req):
            if vector_camera.enable_getting_image is False:
                image = _convert_to_pillow_image(evt.data)
                vector_camera.vector_camera = CameraImage(image, None, evt.image_id)
    except Exception as e:
        _LOGGER.exception(e)
