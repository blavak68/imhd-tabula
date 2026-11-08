"""imhd.sk zastávková tabuľa."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import ImhdClient
from .const import CONF_SECTION, CONF_STOP_ID

PLATFORMS = ["sensor"]

type ImhdConfigEntry = ConfigEntry[ImhdClient]


async def async_setup_entry(hass: HomeAssistant, entry: ImhdConfigEntry) -> bool:
    client = ImhdClient(entry.data[CONF_STOP_ID], entry.data[CONF_SECTION])
    entry.runtime_data = client
    entry.async_create_background_task(
        hass, client.run(), f"odjazdove_tabule_sr_{client.stop_id}"
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ImhdConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ImhdConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.stop()
    return ok