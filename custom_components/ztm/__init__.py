"""module ztm init"""
from datetime import timedelta
import asyncio
import aiohttp
import async_timeout
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (DOMAIN,
                    DEFAULT_NAME,
                    CONF_ATTRIBUTION,
                    ZTM_ENDPOINT,
                    ZTM_DATA_ID,
                    CONF_API_KEY,
                    CONF_LINES,
                    CONF_LINE_NUMBER,
                    CONF_STOP_ID,
                    CONF_STOP_NUMBER,
                    REQUEST_TIMEOUT,
                    DEFAULT_ENTRIES,
                    UNIT,
                    SENSOR_ID_FORMAT,
                    SENSOR_NAME_FORMAT,
                    CONF_ENTRIES)
from .sensor import ZTMSensor

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info = None) -> None:
    """Set up the platform."""
    websession = async_get_clientsession(hass)
    api_key = config[CONF_API_KEY]
    prepend = config[CONF_NAME]
    entries = config[CONF_ENTRIES]
    lines = []
    for line_config in config.get(CONF_LINES):
        line = line_config[CONF_LINE_NUMBER]
        stop_id = line_config[CONF_STOP_ID]
        stop_number = line_config[CONF_STOP_NUMBER]
        identifier = SENSOR_ID_FORMAT.format(prepend, line, stop_id, stop_number)
        lines.append(ZTMSensor(hass.loop, websession, api_key, line, stop_id,
                               stop_number, identifier, entries))
    try:
        await lines.async_setup()
    except (asyncio.TimeoutError, TimeoutException) as ex:
        raise PlatformNotReady(f"Timeout setting up ZTM API sensor") from ex
    except Exception as ex:
        raise PlatformNotReady(f"Cannot initiate ZTM API sensor") from ex