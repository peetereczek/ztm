import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import homeassistant.util.dt as dt_util


@dataclass
class ZTMDepartureDataReading:
    def __post_init__(self):
        if not re.match(r'^\d{2}:\d{2}:\d{2}$', self.czas):
            raise ValueError("The 'czas' field must be in HH:MM:SS format.")

    symbol_1: Optional[str]
    symbol_2: Optional[str]
    trasa: Optional[str]
    brygada: Optional[str]

    kierunek: str = field(default="na")
    czas: str = field(default="00:00:00")

    @property
    def night_bus(self) -> bool:
        hour, _, _ = self.czas.split(':')

        hour = int(hour)

        if int(hour) >= 24:
            return True

        return False

    @property
    def dt(self):
        hour, minute, _ = self.czas.split(':')

        hour = int(hour)
        minute = int(minute)

        if int(hour) >= 24:
            hour = hour - 24

        now = datetime.now().astimezone()

        try:
            dt = datetime.combine(now.date() + timedelta(days=1 if self.night_bus else 0),
                                  dt_util.parse_time(f"{hour:02d}:{minute:02d}"))

            dt = dt.replace(tzinfo=now.tzinfo)

            return dt
        except Exception:
            return None

    @property
    def time_to_depart(self):
        now = dt_util.now()

        return int((self.dt - now).seconds / 60)


@dataclass
class ZTMDepartureData:
    departures: list[ZTMDepartureDataReading]
