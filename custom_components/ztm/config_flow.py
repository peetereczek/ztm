import os
import time

from homeassistant import config_entries, data_entry_flow
from homeassistant.config_entries import ConfigEntry as config_entry
from homeassistant.helpers import entity_registry as er, config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from collections import OrderedDict
from homeassistant.data_entry_flow import FlowHandler, FlowResult
from homeassistant.core import callback

import homeassistant.util.dt as dt_util
import voluptuous as vol
import asyncio
import aiohttp
import async_timeout
import logging
from .const import (
    DOMAIN,
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
    DEFAULT_ENTRIES,
)

_LOGGER = logging.getLogger(__name__)

@callback
def configured_accounts(hass):
    """Return tuple of configured usernames."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if entries:
        _LOGGER.debug("Found existing ZTM configurations %s", entries)
#        return (entry.data[identifier] for entry in entries)
    return ()


@config_entries.HANDLERS.register(DOMAIN)
class ZtmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    data = None
    def __init__(self):
        """Initialize."""
        self._api_key = vol.UNDEFINED
        self._line_number = vol.UNDEFINED
        self._stop_id = vol.UNDEFINED
        self._stop_number = vol.UNDEFINED
        self._request_timeout = REQUEST_TIMEOUT
        self._default_entries = DEFAULT_ENTRIES

    async def async_step_user(self, user_input=None):
        errors = {}
        data_schema = {
            vol.Required("api_key"): str,
            vol.Required("line_number"): str,
            vol.Required("stop_id"): str,
            vol.Required("stop_number"): str,
        }

        if user_input is not None:
            _LOGGER.debug("User input %s", user_input)
            self._api_key = user_input["api_key"]
            self._line_number = user_input["line_number"]
            self._stop_id = user_input["stop_id"]
            self._stop_number = user_input["stop_number"]
            params = {
                'id': ZTM_DATA_ID,
                'apikey': self._api_key,
                'line': self._line_number,
                'busstopId': self._stop_id,
                'busstopNr': self._stop_number
            }
            identifier = SENSOR_ID_FORMAT.format("ZTM", self._line_number, self._stop_id, self._stop_number)
            _LOGGER.debug("Read user input %s", identifier)

            try:
                #Test API connection
                _LOGGER.debug("Testing API connection with params: %s", params)
                session = async_get_clientsession(self.hass)
                with async_timeout.timeout(REQUEST_TIMEOUT):
                    req = await session.get(ZTM_ENDPOINT, params=params)
                if req.status == 200:
                    _LOGGER.info("Configuration correct, ZTM API http response code: %s", req.status)
                    return self.async_create_entry(
                        title=identifier,
                        data=params
                    )
                elif req.status != 200:
                    raise Exception(
                        _LOGGER.error("ERROR http code: %s", req.status)
                    )
                elif req.status == 400:
                    raise Exception(
                        _LOGGER.error("BAD REQUEST, http code: %s", req.status)
                    )
                elif req.status == 401:
                    raise Exception(
                        _LOGGER.error("UNAUTHORIZED, http code: %s", req.status)
                    )
                elif req.status == 404:
                    raise Exception(
                        _LOGGER.error("NOT FOUND, http code: %s", req.status)
                    )
            except (asyncio.TimeoutError, aiohttp.ClientError):
                _LOGGER.error("ZTM API endpoint timeout")
                errors["base"] = "connection_timeout"
            except Exception:
                _LOGGER.error("Connection to ZTM API failed. HTTP session was not opened.")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors
        )

    @callback
    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return ZtmOptionsFlowHandler(config_entry)
    
    async def async_step_finish(self, user_input=None):
        errors = {}
        try:
            return self.async_create_entry(
                title=self.data["line_number"],
                data=self.data
            )
        except Exception:
            _LOGGER.exception("Unexpected exception in ZTM API")
            errors["base"] = "unknown"


class ZtmOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "show_things",
                        default=self.config_entry.options.get("show_things"),
                    ): bool
                }
            ),
        )
