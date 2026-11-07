"""Senzor odchodov z imhd.sk cez socket.io."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval

from . import ImhdConfigEntry
from .client import ImhdClient
# from .const import CONF_LIMIT, DEFAULT_LIMIT, DOMAIN
from .const import CITY_NAMES, CONF_LIMIT, DEFAULT_LIMIT, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ImhdConfigEntry, async_add_entities):
    limit = entry.options.get(CONF_LIMIT, DEFAULT_LIMIT)
    async_add_entities([DeparturesSensor(entry, entry.runtime_data, limit)])


class DeparturesSensor(SensorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None            # <-- bolo "Najbližší odchod"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:bus-clock"

    def __init__(self, entry, client: ImhdClient, limit: int):
        self._client = client
        self._limit = limit
        self._stop_name = entry.title
        self._attr_unique_id = f"{client.section}_{client.stop_id}_next"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{client.section}_{client.stop_id}")}, name=entry.title
        )

    async def async_added_to_hass(self):
        self._client.listeners.append(self._refresh)
        self.async_on_remove(lambda: self._client.listeners.remove(self._refresh))
        self.async_on_remove(
            async_track_time_interval(
                self.hass, lambda _: self._refresh(), timedelta(seconds=30)
            )
        )

    @callback
    def _refresh(self):
        self.async_write_ha_state()

    @property
    def native_value(self):
        deps = self._client.departures()
        return datetime.fromisoformat(deps[0]["time"]) if deps else None

    @property
    def extra_state_attributes(self):
        sec = self._client.section
        return {
            "stop": self._stop_name,
            "stop_id": self._client.stop_id,
            "city": CITY_NAMES.get(sec, sec.upper()),
            "departures": self._client.departures()[: self._limit],
        }