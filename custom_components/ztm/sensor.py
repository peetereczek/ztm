"""
Support for Zarząd Transportu Miejskiego w Warszawie (ZTM) transport data.
For more details about this platform please refer to the documentation at
https://github.com/peetereczek/ztm
"""

from datetime import timedelta, datetime, timezone
import logging
from enum import Enum

import voluptuous as vol
import re

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, CONF_API_KEY
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity

from .client import ZTMStopClient


class ReturnType(str, Enum):
    TIME_TO_DEPART = "TIME_TO_DEPART"
    TIME_OF_DEPARTURE = "TIME_OF_DEPARTURE"


_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Dane dostarcza Miasto Stołeczne Warszawa, api.um.warszawa.pl"

SCAN_INTERVAL = timedelta(minutes=1)

DEFAULT_NAME = "ZTM"
SENSOR_ID_FORMAT = "{} {} from {} {}"
SENSOR_NAME_FORMAT = "{} {} from {} {}"

CONF_LINES = "lines"
CONF_LINE_NUMBER = "number"
CONF_STOP_ID = "stop_id"
CONF_STOP_NUMBER = "stop_number"
CONF_ENTRIES = "entries"
DEFAULT_ENTRIES = 3
CONF_RETURN_TYPE = "return_type"
DEFAULT_RETURN_TYPE = ReturnType.TIME_TO_DEPART.value

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_LINES): vol.All(
            cv.ensure_list,
            [
                {
                    vol.Required(CONF_LINE_NUMBER): cv.string,
                    vol.Required(CONF_STOP_ID): cv.string,
                    vol.Required(CONF_STOP_NUMBER): cv.string,
                }
            ],
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ENTRIES, default=DEFAULT_ENTRIES): cv.positive_int,
        vol.Optional(CONF_RETURN_TYPE, default=DEFAULT_RETURN_TYPE): vol.Coerce(ReturnType)
    }
)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the ZTM platform."""
    session = async_get_clientsession(hass)
    api_key = config[CONF_API_KEY]
    prepend = config[CONF_NAME]
    entries = config[CONF_ENTRIES]
    return_type = config[CONF_RETURN_TYPE]
    lines = []
    for line_config in config.get(CONF_LINES):
        line = line_config[CONF_LINE_NUMBER]
        stop_id = line_config[CONF_STOP_ID]
        stop_number = line_config[CONF_STOP_NUMBER]
        identifier = SENSOR_ID_FORMAT.format(prepend, line, stop_id, stop_number)
        lines.append(
            ZTMSensor(
                hass.loop,
                session,
                api_key,
                line,
                stop_id,
                stop_number,
                identifier,
                entries,
                return_type
            )
        )
    async_add_devices(lines)


class ZTMSensor(Entity):
    def __init__(
            self, loop, session, api_key, line, stop_id, stop_number, identifier, entries, return_type
    ):
        """Initialize the sensor."""
        self._loop = loop
        self._line = line
        self._stop_id = stop_id
        self._stop_number = stop_number
        self._name = identifier
        self._entries = entries
        self._state = None
        self._icon = ""
        self._attributes = {"departures": [], "direction": []}
        self._timetable = []
        self.client = ZTMStopClient(session, api_key, stop_id, stop_number, line)
        self._return_type = return_type

        self._attr_unique_id = identifier

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name  # todo change

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if re.match(r"^(\d{2})$", self._line):
            icon = "mdi:tram"  # regularTRAM
        elif re.match(r"^(\d{3})$", self._line):
            icon = "mdi:bus"  # regularBUS
        elif re.match(r"^N{1}(\d{2})$", self._line):
            icon = "mdi:bus"  # nightBUS
        elif re.match(r"^L{1}([-]{,1})(\d{1,2})$", self._line):
            icon = "mdi:bus"  # localBUS
        elif re.match(r"^S{1}(\d{1,2})$", self._line):
            icon = "mdi:train"  # SKM
        elif re.match(r"^M{1}(\d{1})$", self._line):
            icon = "mdi:train-variant"  # METRO
        return icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "min" if self._return_type == ReturnType.TIME_TO_DEPART.value else ""

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        attribution = CONF_ATTRIBUTION

        self._attributes[ATTR_ATTRIBUTION] = attribution
        return self._attributes

    async def async_update(self):
        departures_data = await self.client.get()

        self._timetable = departures_data.departures

        _LOGGER.debug(
            "Downloaded timetable for line: %s stop: %s-%s",
            self._line,
            self._stop_id,
            self._stop_number,
        )

        _LOGGER.debug("TIMETABLE: %s", self._timetable)

        local_timezone = datetime.now(timezone(timedelta(0))).astimezone().tzinfo

        if departures := self._timetable:
            if self._return_type == ReturnType.TIME_TO_DEPART:
                getter = lambda x: x.time_to_depart
            else:
                getter = lambda x: x.dt.astimezone(local_timezone).strftime("%H:%M")

                self._state = str(getter(departures[0])) if departures[0].time_to_depart <= 60 else "60+"

            self._attributes["departures"] = [getter(x) for x in departures[:self._entries]]

            self._attributes["direction"] = [departures[0].kierunek] * self._entries
        else:
            self._attributes["departures"] = "tommorow"
            self._state = "60+"
