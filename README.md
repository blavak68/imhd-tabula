# imhd.sk zastávková tabuľa pre Home Assistant

Vlastná integrácia (custom component), ktorá zobrazuje odchody z virtuálnej
zastávkovej tabule [imhd.sk](https://imhd.sk) priamo v Home Assistantovi.
Dáta chodia v reálnom čase cez socket.io, nie pollingom.

> **Neoficiálny projekt.** Nie je spojený so službou imhd.sk ani s jej
> prevádzkovateľom. Používa rovnaké rozhranie ako webová stránka tabule, ktoré
> nemá zverejnenú dokumentáciu a môže sa kedykoľvek zmeniť. Používajte ho
> ohľaduplne (jedno spojenie na zastávku) a riaďte sa podmienkami služby
> imhd.sk.

## Funkcie

- Pridávanie a odoberanie zastávok z UI (*Nastavenia → Zariadenia a služby*).
- Výber mesta a zastávky zo zoznamu podľa názvu (písaním sa dá vyhľadávať).
- Jeden senzor na zastávku. Stav = čas najbližšieho odchodu, atribúty obsahujú
  zoznam odchodov.
- Atribúty odchodu: linka, smer, čas, minúty do odchodu, nástupište,
  plánovaný čas, meškanie, príznak živých dát a príznak uviaznutého spoja.
- Slovenský a anglický preklad rozhrania.

## Inštalácia

Vyžaduje Home Assistant **2024.12** alebo novší.

### Cez HACS (odporúčané)

1. HACS → ⋮ → *Custom repositories*.
2. Vložte `https://github.com/USER/imhd-tabula`, kategória *Integration*.
3. Nainštalujte *imhd.sk zastávková tabuľa* a reštartujte Home Assistant.

### Ručne

1. Stiahnite archív poslednej verzie zo sekcie *Releases*.
2. Priečinok `custom_components/imhd_tabula` skopírujte do
   `<config>/custom_components/`.
3. Reštartujte Home Assistant. Potrebná knižnica `python-socketio` sa
   nainštaluje automaticky.

## Nastavenie

*Nastavenia → Zariadenia a služby → Pridať integráciu → imhd.sk zastávková
tabuľa*, potom vyberte mesto a zastávku. Počet zobrazených odchodov sa mení v
*Konfigurovať*. Ďalšiu zastávku pridáte tým istým postupom, odstránite ju cez
⋮ pri zázname.

### Zoznamy zastávok

Zoznamy sú súbory `custom_components/imhd_tabula/zastavky_<kod>.json`, kde
`<kod>` je kód mesta z adresy imhd.sk (`ba`, `ke`, `tt`, ...). Formulár ponúka
mestá, pre ktoré taký súbor existuje. Ak žiadny nie je, zobrazí sa formulár na
ručné zadanie kódu mesta a ID zastávky (to je parameter `st=` v adrese
tabule, napr. `imhd.sk/ba/online-zastavkova-tabula?st=3534`).

## Karta na dashboard

Hotová karta Markdown je v [`examples/markdown_card.yaml`](examples/markdown_card.yaml).
Názov entity upravte podľa názvu zastávky (napr. `sensor.kvetoslavov_zastavka`).

Atribút `departures` vyzerá takto:

```yaml
departures:
  - line: '50'
    destination: Kukučínova
    time: '2026-11-07T08:52:36+00:00'
    in_minutes: 1
    display: 1 min
    platform: 1125
    scheduled: '2026-11-07T08:52:36+00:00'
    delay_min: 0
    realtime: true
    stuck: false
```

Údaj o meškaní sa počíta ako rozdiel medzi očakávaným a plánovaným časom
odchodu. Spoje bez sledovania vozidla (cestovný poriadok) majú `realtime:
false`.

## Ako to funguje

Webová stránka tabule sa pripája na `https://imhd.sk/` cez socket.io (cesta
`/rt/sio2`), odošle udalosť `tabStart` s ID zastávky, zoznamom nástupíšť a
kódom mesta a server potom sám posiela udalosť `tabs` s odchodmi. Integrácia
robí to isté jedným spojením na každú pridanú zastávku a po prerušení sa sama
znova pripojí.

## Riešenie problémov

- **Integrácia sa nezobrazuje v zozname:** skontrolujte *Nastavenia → Systém →
  Záznamy* a názov súboru `__init__.py` (dva podčiarkovníky na oboch stranách).
- **Senzor nemá odchody:** zastávka v danej chvíli nemá plánované spoje, alebo
  mesto nemá živé údaje. Vyskúšajte `tools/test_connection.py`.
- **Ikona sa nezobrazuje:** vlastné ikony integrácie z priečinka `brand/`
  podporuje Home Assistant 2026.3 a novší.

## Vývoj

```bash
pip install ruff
ruff check .
```

GitHub Actions (`.github/workflows/validate.yml`) spúšťa Hassfest, validáciu
HACS a kontrolu štýlu kódu. Po nahratí tagu `vX.Y.Z` vytvorí
`release.yml` vydanie s archívom integrácie.

## Licencia

MIT, pozri (LICENSE).
