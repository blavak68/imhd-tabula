from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .client import async_validate
from .const import (
    CITY_NAMES, CONF_LIMIT, CONF_SECTION, CONF_STOP_ID,
    DEFAULT_LIMIT, DOMAIN,
)

BASE = Path(__file__).parent


def _available_cities() -> dict[str, str]:
    cities = {}
    for p in sorted(BASE.glob("zastavky_*.json")):
        code = p.stem.removeprefix("zastavky_")
        cities[code] = CITY_NAMES.get(code, code.upper())
    return cities


def _load_stops(section: str) -> list[dict]:
    with open(BASE / f"zastavky_{section}.json", encoding="utf-8") as f:
        return json.load(f)


def _stop_options(stops: list[dict]) -> list[SelectOptionDict]:
    counts = Counter(s["nazov"] for s in stops)
    return [
        SelectOptionDict(
            value=str(s["kod"]),
            label=f'{s["nazov"]} ({s["kod"]})' if counts[s["nazov"]] > 1 else s["nazov"],
        )
        for s in stops
    ]


class ImhdConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._cities: dict[str, str] | None = None
        self._section: str | None = None

    async def async_step_user(self, user_input=None):
        if self._cities is None:
            self._cities = await self.hass.async_add_executor_job(_available_cities)
        if not self._cities:
            return self.async_abort(reason="no_stops_file")

        if len(self._cities) == 1:
            self._section = next(iter(self._cities))
            return await self.async_step_stop()

        if user_input is not None:
            self._section = user_input[CONF_SECTION]
            return await self.async_step_stop()

        schema = vol.Schema(
            {
                vol.Required(CONF_SECTION): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=c, label=n)
                            for c, n in self._cities.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_stop(self, user_input=None):
        errors = {}
        stops = await self.hass.async_add_executor_job(_load_stops, self._section)
        names = {str(s["kod"]): s["nazov"] for s in stops}

        if user_input is not None:
            code = user_input[CONF_STOP_ID]
            await self.async_set_unique_id(f"{self._section}_{code}")
            self._abort_if_unique_id_configured()
            err = await async_validate(int(code), self._section)
            if err is None:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or names.get(code, code),
                    data={CONF_STOP_ID: int(code), CONF_SECTION: self._section},
                    options={CONF_LIMIT: user_input[CONF_LIMIT]},
                )
            errors["base"] = err

        schema = vol.Schema(
            {
                vol.Required(CONF_STOP_ID): SelectSelector(
                    SelectSelectorConfig(
                        options=_stop_options(stops),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_NAME): str,
                vol.Required(CONF_LIMIT, default=DEFAULT_LIMIT): vol.All(
                    int, vol.Range(1, 50)
                ),
            }
        )
        return self.async_show_form(step_id="stop", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ImhdOptionsFlow()


class ImhdOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_LIMIT, DEFAULT_LIMIT)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_LIMIT, default=current): vol.All(int, vol.Range(1, 50))}
            ),
        )