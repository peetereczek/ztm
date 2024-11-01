import re
from freezegun import freeze_time

import aiohttp
import pytest
import asyncio
from aioresponses import aioresponses
from custom_components.ztm.models import (ZTMDepartureData)
from custom_components.ztm.client import ZTMStopClient


@pytest.fixture
def endpoint_pattern():
    return re.compile(r'^https://api\.um\.warszawa\.pl/api/action/dbtimetable_get/.*$')


@pytest.fixture
def api_key():
    return "test_api_key"


@pytest.fixture
def stop_id():
    return 123


@pytest.fixture
def stop_number():
    return "01"


@pytest.fixture
def line():
    return 111


@pytest.fixture
def session():
    return aiohttp.ClientSession()


@pytest.fixture
def ztm_client(session, api_key, stop_id, stop_number, line):
    return ZTMStopClient(session, api_key, stop_id, stop_number, line)


@pytest.mark.asyncio
@freeze_time("2024-01-01 14:05:00")
async def test_get_successful_response(ztm_client, endpoint_pattern):
    # Mock response JSON for a successful response
    mock_json_response = {
        "result": [
            [
                {"key": "kierunek", "value": "Centrum"},
                {"key": "czas", "value": "17:15:00"},
                {"key": "symbol_1", "value": None},
                {"key": "symbol_2", "value": None},
                {"key": "trasa", "value": None},
                {"key": "brygada", "value": None}
            ]
        ]
    }

    with aioresponses() as m:
        m.get(endpoint_pattern, payload=mock_json_response, status=200)

        data = await ztm_client.get()
        assert isinstance(data, ZTMDepartureData)
        assert len(data.departures) == 1
        assert data.departures[0].kierunek == "Centrum"
        assert data.departures[0].czas == "17:15:00"


@pytest.mark.asyncio
async def test_get_handles_non_200_response(ztm_client):
    with aioresponses() as m:
        m.get(ztm_client._endpoint, status=404)

        data = await ztm_client.get()
        assert data is None


@pytest.mark.asyncio
async def test_get_handles_json_parse_error(ztm_client):
    with aioresponses() as m:
        m.get(ztm_client._endpoint, body="Non-JSON response", status=200)

        data = await ztm_client.get()
        assert data is None


@pytest.mark.asyncio
async def test_get_handles_timeout(ztm_client):
    with aioresponses() as m:
        m.get(ztm_client._endpoint, exception=asyncio.TimeoutError)

        data = await ztm_client.get()
        assert data is None


@pytest.mark.asyncio
async def test_get_handles_client_error(ztm_client):
    with aioresponses() as m:
        m.get(ztm_client._endpoint, exception=aiohttp.ClientError)

        data = await ztm_client.get()
        assert data is None


@pytest.mark.asyncio
@freeze_time("2024-01-01 14:05:00")
async def test_get_sorts_departures_correctly(ztm_client, endpoint_pattern):
    # Mock response with multiple departures
    mock_json_response = {
        "result": [
            [{"key": "kierunek", "value": "Centrum"}, {"key": "czas", "value": "14:20:00"}],
            [{"key": "kierunek", "value": "Centrum"}, {"key": "czas", "value": "14:10:00"}],
            [{"key": "kierunek", "value": "Centrum"}, {"key": "czas", "value": "14:30:00"}]
        ]
    }

    with aioresponses() as m:
        m.get(endpoint_pattern, payload=mock_json_response, status=200)

        data = await ztm_client.get()
        assert len(data.departures) == 3
        assert data.departures[0].czas == "14:10:00"
        assert data.departures[1].czas == "14:20:00"
        assert data.departures[2].czas == "14:30:00"


@pytest.mark.asyncio
@freeze_time("2024-01-01 14:05:00")
async def test_get_filters_past_departures(ztm_client, endpoint_pattern):
    # Mock response with a mix of past and future departures
    mock_json_response = {
        "result": [
            [{"key": "kierunek", "value": "Centrum"}, {"key": "czas", "value": "13:50:00"}],  # Past
            [{"key": "kierunek", "value": "Centrum"}, {"key": "czas", "value": "14:10:00"}],  # Future
        ]
    }

    with aioresponses() as m:
        m.get(endpoint_pattern, payload=mock_json_response, status=200)

        data = await ztm_client.get()
        assert len(data.departures) == 1
        assert data.departures[0].czas == "14:10:00"
