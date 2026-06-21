# Restauracja pod Sosnami

System zamówień i zarządzania dla restauracji. Trzy panele: zamawianie (kiosk), tablica (podgląd na żywo z efektownymi logami DVD), zarządzanie (admin). Hostowane (może być nieaktualne) na wegiel.pythonanywhere.com

## Strony

| Ścieżka | Opis |
|---|---|
| `/zamow` | Kiosk dla gości — wybór dań, porcji, dodatków gratis, koszyk |
| `/tablica` | Tablica z zamówieniami na żywo + 4 odbijających się logotypów |
| `/manage` | Panel zarządzania — menu, zamówienia, dzwonek, statusy |
| `/bazadanych.json` | Podgląd bazy danych |

## Uruchomienie

```bash
python flask_app.py
```

Serwer na `0.0.0.0:6969`.

## Bouncing DVD Logos (tablica)

4 logotypy odbijające się od krawędzi ekranu z dźwiękami:

| Klawisz | Logo | Dźwięk |
|---|---|---|
| 1 | Rickroll GIF (220×170) | Rick Astley |
| 2 | Logo restauracji (360×198) | Bonk |
| 3 | Metal Pipe (360×32) | Metal Pipe Clang |
| 4 | Kurczaki (240×144) | Kurczaki |

### Skróty klawiszowe

| Klawisz | Funkcja |
|---|---|
| R | pokaż/ukryj wszystkie loga |
| 1-5 | pokaż/ukryj + wycisz konkretne logo |
| 6-0 | tylko wycisz (bez ukrywania) |
| T | race mode (×5 prędkości na 10s) |
| H | pokaż/ukryj licznik uderzeń |
| `` ` `` | pomoc (to okno) |

## API

| Metoda | Ścieżka | Opis |
|---|---|---|
| GET/POST | `/api/orders` | Lista / dodaj zamówienie |
| PUT/DELETE | `/api/orders/<id>` | Zmień status / usuń |
| GET | `/api/menu` | Lista menu |
| POST | `/api/menu` | Dodaj pozycję menu |
| POST | `/api/dzwonek` | Dzwonek (dźwięk na tablicy) |
| GET/POST | `/api/extras` | Dodatki gratis |

## Technologie

- Python + Flask
- HTML/CSS/JavaScript (vanilla)
- Baza danych: JSON (`bazadanych.json`)
- PythonAnywhere-ready (CPU-light, brak `backdrop-filter`)
- w pełni vibe codowane
- never gonna give you up
- never gonna let you down
