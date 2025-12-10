import logging
import asyncio
import json
import datetime
import aiohttp
import requests
from datetime import timedelta
from urllib.parse import urlparse, parse_qs
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.helpers import discovery
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    sensor = UpoffizParkingSensor(config)
    
    # Set SCAN_INTERVAL dynamically to the minimum configured interval
    global SCAN_INTERVAL
    peak_interval = config.get('peak_interval', 30)
    off_peak_interval = config.get('off_peak_interval', 300)
    night_interval = config.get('night_interval', 3600)
    min_interval = min(peak_interval, off_peak_interval, night_interval)
    SCAN_INTERVAL = timedelta(seconds=min_interval)
    _LOGGER.info("SCAN_INTERVAL set to %s seconds (minimum of configured intervals)", min_interval)
    
    async_add_entities([sensor])
    
    # Store sensor in hass.data for button platform access
    if 'upoffiz_parking' not in hass.data:
        hass.data['upoffiz_parking'] = {}
    hass.data['upoffiz_parking']['sensor'] = sensor
    
    # Register the refresh service
    async def handle_refresh(call):
        """Handle the refresh service call."""
        await sensor.async_update(force=True)
        await sensor.async_update_ha_state()
    
    hass.services.async_register('upoffiz_parking', 'refresh', handle_refresh)
    
    # Load button platform
    hass.async_create_task(
        discovery.async_load_platform(hass, 'button', 'upoffiz_parking', {}, config)
    )

class UpoffizParkingSensor(Entity):
    """Representation of the Upoffiz Parking sensor."""

    def __init__(self, config):
        self._state = None
        self._name = "Upoffiz Parking"
        self._username = config.get('username')
        self._password = config.get('password')
        self._attributes = {}
        self._cookie = None
        self._icon = "mdi:parking"
        self._last_update = None
        self._last_peak_update = None
        # Configurable intervals (in seconds)
        self._peak_interval = config.get('peak_interval', 30)  # Default: 30 seconds
        self._off_peak_interval = config.get('off_peak_interval', 300)  # Default: 5 minutes
        self._night_interval = config.get('night_interval', 3600)  # Default: 1 hour
        _LOGGER.info("Upoffiz Parking initialized with intervals - Peak: %ss, Off-peak: %ss, Night: %ss", 
                     self._peak_interval, self._off_peak_interval, self._night_interval)

    @property
    def icon(self):
        return self._icon

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return "Spaces"

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes

    async def async_update(self, force=False):
        from datetime import time

        # Use Home Assistant's timezone-aware datetime
        now = dt_util.now()
        now_time = now.time()

        # Check if we're in peak hours (7:30 - 9:30)
        is_peak_hours = time(7, 30) <= now_time <= time(9, 30)
        is_night_hours = time(22, 0) <= now_time or now_time <= time(6, 0)
        should_update = False

        # Log current time and timezone info
        _LOGGER.info("Update check at %s (local time: %s, TZ: %s)", now, now_time, now.tzinfo)

        if force:
            should_update = True
            _LOGGER.info("Manual refresh triggered")
        elif is_peak_hours:
            # During peak hours, use configured peak interval
            time_since_last = (now - self._last_peak_update).total_seconds() if self._last_peak_update else None
            _LOGGER.info("Peak hours detected! Time since last peak update: %s seconds (interval: %s seconds)", 
                        time_since_last, self._peak_interval)
            if self._last_peak_update is None or (now - self._last_peak_update) >= timedelta(seconds=self._peak_interval):
                should_update = True
                self._last_peak_update = now
            else:
                _LOGGER.info("Peak hours: waiting for %s second interval (still %s seconds to go)", 
                           self._peak_interval, self._peak_interval - time_since_last)
                return
        elif is_night_hours:
            # During night hours, use configured night interval
            time_since_last = (now - self._last_update).total_seconds() if self._last_update else None
            if self._last_update is None or (now - self._last_update) >= timedelta(seconds=self._night_interval):
                should_update = True
            else:
                _LOGGER.info("Night hours: skipping update (interval: %s seconds, time since last: %s seconds)", 
                           self._night_interval, time_since_last)
                return
        else:
            # During off-peak hours, use configured off-peak interval
            time_since_last = (now - self._last_update).total_seconds() if self._last_update else None
            if self._last_update is None or (now - self._last_update) >= timedelta(seconds=self._off_peak_interval):
                should_update = True
            else:
                _LOGGER.info("Off-peak hours: waiting for %s second interval (time since last: %s seconds)", 
                           self._off_peak_interval, time_since_last)
                return

        if not should_update:
            return

        self._last_update = now  # Update the timestamp only when we do an actual update

        _LOGGER.info("Executing update at %s (peak_hours=%s, night_hours=%s, force=%s)", now, is_peak_hours, is_night_hours, force)

        if not self._username or not self._password:
            _LOGGER.error("Missing username or password in configuration file")
        
        # Call the API to retrieve the cookie
        url = 'https://my.upoffiz.be/community/i/organizations/upgrade-estate/signin'
        payload = {
            'username': self._username,
            'password': self._password
        }

        headers = {'Content-Type': 'application/json'}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to retrieve parking data for spot", await response.text())
                    return
                self._cookie = response.cookies.get('connect.sid').value
                self._attributes['cookie'] = self._cookie

        # Call the API to retrieve the access token
        url = 'https://my.upoffiz.be/community/i/organizations/upgrade-estate/user/pages/65709563b7985583b1b82ee2'

        headers = {'Content-Type': 'application/json', 'User-Agent': 'ImAKoffiePot:)'}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, cookies=response.cookies) as response:
                status = response.status
                data = await response.json()
                if response.status != 200:
                    _LOGGER.error("Failed to retrieve parking data for spot", {await response.text()})
                    return

        self._access_url = data['options']['url']

        parsed_url = urlparse(self._access_url)
        query_params = parse_qs(parsed_url.query)

        nm = query_params['nm'][0]
        cnm = query_params['cnm'][0]
        cid = query_params['cid'][0]
        mid = query_params['mid'][0]
        tk = query_params['tk'][0]

        self._attributes['nm'] = nm
        self._attributes['cnm'] = cnm
        self._attributes['cid'] = cid
        self._attributes['mid'] = mid
        self._attributes['tk'] = tk

        url = 'https://visitor-api.upoffiz.be/v1/integration/parking/init/'
        payload = {
            "user-name": nm,
            "user-id": mid,
            "company-name": cnm,
            "company-id": cid,
            "token": tk
        }           

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, json=payload) as response:
                status = response.status
                data = await response.json()
        try:
            self._attributes['visitor parking'] = data['data']['availableGuestSpots']
        except:
            self._attributes['visitor parking'] = "error loading guest spots"
        
        try:
            self._state = data['data']['availableSpots']
        except:
            self._state = data #return all data to at least debug if it is not found
