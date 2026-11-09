# Odjazdové tabule v SR pre Home Assistant

Vlastná integrácia (custom component), ktorá zobrazuje odchody z virtuálnej
zastávkovej tabule imhd.sk priamo v Home Assistantovi.
Dáta chodia v reálnom čase.

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
- Atribúty odchodu: linka, smer, čas, minúty do odchodu, nástupište.
- Slovenský a anglický preklad rozhrania.

## Inštalácia

Vyžaduje Home Assistant **2024.12** alebo novší.

### Cez HACS (odporúčané)

1. HACS → ⋮ → *Custom repositories*.
2. Vložte `https://github.com/blavak68/odjazdove-tabule-sr`, kategória *Integration*.
3. Nainštalujte *Odjazdové tabule v SR* a reštartujte Home Assistant.

### Ručne

1. Stiahnite archív poslednej verzie zo sekcie *Releases*.
2. Priečinok `custom_components/odjazdove-tabule-sr` skopírujte do
   `<config>/custom_components/`.
3. Reštartujte Home Assistant. Potrebná knižnica `python-socketio` sa
   nainštaluje automaticky.

## Nastavenie

*Nastavenia → Zariadenia a služby → Pridať integráciu → Odjazdové tabule v SR*, 
potom vyberte mesto a zastávku. Počet zobrazených odchodov sa mení v
*Konfigurovať*. Ďalšiu zastávku pridáte tým istým postupom, odstránite ju cez
⋮ pri zázname.

### Zoznamy zastávok

Zoznamy sú súbory `custom_components/odjazdove-tabule-sr/zastavky_<kod>.json`, kde
`<kod>` je kód mesta z adresy imhd.sk (`ba`, `ke`, `tt`, ...). Formulár ponúka
mestá, pre ktoré taký súbor existuje. Ak žiadny nie je, zobrazí sa formulár na
ručné zadanie kódu mesta a ID zastávky (to je parameter `st=` v adrese
tabule, napr. `imhd.sk/ba/online-zastavkova-tabula?st=461`).

## Karta na dashboard

Hotová karta Markdown je v [`examples/markdown_card_1.yaml`](examples/markdown_card1.yaml) pripadne [`examples/markdown_card_2.yaml`](examples/markdown_card2.yaml).
Názov entity upravte podľa názvu zastávky (napr. `sensor.ba_hlavna_stanica`).

Atribút `departures` vyzerá takto:

```yaml
departures:
  - line: '6'
    destination: Stodolova
    time: '2026-11-09T19:00:00+00:00'
    expected: '2026-11-09T19:00:00+00:00'
    scheduled: '2026-11-09T19:00:00+00:00'
    delay_min: 0
    delay_raw: null
    in_minutes: 13
    display: 12 min
    platform: 3472
    realtime: false
    stuck: false
```

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

GitHub Actions (`.github/workflows/validate.yml`) spúšťa Hassfest, validáciu
HACS a kontrolu štýlu kódu. Po nahratí tagu `vX.Y.Z` vytvorí
`release.yml` vydanie s archívom integrácie.

## Licencia

MIT, pozri (LICENSE).
