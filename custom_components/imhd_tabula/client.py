"""socket.io klient pre imhd.sk."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import socketio

from .const import SIO_PATH, URL

_LOGGER = logging.getLogger(__name__)
HEADERS = {"Origin": "https://imhd.sk"}


def _items(data) -> list[dict]:
    return data if isinstance(data, list) else list(data.values())


class ImhdClient:
    """Jedno spojenie = jedna zastávka."""

    def __init__(self, stop_id: int, section: str) -> None:
        self.stop_id = stop_id
        self.section = section
        self.platforms: dict[int, list[dict]] = {}
        self.listeners: list = []
        self.sio = socketio.AsyncClient(
            reconnection=True, reconnection_delay=5, reconnection_delay_max=60
        )
        self.sio.on("connect", self._on_connect)
        self.sio.on("cack", self._on_cack)
        self.sio.on("tabs", self._on_tabs)

    async def _on_connect(self):
        await self.sio.emit("tabStart", [self.stop_id, ["*"], self.section])

    async def _on_cack(self, data):
        if data is not True:
            _LOGGER.warning("imhd.sk odmietol spojenie: %s", data)

    async def _on_tabs(self, data):
        for item in _items(data):
            if item.get("zastavka") == self.stop_id:
                self.platforms[item.get("nastupiste")] = item.get("tab", [])
        for cb in list(self.listeners):
            cb()

    def departures(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        out = []
        for platform, tab in self.platforms.items():
            for d in tab:
                ts = d.get("cas")
                if not ts:
                    continue
                when = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                if when < now - timedelta(minutes=1):
                    continue
                out.append(
                    {
                        "line": d.get("linka"),
                        "destination": d.get("konecnaZstr"),
                        "time": when.isoformat(),
                        "in_minutes": max(0, round((when - now).total_seconds() / 60)),
                        "display": d.get("odjazd"),
                        "platform": platform,
                    }
                )
        out.sort(key=lambda x: x["time"])
        return out

    async def run(self):
        """Beží ako background task; pri páde sa pripája znova."""
        while True:
            try:
                await self.sio.connect(
                    URL, socketio_path=SIO_PATH,
                    transports=["websocket"], headers=HEADERS,
                )
                await self.sio.wait()
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("imhd.sk spojenie zlyhalo: %s", err)
            await asyncio.sleep(30)

    async def stop(self):
        if self.sio.connected:
            await self.sio.disconnect()


async def async_validate(stop_id: int, section: str, timeout: int = 15) -> str | None:
    """None = OK, inak kód chyby."""
    ok = asyncio.Event()
    sio = socketio.AsyncClient(reconnection=False)

    async def on_connect():
        await sio.emit("tabStart", [stop_id, ["*"], section])

    async def on_cack(data):
        if data is True:
            ok.set()

    sio.on("connect", on_connect)
    sio.on("cack", on_cack)
    try:
        await sio.connect(URL, socketio_path=SIO_PATH,
                          transports=["websocket"], headers=HEADERS)
        await asyncio.wait_for(ok.wait(), timeout)
        return None
    except Exception:  # noqa: BLE001
        return "cannot_connect"
    finally:
        if sio.connected:
            await sio.disconnect()