"""
module ZTM API init
"""
import asyncio
import voluptuous as vol

from homeassistant.config_entries         import ConfigEntry
from homeassistant.const                  import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP, ATTR_ATTRIBUTION, CONF_NAME, CONF_API_KEY
from homeassistant.components.sensor      import PLATFORM_SCHEMA
from homeassistant.core                   import HomeAssistant
from homeassistant.helpers.typing         import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers                import (area_registry as ar)
from homeassistant.util.dt                import utcnow
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import homeassistant.util.location  as ha_location_info
import os
import logging

from .sensor import ZTMSensor

_LOGGER = logging.getLogger(__name__)

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

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_LINES): vol.All(cv.ensure_list, [{
        vol.Required(CONF_LINE_NUMBER): cv.string,
        vol.Required(CONF_STOP_ID): cv.string,
        vol.Required(CONF_STOP_NUMBER): cv.string}]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_ENTRIES, default=DEFAULT_ENTRIES): cv.positive_int,
    })

async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Set up the ZTM platform."""
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
    async_add_devices(lines)

#-------------------------------------------------------------------------------------------
async def async_setup(hass, config):
    if hass.config_entries.async_entries(DOMAIN):
        return True

    if DOMAIN not in config:
        return True
    
    line = config[DOMAIN].get(CONF_LINES)
    if len(line) == 0:
        return True
    
    data = {}
    data[CONF_API_KEY] = config[DOMAIN].get(CONF_API_KEY)
    data[CONF_LINES] = config[DOMAIN].get(CONF_LINES)
    data[CONF_STOP_ID] = config[DOMAIN].get(CONF_STOP_ID)
    data[CONF_STOP_NUMBER] = config[DOMAIN].get(CONF_STOP_NUMBER)

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=data
        )
    )

    return True
#-------------------------------------------------------------------------------------------
async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    """Set up the ZTM API component."""
    hass.data[DOMAIN]["entities"] = set()
    api_key = config_entry.data.get(CONF_API_KEY)
    data = hass.data[DOMAIN][api_key]

    return await data.update(utcnow())
#-------------------------------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]))

    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
#-------------------------------------------------------------------------------------------
async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
