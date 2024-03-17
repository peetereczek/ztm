"""module ztm init"""
import logging
import asyncio

from homeassistant.config_entries         import ConfigEntry
from homeassistant.const                  import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core                   import HomeAssistant
from homeassistant.helpers.typing         import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers                import (area_registry as ar, )
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import homeassistant.util.location  as ha_location_info
import os
import logging

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

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

successful_startup = True