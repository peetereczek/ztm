"""Config flow for ZTM API"""
import asyncio
import aiohttp
import async_timeout
import logging

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

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

_LOGGER = logging.getLogger(__name__)

@callback
def configured_accounts(hass):
    """Return tuple of configured entities."""
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
        self._api_key = CONF_API_KEY
        self._line_number = CONF_LINE_NUMBER
        if self._line_number == 'number':
            self._line_number = vol.UNDEFINED
        self._stop_id = CONF_STOP_ID
        if self._stop_id == 'stop_id':
            self._stop_id = vol.UNDEFINED
        self._stop_number = CONF_STOP_NUMBER
        if self._stop_number == 'stop_number':
            self._stop_number = vol.UNDEFINED
        self._request_timeout = REQUEST_TIMEOUT
        self._default_entries = DEFAULT_ENTRIES

    async def async_step_user(self, user_input=None):
        errors = {}
        data_schema = {
            vol.Required("api_key", default=self._api_key): str,
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
            identifier = SENSOR_ID_FORMAT.format(DEFAULT_NAME, self._line_number, self._stop_id, self._stop_number)
            _LOGGER.debug("Read user input %s", identifier)

            try:
                #Test API connection
                _LOGGER.debug("Testing API connection with params: %s", params)
                session = async_get_clientsession(self.hass)
                with async_timeout.timeout(REQUEST_TIMEOUT):
                    req = await session.get(ZTM_ENDPOINT, params=params)
                    json_response = await req.json()
                    _LOGGER.debug("Configuration ZTM API http response code: %s", req.status)
                    _LOGGER.debug("Configuration ZTM API http response text: %s", json_response)
                if req.status == 200:
                    if json_response is not None:
                        if json_response['result'] == "false" and json_response['error'] == "Błędny apikey lub jego brak":
                            errors["base"] = "api_key_invalid"
                            _LOGGER.error("ZTM API UNAUTHORIZED")
                        else:
                            _LOGGER.info("Configuration correct, ZTM API http response code: %s", req.status)
                            CONF_API_KEY = self._api_key
                            CONF_LINE_NUMBER = self._line_number
                            CONF_STOP_ID = self._stop_id
                            CONF_STOP_NUMBER = self._stop_number
                            return self.async_create_entry(
                                title=identifier,
                                data=params,
                                options={
                                    "request_timeout": REQUEST_TIMEOUT,
                                    "default_entries": DEFAULT_ENTRIES
                                    }
                            )
                    else:
                        errors["base"] = "unknown"
                        raise Exception(
                            _LOGGER.error("Received non-JSON data from ZTM API endpoint")
                        )
                elif req.status != 200:
                    errors["base"] = "unknown"
                    raise Exception(
                        _LOGGER.error("ERROR http code: %s", req.status)
                    )
                elif req.status == 400:
                    errors["base"] = "bad_request"
                    raise Exception(
                        _LOGGER.error("BAD REQUEST, http code: %s", req.status)
                    )
                elif req.status == 404:
                    errors["base"] = "cannot_connect"
                    raise Exception(
                        _LOGGER.error("NOT FOUND, http code: %s", req.status)
                    )
            except (asyncio.TimeoutError):
                _LOGGER.error("ZTM API endpoint timeout")
                errors["base"] = "connection_timeout"
            except (aiohttp.ClientSession):
                _LOGGER.error("ZTM API endpoint timeout")
                errors["base"] = "fatal"
            except Exception:
                _LOGGER.error("Connection to ZTM API failed.")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors
        )
    
#TO DO options menu to control number of tracked departures and timeout