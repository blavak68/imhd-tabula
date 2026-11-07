#!/usr/bin/env python3
"""Otestuje spojenie s imhd.sk a vypíše surové odchody.

    pip install "python-socketio[asyncio_client]" aiohttp
    python tools/test_connection.py ba 3534
"""
from __future__ import annotations

import argparse
import asyncio
import json

import socketio


async def main(section: str, stop_id: int, seconds: int) -> None:
    sio = socketio.AsyncClient(reconnection=False)

    @sio.event
    async def connect():
        print("connected")
        await sio.emit("tabStart", [stop_id, ["*"], section])

    @sio.on("cack")
    async def cack(data):
        print("cack:", data)

    @sio.on("tabs")
    async def tabs(data):
        items = data if isinstance(data, list) else list(data.values())
        types = {d.get("typ") for it in items for d in it.get("tab", [])}
        print("typy odchodov:", types or "žiadne")
        print(json.dumps(data, ensure_ascii=False, indent=1)[:4000])

    await sio.connect(
        "https://imhd.sk/",
        socketio_path="/rt/sio2",
        transports=["websocket"],
        headers={"Origin": "https://imhd.sk"},
    )
    await asyncio.sleep(seconds)
    await sio.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("section", help="kód mesta, napr. ba")
    parser.add_argument("stop_id", type=int, help="ID zastávky")
    parser.add_argument("--seconds", type=int, default=15)
    args = parser.parse_args()
    asyncio.run(main(args.section, args.stop_id, args.seconds))
