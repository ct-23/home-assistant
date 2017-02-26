"""
Support KNX switching actuators.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.knx/
"""

import voluptuous as vol

from homeassistant.components.knx import (KNXConfig, KNXFlexibleEntity)
from homeassistant.core import HomeAssistant
from homeassistant.components.light import (Light,
                                            PLATFORM_SCHEMA,
                                            SUPPORT_BRIGHTNESS,
                                            ATTR_BRIGHTNESS)
from homeassistant.const import (CONF_NAME,
                                 CONF_BRIGHTNESS)
import homeassistant.helpers.config_validation as cv

from typing import Optional

ON_OFF_BLOCK = 'on_off'

DEFAULT_NAME = 'KNX Light'
DEPENDENCIES = ['knx']

ga_item = vol.Schema({
    vol.Required("address"): str,
    vol.Optional("state_address"): str,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(ON_OFF_BLOCK): ga_item,
    vol.Optional(CONF_BRIGHTNESS): ga_item,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

DEFAULT_BRIGHTNESS = b'\x00'

SUPPORT_KNX = (SUPPORT_BRIGHTNESS)


def setup_platform(hass: HomeAssistant, config: dict, add_devices, discovery_info=None):
    """Setup the KNX switch platform."""
    add_devices([KNXLight(hass, config)])


class KNXLight(KNXFlexibleEntity, Light):
    """Representation of a KNX light device."""

    def __init__(self, hass: HomeAssistant, config):
        """
        Initialize the device using a config Map.

        KNX relevant Configuration is converted to KNXConfig
        and passed to Parent
        """
        light_settings = {ON_OFF_BLOCK: KNXConfig(config[ON_OFF_BLOCK])}
        if config.get(CONF_BRIGHTNESS) is not None:
            light_settings.update({
                CONF_BRIGHTNESS: KNXConfig(config[CONF_BRIGHTNESS])
            })
        self.__name = config.get(CONF_NAME)
        super().__init__(hass, light_settings)

    @property
    def name(self) -> Optional[str]:
        """Return the name of the entity."""
        return self.__name

    def turn_on(self, **kwargs) -> None:
        """Turn the Light on.

        This either sets brightness or turns on the device.
        """
        if ATTR_BRIGHTNESS in kwargs:
            self.address[CONF_BRIGHTNESS].group_write(kwargs[ATTR_BRIGHTNESS])
        else:
            self.address[ON_OFF_BLOCK].group_write(1)

        if not self.should_poll:
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the switch off.

        This sends a value 1 to the group address of the device
        """
        self.address[ON_OFF_BLOCK].group_write(0)
        if not self.should_poll:
            self.schedule_update_ha_state()

    @property
    def is_on(self):
        """Return True if the value is not 0 is on, else False.

        [0] is the representation from the KNX library.
        """
        return self.raw_state.get(ON_OFF_BLOCK) != [0]

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return int.from_bytes(
            self.raw_state.get(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS),
            byteorder='big'
        )

    @property
    def supported_features(self):
        """Flag supported features."""
        default_features = 0
        supported_features = default_features
        if self.address.get(CONF_BRIGHTNESS) is not None:
            supported_features = supported_features | SUPPORT_BRIGHTNESS

        return supported_features
