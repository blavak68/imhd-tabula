"""Senzor odchodov z imhd.sk."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from . import ImhdConfigEntry
from .client import ImhdClient
from .const import CITY_NAMES, CONF_LIMIT, DEFAULT_LIMIT, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ImhdConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    limit = entry.options.get(CONF_LIMIT, DEFAULT_LIMIT)
    async_add_entities([DeparturesSensor(entry, entry.runtime_data, limit)])


class DeparturesSensor(SensorEntity):
    """Stav = očakávaný čas najbližšieho odchodu, atribút `departures` = zoznam."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None  # entita sa volá ako zariadenie (názov zastávky)
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:bus-clock"

    def __init__(self, entry: ImhdConfigEntry, client: ImhdClient, limit: int) -> None:
        self._client = client
        self._limit = limit
        self._stop_name = entry.title
        self._attr_unique_id = f"{client.section}_{client.stop_id}_next"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{client.section}_{client.stop_id}")},
            name=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        self._client.listeners.append(self._refresh)
        self.async_on_remove(lambda: self._client.listeners.remove(self._refresh))
        # prepočet "in_minutes" a vyradenie odídených spojov každých 30 s
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._handle_interval, timedelta(seconds=30)
            )
        )

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()

    @callback
    def _handle_interval(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        deps = self._client.departures()
        return datetime.fromisoformat(deps[0]["expected"]) if deps else None

    @property
    def extra_state_attributes(self) -> dict:
        section = self._client.section
        deps = self._client.departures()
        nxt = deps[0] if deps else {}
        return {
            "stop": self._stop_name,
            "stop_id": self._client.stop_id,
            "city": CITY_NAMES.get(section, section.upper()),
            "next_line": nxt.get("line"),
            "next_destination": nxt.get("destination"),
            "next_expected": nxt.get("expected"),
            "next_scheduled": nxt.get("scheduled"),
            "next_delay_min": nxt.get("delay_min"),
            "departures": deps[: self._limit],
        }
