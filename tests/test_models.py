import pytest
from datetime import datetime, timedelta
from homeassistant.util import dt as dt_util
from custom_components.ztm.models import ZTMDepartureDataReading, ZTMDepartureData


# Mock the current time for consistent testing results
@pytest.fixture
def mock_now(monkeypatch):
    mock_time = datetime(2024, 1, 1, 14, 0, 0)
    monkeypatch.setattr(dt_util, "now", lambda: mock_time)
    yield mock_time


# Tests for ZTMDepartureDataReading ------------------------------------------------------------------------------------

def test_valid_time_format():
    # Valid time format
    reading = ZTMDepartureDataReading(kierunek="na", czas="12:30:00")
    assert reading.czas == "12:30:00"


def test_invalid_time_format():
    # Invalid time format should raise ValueError
    with pytest.raises(ValueError):
        ZTMDepartureDataReading(kierunek="na", czas="123:0:00")


def test_night_bus_property():
    # Test if the night_bus property correctly identifies night buses
    reading = ZTMDepartureDataReading(kierunek="na", czas="24:15:00")
    assert reading.night_bus is True

    reading = ZTMDepartureDataReading(kierunek="na", czas="23:59:00")
    assert reading.night_bus is False


def test_dt_property_daytime(mock_now):
    # Test dt property for a daytime departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas="14:15:00")
    expected_dt = dt_util.now().replace(hour=14, minute=15, second=0, microsecond=0)
    assert reading.dt == expected_dt


def test_dt_property_nighttime(mock_now):
    # Test dt property for a nighttime departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas="24:15:00")
    expected_dt = dt_util.now().replace(hour=0, minute=15, second=0, microsecond=0) + timedelta(days=1)
    assert reading.dt == expected_dt


def test_time_to_depart_future(mock_now):
    # Test time_to_depart with a future departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas="14:10:00")
    assert reading.time_to_depart == 10  # Minutes until 14:10 from 14:00


def test_time_to_depart_past(mock_now):
    # Test time_to_depart with a past departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas="13:50:00")
    assert reading.time_to_depart == 1430  # 24 hours until next day's 13:50


# Tests for ZTMDepartureData -------------------------------------------------------------------------------------------

def test_departures_initialization():
    # Test ZTMDepartureData with a list of ZTMDepartureDataReading instances
    departures = [
        ZTMDepartureDataReading(kierunek="na", czas="12:00:00"),
        ZTMDepartureDataReading(kierunek="na", czas="24:00:00"),
    ]
    data = ZTMDepartureData(departures=departures)
    assert len(data.departures) == 2
    assert data.departures[0].czas == "12:00:00"
    assert data.departures[1].czas == "24:00:00"
