import logging
import asyncio
import json
import datetime
import aiohttp
import requests
from datetime import timedelta
from urllib.parse import urlparse, parse_qs

from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([UpoffizParkingSensor(config)])

class UpoffizParkingSensor(Entity):
    """Representation of the Upoffiz Parking sensor."""

    def __init__(self, config):
        self._state = None
        self._name = "Upoffiz Parking"
        self._username = config.get('username')
        self._password = config.get('password')
        self._attributes = {}
        self._cookie = None

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

    async def async_update(self):
        # Replace the following with your sensor logic
        _LOGGER.info("Updated Upoffiz Parking state to %s", self._state)

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

        headers = {'Content-Type': 'application/json'}
        
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
        self._attributes['visitor parking'] = data['data']['availableGuestSpots']

        self._state = data['data']['availableSpots']
