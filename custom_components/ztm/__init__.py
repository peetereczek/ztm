"""
module ZTM API init
"""
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

from .const import (DOMAIN, CONF_VERSION, VERSION)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
_LOGGER = logging.getLogger("ztm")

successful_startup = True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   PLATFORM MODE - STARTED FROM CONFIGURATION.YAML 'DEVICE_TRACKER/PLATFORM: ICLOUD3 STATEMENT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SETUP PROCESS TO START ICLOUD3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   INTEGRATION MODE - STARTED FROM CONFIGURATION > INTEGRATIONS ENTRY
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SETUP PROCESS TO START ICLOUD3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



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
#-------------------------------------------------------------------------------------------
async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version > 1:
      # This means the user has downgraded from a future version
      return False

    if config_entry.version == 1:

        new = {**config_entry.data}
        config_entry.minor_version < 2:
            # TODO: modify Config Entry data with changes in version 1.2
            pass
        config_entry.minor_version < 3:
            # TODO: modify Config Entry data with changes in version 1.3
            pass

        hass.config_entries.async_update_entry(config_entry, data=new, minor_version=3, version=1)

    _LOGGER.debug("Migration to version %s.%s successful", config_entry.version, config_entry.minor_version)

    return True
