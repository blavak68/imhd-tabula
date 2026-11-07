#!/usr/bin/env python3
"""Vygeneruje zoznamy zastávok zastavky_<mesto>.json pre integráciu.

Použitie:
    python tools/generate_stops.py                 # všetky mestá
    python tools/generate_stops.py ba ke           # len vybrané
    python tools/generate_stops.py --out /config/custom_components/imhd_tabula

Stránka zastávkovej tabule zoznam zastávok vypíše až s parametrom ?st=<ID>,
preto sa najprv cez API nájde ID jednej zastávky pri strede mesta.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://imhd.sk"

# kód mesta: (lat, lng) stredu mesta
CITIES = {
    "ba": (48.1486, 17.1077),      # Bratislava
    "ke": (48.7164, 21.2611),      # Košice
    "hc": (48.4313, 17.8031),      # Hlohovec
    "bb": (48.7363, 19.1462),      # Banská Bystrica
    "lm": (49.0833, 19.6128),      # Liptovský Mikuláš
    "mt": (49.0665, 18.9216),      # Martin
    "nr": (48.3069, 18.0864),      # Nitra
    "nz": (47.9855, 18.1614),      # Nové Zámky
    "pn": (48.5948, 17.8259),      # Piešťany
    "tatry": (49.0614, 20.2980),   # Poprad-Tatry
    "pb": (49.1215, 18.4237),      # Považská Bystrica
    "po": (48.9984, 21.2339),      # Prešov
    "pd": (48.7745, 18.6236),      # Prievidza
    "rk": (49.0746, 19.3053),      # Ružomberok
    "se": (48.6806, 17.3667),      # Senica
    "si": (48.8450, 17.2267),      # Skalica
    "sn": (48.9455, 20.5614),      # Spišská Nová Ves
    "tn": (48.8945, 18.0444),      # Trenčín
    "tt": (48.3774, 17.5883),      # Trnava
    "zv": (48.5748, 19.1531),      # Zvolen
}


def get(url: str, referer: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Referer": referer}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, ""
    except Exception as err:  # noqa: BLE001
        return 0, str(err)


def build(city: str, lat: float, lng: float, outdir: Path) -> tuple[str, int]:
    ref = f"{BASE}/{city}/online-zastavkova-tabula"
    status, body = get(
        f"{BASE}/{city}/api/cepo?op=GetNearestStop&lat={lat}&lng={lng}"
        "&nthDisplay=0&longName=1&ss=1",
        ref,
    )
    try:
        stop_id = json.loads(body)["stops"][0]["id"]
    except Exception:  # noqa: BLE001
        return f"API HTTP {status}, nečakaná odpoveď: {body[:120]!r}", 0

    status, src = get(f"{ref}?st={stop_id}", ref)
    result, seen = [], set()
    for code, name in re.findall(
        r'<option[^>]*\svalue="(\d+)"[^>]*>([^<]+)</option>', src
    ):
        name = html.unescape(name).replace("\xa0", " ").strip()
        if name and code not in seen:
            seen.add(code)
            result.append({"nazov": name, "kod": int(code)})
    if not result:
        return f"stránka HTTP {status}, zoznam zastávok je prázdny", 0

    result.sort(key=lambda x: x["nazov"].lower())
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / f"zastavky_{city}.json", "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=1)
    return "OK", len(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("cities", nargs="*", help="kódy miest (predvolene všetky)")
    parser.add_argument(
        "--out",
        default=str(Path(__file__).parent.parent / "custom_components" / "imhd_tabula"),
        help="cieľový priečinok",
    )
    args = parser.parse_args()

    selected = args.cities or list(CITIES)
    unknown = [c for c in selected if c not in CITIES]
    if unknown:
        parser.error(f"neznáme mestá: {', '.join(unknown)} (doplňte ich do CITIES)")

    print(f'{"mesto":7} {"zastávok":9} stav')
    for city in selected:
        lat, lng = CITIES[city]
        message, count = build(city, lat, lng, Path(args.out))
        print(f"{city:7} {count:<9} {message}")
        time.sleep(1)


if __name__ == "__main__":
    main()
