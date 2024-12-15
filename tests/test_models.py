import datetime

import pytest
from datetime import timedelta
from homeassistant.util import dt as dt_util
from custom_components.ztm.models import ZTMDepartureDataReading, ZTMDepartureData, ZTMTimeZone
from freezegun import freeze_time


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


@freeze_time("2024-01-01 14:05:00 CET")
def test_dt_property_daytime():
    hour_cet = "14"
    minute = "15"
    # Test dt property for a daytime departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas=f"{hour_cet}:{minute}:00")

    _expected_dt = datetime.datetime(year=2024, month=1, day=1,
                                     hour=int(hour_cet), minute=int(minute), second=0, microsecond=0,
                                     tzinfo=ZTMTimeZone).astimezone(datetime.timezone.utc)

    expected_dt = dt_util.now().replace(hour=_expected_dt.hour, minute=int(minute), second=0, microsecond=0)

    assert reading.dt == expected_dt


@freeze_time("2024-01-01 14:05:00 CET")
def test_dt_property_nighttime():
    minute = "15"
    # Test dt property for a nighttime departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas=f"24:{minute}:00")
    expected_dt = dt_util.now().astimezone(ZTMTimeZone).replace(hour=0, minute=int(minute), second=0,
                                                                microsecond=0) + timedelta(days=1)

    result_dt = reading.dt.astimezone(ZTMTimeZone)

    assert result_dt == expected_dt


@freeze_time("2024-01-01 14:00:00 CET")
def test_time_to_depart_future():
    # Test time_to_depart with a future departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas="14:10:00")
    assert reading.time_to_depart == 10  # Minutes until 14:10 from 14:00


@freeze_time("2024-01-01 14:05:00 CET")
def test_time_to_depart_past():
    # Test time_to_depart with a past departure time
    reading = ZTMDepartureDataReading(kierunek="na", czas="13:50:00")
    assert reading.time_to_depart == 1425


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
