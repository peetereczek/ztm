import os
import time

from homeassistant                  import config_entries, data_entry_flow
from homeassistant.config_entries   import ConfigEntry as config_entry
from .const                         import DOMAIN
from homeassistant.helpers          import (entity_registry as er, config_validation as cv)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from collections                    import OrderedDict
from homeassistant.data_entry_flow  import FlowHandler, FlowResult

import homeassistant.util.dt as dt_util
import voluptuous as vol
import asyncio
import aiohttp
import async_timeout
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

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY, default=""): cv.string,
        vol.Required(CONF_LINE_NUMBER, default=""): cv.string,
        vol.Required(CONF_STOP_ID, default=""): cv.string,
        vol.Required(CONF_STOP_NUMBER, default=""): cv.string
    }
)
@config_entries.HANDLERS.register(DOMAIN)
class ZtmConfigFlow(config_entries.ConfigFlow, FlowHandler, domain=DOMAIN):
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a user initiated config flow."""

        errors = {}

        if self.hass.data.get(DOMAIN):
            _LOGGER.info(f"ZTM API already set up")
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            line_number = user_input["CONF_LINE_NUMBER"]
            stop_id = user_input["ONF_STOP_ID"]
            stop_number = user_input["CONF_STOP_NUMBER"]
            params = {
                'id': ZTM_DATA_ID,
                'apikey': CONF_API_KEY,
                'busstopId': stop_id,
                'busstopNr': stop_number,
                'line': line_number,
            }
            identifier = SENSOR_ID_FORMAT.format("ZTM", line_number, stop_id, stop_number)

            try:
                websession = async_get_clientsession(self.hass)
                with async_timeout.timeout(REQUEST_TIMEOUT):
                    req = websession.get(ZTM_ENDPOINT, params)

                if req.status != 200:
                    raise Exception(
                        f"Error while setting up ZTM API, http code: {req.status}"
                    )
            except (asyncio.TimeoutError, aiohttp.ClientError):
                _LOGGER.error("Cannot connect to ZTM API endpoint.")
                return self.async_abort(reason="cannot_connect")
            except Exception:
                _LOGGER.error("ZTM API setup error")
                return self.async_abort(reason="unknown")
            else:
                await self.async_set_unique_id(identifier)
                return self.async_create_entry(
                    title=f"{self._line} z przystanku {self._stop_id} {self._stop_number}",
                    data={
                        CONF_API_KEY: CONF_API_KEY,
                        CONF_LINE_NUMBER: self._line_number,
                        CONF_STOP_ID: self._stop_id,
                        CONF_STOP_NUMBER: self._stop_number,
                    }
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(DATA_SCHEMA),
            errors=errors,
        )
    
    async def async_step_finish(self, user_input=None):
        if not user_input:
            return self.async_show_form(step_id="finish")
        return self.async_create_entry(
            title=f"{self._line_number} z przystanku {self._stop_id} {self._stop_number}",
            data={
                CONF_API_KEY: CONF_API_KEY,
                CONF_LINES: self._line_number,
                CONF_STOP_ID: self._stop_id,
                CONF_STOP_NUMBER: self._stop_number,
            }
        )

    async def async_step_import(self, user_input):
        """Import a config flow from configuration."""
        api_key = user_input[CONF_API_KEY]
        line_number = user_input[CONF_LINES]
        stop_id = user_input[CONF_STOP_ID]
        stop_number = user_input[CONF_STOP_NUMBER]
        params = {
                'id': ZTM_DATA_ID,
                'apikey': api_key,
                'busstopId': stop_number,
                'busstopNr': stop_id,
                'line': line_number,
            }

        try:
            websession = async_get_clientsession(self.hass)
            with async_timeout.timeout(REQUEST_TIMEOUT):
                req = websession.get(ZTM_ENDPOINT, params)

            if req.status != 200:
                raise Exception(
                    f"Error while setting up ZTM API, http code: {req.status}"
                )
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Cannot connect to ZTM API endpoint.")
            return self.async_abort(reason="cannot_connect")
        except Exception:
            _LOGGER.error("ZTM API setup error")
            return self.async_abort(reason="unknown")

        return self.async_create_entry(
            title=f"{line_number} z przystanku {stop_id} {stop_number}",
            data={
                CONF_API_KEY: CONF_API_KEY,
                CONF_LINES: line_number,
                CONF_STOP_ID: stop_id,
                CONF_STOP_NUMBER: stop_number,
            }
        )
