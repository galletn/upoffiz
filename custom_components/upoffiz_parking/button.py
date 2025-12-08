"""Button platform for Upoffiz Parking."""
import logging
from homeassistant.components.button import ButtonEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Upoffiz Parking button."""
    # Get the sensor entity from hass.data
    sensor = hass.data.get('upoffiz_parking', {}).get('sensor')
    
    if sensor:
        async_add_entities([UpoffizParkingRefreshButton(sensor)])
    else:
        _LOGGER.error("Could not find Upoffiz Parking sensor to attach button")


class UpoffizParkingRefreshButton(ButtonEntity):
    """Button to manually refresh Upoffiz Parking data."""

    def __init__(self, sensor):
        """Initialize the button."""
        self._sensor = sensor
        self._attr_name = "Upoffiz Parking Refresh"
        self._attr_icon = "mdi:refresh"
        self._attr_unique_id = "upoffiz_parking_refresh_button"

    async def async_press(self):
        """Handle the button press."""
        _LOGGER.info("Refresh button pressed, updating Upoffiz Parking sensor")
        await self._sensor.async_update(force=True)
        await self._sensor.async_update_ha_state()
