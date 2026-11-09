"""socket.io klient pre imhd.sk (neoficiálne rozhranie)."""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import socketio

from .const import SIO_PATH, URL

_LOGGER = logging.getLogger(__name__)
HEADERS = {"Origin": "https://imhd.sk"}


def _items(data) -> list[dict]:
    """Server posiela zoznam objektov (jeden na nástupište)."""
    return data if isinstance(data, list) else list(data.values())


class ImhdClient:
    """Jedno socket.io spojenie = jedna zastávka."""

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

    async def _on_connect(self) -> None:
        _LOGGER.debug("imhd.sk: pripojené, zastávka %s", self.stop_id)
        await self.sio.emit("tabStart", [self.stop_id, ["*"], self.section])

    async def _on_cack(self, data) -> None:
        if data is not True:
            _LOGGER.warning("imhd.sk odmietol spojenie: %s", data)

    async def _on_tabs(self, data) -> None:
        for item in _items(data):
            if item.get("zastavka") == self.stop_id:
                self.platforms[item.get("nastupiste")] = item.get("tab", [])
        for callback in list(self.listeners):
            callback()

    def departures(self) -> list[dict]:
        """Zoradené budúce odchody zo všetkých nástupíšť."""
        now = datetime.now(UTC)
        out = []
        for platform, tab in self.platforms.items():
            for dep in tab:
                ts = dep.get("cas")  # očakávaný čas (ms)
                if not ts:
                    continue
                expected = datetime.fromtimestamp(ts / 1000, tz=UTC)
                if expected < now - timedelta(minutes=1):
                    continue
                sched = dep.get("casCP")  # čas podľa cestovného poriadku (ms)
                out.append(
                    {
                        "line": dep.get("linka"),
                        "destination": dep.get("konecnaZstr"),
                        "time": expected.isoformat(),
                        "expected": expected.isoformat(),
                        "scheduled": (
                            datetime.fromtimestamp(sched / 1000, tz=UTC).isoformat()
                            if sched
                            else None
                        ),
                        "delay_min": round((ts - sched) / 60000) if sched else None,
                        "delay_raw": dep.get("casDelta"),
                        "in_minutes": max(0, round((expected - now).total_seconds() / 60)),
                        "display": dep.get("odjazd"),
                        "platform": platform,
                        "realtime": dep.get("typ") != "cp",
                        "stuck": bool(dep.get("uviaznute")),
                    }
                )
        out.sort(key=lambda x: x["expected"])
        return out

    async def run(self) -> None:
        """Beží ako background task; pri páde sa pripája znova."""
        while True:
            try:
                await self.sio.connect(
                    URL,
                    socketio_path=SIO_PATH,
                    transports=["websocket"],
                    headers=HEADERS,
                )
                await self.sio.wait()
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("imhd.sk: spojenie zlyhalo: %s", err)
            await asyncio.sleep(30)

    async def stop(self) -> None:
        if self.sio.connected:
            await self.sio.disconnect()


async def async_validate(stop_id: int, section: str, timeout: int = 15) -> str | None:
    """Vráti None, ak server prijal spojenie, inak kód chyby."""
    ok = asyncio.Event()
    sio = socketio.AsyncClient(reconnection=False)

    async def on_connect() -> None:
        await sio.emit("tabStart", [stop_id, ["*"], section])

    async def on_cack(data) -> None:
        if data is True:
            ok.set()

    sio.on("connect", on_connect)
    sio.on("cack", on_cack)
    try:
        await sio.connect(
            URL, socketio_path=SIO_PATH, transports=["websocket"], headers=HEADERS
        )
        await asyncio.wait_for(ok.wait(), timeout)
        return None
    except Exception:  # noqa: BLE001
        return "cannot_connect"
    finally:
        if sio.connected:
            await sio.disconnect()
