"""
Support for Zarząd Transportu Miejskiego w Warszawie (ZTM) transport data.
For more details about this platform please refer to the documentation at
https://github.com/peetereczek/ztm
"""
import asyncio
from datetime import datetime, timedelta
import logging

import aiohttp
import async_timeout
import voluptuous as vol
import re

from homeassistant.const import (ATTR_ATTRIBUTION, CONF_NAME, CONF_API_KEY)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
import homeassistant.util.dt as dt_util
from .const import (DOMAIN,
                    DEFAULT_NAME,
                    CONF_ATTRIBUTION,
                    ZTM_ENDPOINT,
                    ZTM_DATA_ID,
                    CONF_API_KEY,
                    REQUEST_TIMEOUT,
                    UNIT,
                    SENSOR_ID_FORMAT,
                    SENSOR_NAME_FORMAT,
                    CONF_LINES,
                    CONF_LINE_NUMBER,
                    CONF_STOP_ID,
                    CONF_STOP_NUMBER,
                    CONF_ENTRIES,
                    DEFAULT_ENTRIES)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)

class ZTMSensor(Entity):
    """Implementation of a ZTM sensor."""
    _attr_has_entity_name = True

    def __init__(self, loop, websession, api_key, line, stop_id, stop_number,
                 identifier, entries):
        """Initialize the sensor."""
        self._loop = loop
        self._websession = websession
        self._line = line
        self._stop_id = stop_id
        self._stop_number = stop_number
        self._name = SENSOR_NAME_FORMAT.format("ZTM", line, stop_id, stop_number)
        self._entries = entries
        self._state = None
        self._icon = ''
        self._attributes = {'departures': [], 'direction': []}
        self._timetable = []
        self._timetable_date = None
        self._params = {
            'id': ZTM_DATA_ID,
            'apikey': api_key,
            'busstopId': stop_id,
            'busstopNr': stop_number,
            'line': line,
        }
        self._attr_unique_id = identifier

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):    
        """Icon to use in the frontend, if any."""
        if re.match(r"^(\d{2})$", self._line):
          icon = 'mdi:tram' #regularTRAM
        elif re.match(r"^(\d{3})$", self._line):
          icon = 'mdi:bus' #regularBUS
        elif re.match(r"^N{1}(\d{2})$", self._line):
          icon = 'mdi:bus' #nightBUS
        elif re.match(r"^L{1}([-]{,1})(\d{1,2})$", self._line):
          icon = 'mdi:bus' #localBUS
        elif re.match(r"^S{1}(\d{1,2})$", self._line):
          icon = 'mdi:train' #SKM
        elif re.match(r"^M{1}(\d{1})$", self._line):
          icon = 'mdi:train-variant' #METRO
        return icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return UNIT
        
    @property
    def line(self):
        """Return the line number."""
        return line

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        attribution = CONF_ATTRIBUTION
        if self._timetable_date:
            attribution_date = " dnia {}".format(self._timetable_date)
            attribution = attribution + attribution_date
        self._attributes[ATTR_ATTRIBUTION] = attribution
        return self._attributes
        
    async def async_update(self):
        """Update state."""
        if self.data_is_outdated():
            res = await async_http_request(self._websession,
                                           ZTM_ENDPOINT, self._params)
            if res.get('error', ''):
                _LOGGER.error("Error: %s", res['error'])
            else:
                self._timetable = self.map_results(res.get('response', [0]))
                self._timetable_date = dt_util.now().date()
                _LOGGER.debug("wnloaded timetable for line: %s stop: %s-%s",
                              self._line, self._stop_id, self._stop_number)
                _LOGGER.debug("TIMETABLE: %s", self._timetable)
        # check if there are trains after actual time
        departures = []
        direction = []
        nocny = ''
        now = dt_util.now()
        for entry in self._timetable:
            if entry['czas'][0:2] == '24':
                nocny = '00' + entry['czas'][2:]
            elif entry['czas'][0:2] == '25':
                nocny = '01' + entry['czas'][2:]
            elif entry['czas'][0:2] == '26':
                nocny = '02' + entry['czas'][2:]
            elif entry['czas'][0:2] == '27':
                nocny = '03' + entry['czas'][2:]
            elif entry['czas'][0:2] == '28':
                nocny = '04' + entry['czas'][2:]
            elif entry['czas'][0:2] == '29':
                nocny = '05' + entry['czas'][2:]
            if  nocny != '':
                entry_time = dt_util.parse_time(nocny) 
                _LOGGER.debug("ENTRY: %s", nocny)
                entry_dt = datetime.combine(now.date() + timedelta(days=1), entry_time)
                entry_dt = entry_dt.replace(tzinfo=now.tzinfo)
                _LOGGER.debug("ENTRY_dt: %s", entry_dt)
                _LOGGER.debug("NOW: %s", now)
                if entry_dt > now:
                    time_left = int((entry_dt - now).seconds / 60)
                    _LOGGER.debug("TIME_LEFT: %s", time_left)
                    departures.append(time_left)
                    direction.append(entry['kierunek'])
                    list1, list2 = (list(t) for t in zip(*sorted(zip(departures, direction))))
                    departures = list1
                    direction = list2
#                    if len(departures) == self._entries:
#                        break
            else:
                entry_time = dt_util.parse_time(entry['czas'])
                _LOGGER.debug("ENTRY: %s", entry)
                entry_dt = datetime.combine(now.date(), entry_time)
                entry_dt = entry_dt.replace(tzinfo=now.tzinfo)
                _LOGGER.debug("ENTRY_dt: %s", entry_dt)
                _LOGGER.debug("NOW: %s", now)
                if entry_dt > now:
                    time_left = int((entry_dt - now).seconds / 60)
                    _LOGGER.debug("TIME_LEFT: %s", time_left)
                    departures.append(time_left)
                    direction.append(entry['kierunek'])
                    if len(departures) == self._entries:
                        break
        if departures:
            if departures[0]<=60:
                self._state = departures[0]
            else:
                self._state = '60+'
            self._attributes['departures'] = departures[:self._entries]
            self._attributes['direction'] = direction[:self._entries]
        else:
            self._attributes['departures'] = 'tommorow'
            self._state = '60+'

    def data_is_outdated(self):
        """Check if the internal sensor data is outdated."""
        now = dt_util.now()
        return self._timetable_date != now.date()

    @staticmethod
    def map_results(response):
        """Map all timetable entries to proper {'key': 'value'} struct."""
        return [parse_raw_timetable(row) for row in response['result']]


def parse_raw_timetable(raw_result):
    """Change {'key': 'name','value': 'val'} into {'name': 'val'}."""
    result = {}
    for val in raw_result['values']:
        if val['key'] == 'czas':
            if val['value'] != 'None':
                result[val['key']] = val['value']
            else:
                result[val['key']] = 0
        elif val['key'] == 'kierunek':
            result[val['key']] = val['value']
    _LOGGER.debug("RESULT: %s", result)
    return result


async def async_http_request(websession, uri, params):
    """Perform actual request."""
    try:
        with async_timeout.timeout(REQUEST_TIMEOUT):
            req = await websession.get(uri, params=params)
        if req.status != 200:
            return {'error': req.status}
        json_response = await req.json()
        return {'response': json_response}
    except (asyncio.TimeoutError, aiohttp.ClientError):
        _LOGGER.error("Cannot connect to ZTM API endpoint.")
    except ValueError:
        _LOGGER.error("Received non-JSON data from ZTM API endpoint")
