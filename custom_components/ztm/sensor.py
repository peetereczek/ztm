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

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (ATTR_ATTRIBUTION, CONF_NAME, CONF_API_KEY)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

_LOGGER.warning("WARNING from ZTM BETA sensor")
_LOGGER.error("ERROR from ZTM BETA sensor")