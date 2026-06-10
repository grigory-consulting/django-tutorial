# Django-Tutorial — LocalLibrary

Begleitprojekt zum Django-Einsteiger-Intensiv-Seminar. Eine kleine
Bibliotheksverwaltung (`catalog`) mit Admin, Klassen-basierten Views,
REST-API (DRF), CSV-Import, Mehrsprachigkeit (i18n) und einer
WebSocket-Echtzeit-Demo (`channels`).

## Voraussetzungen

- Python 3.12+
- Optional fuer i18n: GNU `gettext` (`brew install gettext` /
  `apt-get install gettext`)

## Einrichtung

```bash
# 1. Virtuelle Umgebung anlegen und aktivieren
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 2. Abhaengigkeiten installieren
pip install -r requirements.txt

# 3. Datenbank initialisieren
python manage.py migrate

# 4. Admin-Benutzer anlegen
python manage.py createsuperuser

# 5. (optional) Beispieldaten importieren
python manage.py import_books books.csv
```

## Starten

```bash
python manage.py runserver
```

- Anwendung: http://127.0.0.1:8000/de/catalog/
- Admin: http://127.0.0.1:8000/admin/

Die Sprache wird ueber das URL-Praefix gesteuert (`/de/...`, `/en/...`).

## Mehrsprachigkeit (i18n)

Uebersetzungen liegen unter `locale/`. Nach Aenderung an uebersetzbaren
Strings:

```bash
python manage.py makemessages -l en
# locale/en/LC_MESSAGES/django.po uebersetzen
python manage.py compilemessages
```

## Projektstruktur

| Pfad             | Inhalt                                            |
|------------------|---------------------------------------------------|
| `catalog/`       | Hauptanwendung (Models, Views, API, Templates)    |
| `locallibrary/`  | Projekt-Settings, URLs, ASGI/WSGI                 |
| `snake/`         | kleine Zusatz-App                                 |
| `locale/`        | Uebersetzungen                                    |
| `lab*.md`, `*.ipynb` | Seminar-Uebungsmaterial                       |

## Hinweis

`db.sqlite3`, `media/`, `staticfiles/` und `.venv/` sind bewusst nicht
versioniert (siehe `.gitignore`) und werden lokal beim Setup erzeugt.
