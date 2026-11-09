"""Konštanty integrácie Odjazdové tabule v SR."""

DOMAIN = "odjazdove_tabule_sr"

CONF_STOP_ID = "stop_id"
CONF_SECTION = "section"
CONF_LIMIT = "limit"
DEFAULT_SECTION = "ba"
DEFAULT_LIMIT = 10

URL = "https://imhd.sk/"
SIO_PATH = "/rt/sio2"

# Kód mesta (prvá časť adresy imhd.sk/<kod>/...) -> zobrazovaný názov.
# Mestá sa vo formulári ponúkajú podľa súborov zastavky_<kod>.json.
CITY_NAMES = {
    "ba": "Bratislava",
    "ke": "Košice",
    "hc": "Hlohovec",
    "bb": "Banská Bystrica",
    "lm": "Liptovský Mikuláš",
    "mt": "Martin",
    "nr": "Nitra",
    "nz": "Nové Zámky",
    "pn": "Piešťany",
    "tatry": "Poprad-Tatry",
    "pb": "Považská Bystrica",
    "po": "Prešov",
    "pd": "Prievidza",
    "rk": "Ružomberok",
    "se": "Senica",
    "si": "Skalica",
    "sn": "Spišská Nová Ves",
    "tn": "Trenčín",
    "tt": "Trnava",
    "zv": "Zvolen",
    "za": "Žilina",
}
