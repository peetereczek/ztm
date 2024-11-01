import asyncio
import logging
from typing import Optional

import aiohttp
import async_timeout

from .models import ZTMDepartureData, ZTMDepartureDataReading

_LOGGER = logging.getLogger(__name__)


class ZTMStopClient:
    def __init__(self, session: aiohttp.ClientSession, api_key: str, stop_id: int, stop_number: str, line: int,
                 timeout: int | None = None):
        self._endpoint = "https://api.um.warszawa.pl/api/action/dbtimetable_get/"
        self._data_id = "e923fa0e-d96c-43f9-ae6e-60518c9f3238"
        self._timeout = timeout or 10
        self._session = session

        self._params = {
            'id': self.id,
            'apikey': api_key,
            'busstopId': stop_id,
            'busstopNr': stop_number,
            'line': line,
        }

    @property
    def id(self):
        return self._data_id

    async def get(self) -> Optional[ZTMDepartureData]:
        try:
            async with self._session as session:
                async with async_timeout.timeout(self._timeout):
                    async with session.get(self._endpoint, params=self._params) as response:
                        if response.status != 200:
                            _LOGGER.error(f"Error fetching data: {response.text}")
                            return None

                        json_response = await response.json()

                        _data = {}
                        _departures = []

                        for reading in json_response["result"]:
                            for entry in reading:
                                _data[entry["key"]] = entry["value"]

                            try:
                                _departures.append(ZTMDepartureDataReading(**_data))
                            except Exception:
                                _LOGGER.warning(f"Data not matching ZTMDepartureDataReading struct: {_data}")

                        return ZTMDepartureData(departures=_departures)

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            _LOGGER.error(f"Cannot connect to ZTM API endpoint. {e.args}")
        except ValueError:
            _LOGGER.error("Received non-JSON data from ZTM API endpoint")
