# Lab 5 — REST-API, Import, i18n & Produktion

> **Lab 5** der Django-Einsteiger-Intensiv-Schulung (Django 5.2). Baut direkt auf **Lab 4** (`lab4_templates_forms_cbv.md`) auf: durchgehendes Projekt **MDN LocalLibrary**, Projekt `locallibrary`, App `catalog`, mit den Modellen `Author`, `Book`, `BookInstance` und den Templates/CBVs aus Lab 4.
>
> **Reihenfolge:** Schritt 5 von 5 · Vorher: **Lab 4** (Templates, Formulare & CBVs, `lab4_templates_forms_cbv.md`) · Abschluss der Reihe.

## Lernziel

Nach diesem Lab können Sie:

- eine **REST-API mit Django REST Framework (DRF)** aus Serializer, ViewSet und Router aufbauen und mit **Token-Authentifizierung** absichern,
- externe Daten aus einer **CSV-Datei** über einen eigenen **Management-Command** idempotent in die Datenbank importieren (Zusatz: JSON-API mit `requests`),
- den **i18n-Workflow** (`makemessages` → `.po` übersetzen → `compilemessages`) durchführen,
- eine **Produktions-Checkliste** mit `python manage.py check --deploy` anwenden und die wichtigsten `settings.py`-Härtungen vornehmen.

> **Echtzeit (Channels) ist in das optionale [Lab 6](lab6_realtime_checklist.md) ausgelagert.** Dort bauen Sie eine voll lauffähige geteilte Prüfliste mit WebSockets, statt nur ein Grundgerüst nachzuvollziehen.

Vergleichen Sie Ihre Ergebnisse am Ende mit **EXPECTED_RESULTS.md**.

### Voraussetzungen

- Sie haben **Lab 4** (`lab4_templates_forms_cbv.md`) abgeschlossen. Die App `catalog` enthält die Modelle `Author`, `Book`, `BookInstance`, Templates mit Vererbung und die generischen Views (`BookListView`, `BookDetailView`).
- Die virtuelle Umgebung ist aktiv, der Entwicklungsserver lässt sich starten, und in der Datenbank liegen einige Test-Datensätze (z. B. die 3 Bücher aus Lab 2).

```bash
python manage.py runserver
```

- Zur Erinnerung das Datenmodell aus Lab 2 (Auszug — relevant für Serializer und CSV-Import):

```python
# catalog/models.py (bereits vorhanden, Auszug)
class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # __str__ -> "Nachname, Vorname"

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.RESTRICT, null=True)
    summary = models.TextField(blank=True)
    isbn = models.CharField(max_length=13, unique=True)
    # ... language (FK) etc.
```

### Überblick über die Übungen

| Übung | Thema | Charakter |
|---|---|---|
| A | REST-API mit DRF (Serializer, ViewSet, Router) | voll lauffähig |
| B | Token-Authentifizierung (`curl` GET/POST) | voll lauffähig |
| C | CSV-/externe Daten per Management-Command importieren | voll lauffähig |
| D | Mehrsprachigkeit (i18n-Workflow) | geführter Walkthrough |
| E | Produktions-Checkliste (`check --deploy`) | voll lauffähig (Anwendung) |

> Die Übungen A, B, C und E sind **voll lauffähig**: die Befehle liefern konkrete, überprüfbare Ausgaben. Übung D (i18n) ist als **geführter Walkthrough** markiert, weil sie das System-`gettext` voraussetzt; die Tiefe steckt in der Erklärung und im Konzept.

---

## Übung A — REST-API mit DRF (voll lauffähig)

### Aufgabe

Stellen Sie eine JSON-API für das Modell `Book` bereit: Installieren Sie Django REST Framework, ergänzen Sie einen `BookSerializer`, ein `BookViewSet` und registrieren Sie es an einem `DefaultRouter`. Schützen Sie den Endpoint mit `IsAuthenticated` und prüfen Sie, dass ein anonymer Aufruf mit **401** abgewiesen wird.

### Schritt A.1 — DRF installieren und registrieren

```bash
pip install djangorestframework
```

In `locallibrary/settings.py` beide Apps zu `INSTALLED_APPS` hinzufügen — `rest_framework` für das Framework selbst, `rest_framework.authtoken` für die Token-Tabelle aus Übung B:

```python
# locallibrary/settings.py (Auszug)
INSTALLED_APPS = [
    'catalog.apps.CatalogConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
]
```

`rest_framework.authtoken` bringt ein Modell mit (die Token-Tabelle), daher ist eine Migration nötig:

```bash
python manage.py migrate
```

**Erwartet:** Die Migration meldet u. a. `Applying authtoken.0001_initial... OK` (sowie `authtoken.0002...`, `authtoken.0003...`). `python manage.py check` läuft ohne Fehler durch.

### Schritt A.2 — Serializer anlegen

Datei `catalog/serializers.py`:

```python
# catalog/serializers.py
from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'summary', 'isbn']
```

Ein `ModelSerializer` ist das API-Pendant zum `ModelForm`: Er leitet die Felder aus dem Modell ab, übersetzt zwischen `Book`-Objekt und JSON und validiert eingehende Daten. Das FK-Feld `author` wird standardmäßig als **Primärschlüssel** (Integer-ID des Autors) serialisiert.

### Schritt A.3 — ViewSet anlegen

Datei `catalog/api.py`:

```python
# catalog/api.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Book
from .serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
```

Ein `ModelViewSet` bündelt alle CRUD-Aktionen einer Ressource in einer Klasse. `permission_classes = [IsAuthenticated]` legt fest, dass **jeder** Zugriff eine angemeldete bzw. authentifizierte Identität voraussetzt.

### Schritt A.4 — Router in `catalog/urls.py` registrieren

Ergänzen Sie `catalog/urls.py`. Der `DefaultRouter` erzeugt aus dem ViewSet automatisch die Listen- und Detail-URLs:

```python
# catalog/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .api import BookViewSet

# bestehende Routen aus Lab 4
urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    # ... weitere Routen (renew etc.) aus Lab 4
]

# DRF-Router: erzeugt /api/books/ (Liste) und /api/books/<pk>/ (Detail)
router = DefaultRouter()
router.register(r'api/books', BookViewSet)

urlpatterns += [
    path('', include(router.urls)),
]
```

Wichtig zum Pfad: `catalog/urls.py` ist im Projekt unter `path('catalog/', include('catalog.urls'))` eingebunden (siehe Lab 4). Die Router-Route `api/books` liegt damit vollständig unter **`/catalog/api/books/`**.

### Schritt A.5 — Endpoint ohne Authentifizierung testen

```bash
python manage.py runserver
```

In einem zweiten Terminal:

```bash
# macOS / Linux (bash)
curl -i http://127.0.0.1:8000/catalog/api/books/
```

```bat
:: Windows (cmd.exe oder PowerShell) — curl.exe, weil "curl" in PowerShell ein Alias ist
curl.exe -i http://127.0.0.1:8000/catalog/api/books/
```

**Erwartet:**

- HTTP-Status **`401 Unauthorized`**.
- JSON-Body: `{"detail":"Authentication credentials were not provided."}`
- Im Browser zeigt `http://127.0.0.1:8000/catalog/api/books/` die **Browsable API** von DRF (eine HTML-Oberfläche) — auch hier ohne Anmeldung mit dem Hinweis auf fehlende Authentifizierung. Grund: Im Browser greift die Session-Authentifizierung, ein nicht eingeloggter Browser ist ebenfalls anonym.

> Hinweis: Ohne explizite `DEFAULT_AUTHENTICATION_CLASSES` in den Settings verwendet DRF seine Defaults (Session- und Basic-Authentifizierung). Für das tokenbasierte Vorgehen in Übung B ergänzen wir die Authentifizierungsklassen gleich gezielt.

---

## Übung B — Token-Authentifizierung (voll lauffähig)

### Aufgabe

Binden Sie den Token-Endpoint ein, holen Sie für einen Benutzer einen Token (per Command **oder** per POST mit Benutzername/Passwort) und rufen Sie den geschützten Endpoint aus Übung A erfolgreich mit dem `Authorization: Token …`-Header auf — sowohl lesend (GET) als auch schreibend (POST, neues Buch).

> **Windows-Hinweis zu `curl` (gilt für die ganze Übung B):**
> - In PowerShell ist `curl` ein Alias für `Invoke-WebRequest`. Schreiben Sie deshalb immer **`curl.exe`** (das echte curl ist ab Windows 10 enthalten).
> - **Zeilenumbruch im Befehl:** bash nutzt `\`. Schreiben Sie unter Windows den Befehl einfach **in eine Zeile** (am einfachsten und überall korrekt).
> - **Variablen:** bash `TOKEN=…` / `$TOKEN`. In **cmd.exe**: `set TOKEN=…` / `%TOKEN%`. In **PowerShell**: `$TOKEN = "…"` / `$TOKEN`.
> - **JSON im POST-Body:** bash kann `'{...}'` mit einfachen Anführungszeichen. cmd.exe nicht — dort die inneren `"` mit `\"` maskieren. In PowerShell das JSON in eine Variable mit einfachen Anführungszeichen legen und übergeben.

### Schritt B.1 — Token-Authentifizierung aktivieren und Endpoint einbinden

Ergänzen Sie in `locallibrary/settings.py` die DRF-Konfiguration, damit Clients sich per Token ausweisen können (Session bleibt für die Browsable API erhalten):

```python
# locallibrary/settings.py (Auszug)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # Browser
        'rest_framework.authentication.TokenAuthentication',    # Skripte/Clients
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

Binden Sie den fertigen Token-Endpoint `obtain_auth_token` in `catalog/urls.py` ein:

```python
# catalog/urls.py (Ergänzung)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns += [
    path('api/token/', obtain_auth_token, name='api-token'),
]
```

Damit liegt der Token-Endpoint unter **`/catalog/api/token/`**.

### Schritt B.2 — Einen Token besorgen

Sie brauchen einen Benutzer. Falls aus Lab 2 noch kein Superuser existiert, legen Sie einen an:

```bash
python manage.py createsuperuser
# Benutzername z. B. anna, Passwort vergeben
```

**Variante 1 — per Management-Command** (DRF bringt diesen mit):

```bash
python manage.py drf_create_token anna
```

**Erwartet:** Ausgabe in der Form `Generated token <40-stelliger-key> for user anna` (der Key ist ein 40 Zeichen langer Hex-String, bei jedem Benutzer anders).

**Variante 2 — per POST mit Benutzername/Passwort** gegen den Endpoint aus B.1:

```bash
# macOS / Linux (bash)
curl -i -X POST http://127.0.0.1:8000/catalog/api/token/ \
     -d "username=anna&password=IHR_PASSWORT"
```

```bat
:: Windows (cmd.exe oder PowerShell) — eine Zeile
curl.exe -i -X POST http://127.0.0.1:8000/catalog/api/token/ -d "username=anna&password=IHR_PASSWORT"
```

**Erwartet:** Status **`200 OK`** und JSON-Body `{"token":"<40-stelliger-key>"}` — derselbe Token wie aus Variante 1 (ein Benutzer hat genau einen Token, der bei Bedarf erzeugt wird).

Setzen Sie den Token zur Bequemlichkeit in eine Variable (Wert aus der vorherigen Ausgabe einsetzen):

```bash
# macOS / Linux (bash)
TOKEN=<hier-den-40-stelligen-key-einfügen>
```

```bat
:: Windows (cmd.exe)
set TOKEN=<hier-den-40-stelligen-key-einfügen>
```

```powershell
# Windows (PowerShell)
$TOKEN = "<hier-den-40-stelligen-key-einfügen>"
```

### Schritt B.3 — Geschützten Endpoint lesend aufrufen (GET)

```bash
# macOS / Linux (bash)
curl -i -H "Authorization: Token $TOKEN" \
     http://127.0.0.1:8000/catalog/api/books/
```

```bat
:: Windows (cmd.exe)
curl.exe -i -H "Authorization: Token %TOKEN%" http://127.0.0.1:8000/catalog/api/books/
```

```powershell
# Windows (PowerShell)
curl.exe -i -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/catalog/api/books/
```

**Erwartet:**

- Status **`200 OK`**.
- JSON-Array mit den Büchern aus der Datenbank. Bei den Lab-2-Testdaten z. B.:

```text
[
  {"id":1,"title":"Der Hobbit","author":1,"summary":"Bilbo Beutlin auf Abenteuerreise.","isbn":"9780261103283"},
  {"id":2,"title":"Solaris","author":2,"summary":"Erstkontakt mit einem Ozean-Planeten.","isbn":"9780156027601"},
  {"id":3,"title":"The Left Hand of Darkness","author":3,"summary":"Geschlecht und Gesellschaft auf Gethen.","isbn":"9780441478125"}
]
```

(Konkrete IDs, Titel und Autor-IDs hängen von Ihren Daten ab — `author` ist die Integer-ID des verknüpften Autors.)

### Schritt B.4 — Neues Buch anlegen (POST)

Legen Sie ein neues `Book` über die API an. `author` ist die ID eines vorhandenen Autors (z. B. `1`); `isbn` muss eindeutig sein:

```bash
# macOS / Linux (bash) — einfache Anführungszeichen um das JSON
curl -i -X POST -H "Authorization: Token $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title":"Per Anhalter durch die Galaxis","author":1,"summary":"Antwort: 42.","isbn":"9783548234106"}' \
     http://127.0.0.1:8000/catalog/api/books/
```

```bat
:: Windows (cmd.exe) — eine Zeile, innere " mit \" maskiert
curl.exe -i -X POST -H "Authorization: Token %TOKEN%" -H "Content-Type: application/json" -d "{\"title\":\"Per Anhalter durch die Galaxis\",\"author\":1,\"summary\":\"Antwort: 42.\",\"isbn\":\"9783548234106\"}" http://127.0.0.1:8000/catalog/api/books/
```

```powershell
# Windows (PowerShell) — JSON in eine Variable mit einfachen Anführungszeichen legen
$body = '{"title":"Per Anhalter durch die Galaxis","author":1,"summary":"Antwort: 42.","isbn":"9783548234106"}'
curl.exe -i -X POST -H "Authorization: Token $TOKEN" -H "Content-Type: application/json" -d $body http://127.0.0.1:8000/catalog/api/books/
```

**Erwartet:**

- Status **`201 Created`**.
- JSON-Body des angelegten Objekts inklusive der neu vergebenen `id`, z. B.:

```text
{"id":4,"title":"Per Anhalter durch die Galaxis","author":1,"summary":"Antwort: 42.","isbn":"9783548234106"}
```

- Ein erneuter GET (Schritt B.3) listet das neue Buch nun mit. In `/admin/` bzw. `/catalog/books/` taucht es ebenfalls auf.

Gegenprobe ohne bzw. mit falschem Token:

```bash
# macOS / Linux (bash)
curl -i -H "Authorization: Token falscherwert" \
     http://127.0.0.1:8000/catalog/api/books/
```

```bat
:: Windows (cmd.exe oder PowerShell)
curl.exe -i -H "Authorization: Token falscherwert" http://127.0.0.1:8000/catalog/api/books/
```

**Erwartet:** Status **`401 Unauthorized`**, Body `{"detail":"Invalid token."}`.

---

## Übung C — Externe/CSV-Daten importieren (voll lauffähig)

### Aufgabe

Schreiben Sie einen Management-Command `import_books`, der eine CSV-Datei zeilenweise mit dem `csv`-Modul liest und je Zeile Autor und Buch idempotent über `get_or_create` anlegt. Importieren Sie eine Beispiel-CSV und prüfen Sie, dass ein zweiter Lauf keine Dubletten erzeugt.

### Schritt C.1 — Verzeichnisstruktur für den Command

Django erkennt Management-Commands an einem festen Pfad: `<app>/management/commands/<name>.py`. Beide `__init__.py`-Dateien sind nötig, damit Python die Pakete findet.

```bash
# macOS / Linux (bash)
mkdir -p catalog/management/commands
touch catalog/management/__init__.py
touch catalog/management/commands/__init__.py
```

```bat
:: Windows (cmd.exe)
mkdir catalog\management\commands
type nul > catalog\management\__init__.py
type nul > catalog\management\commands\__init__.py
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force catalog\management\commands | Out-Null
New-Item -ItemType File -Force catalog\management\__init__.py | Out-Null
New-Item -ItemType File -Force catalog\management\commands\__init__.py | Out-Null
```

### Schritt C.2 — Beispiel-CSV anlegen

Datei `books.csv` im Projektwurzelverzeichnis (neben `manage.py`). Spalten: `title,isbn,author_last,author_first`.

```text
title,isbn,author_last,author_first
Neuromancer,9780441569595,Gibson,William
Schöne neue Welt,9783596905096,Huxley,Aldous
Foundation,9780553293357,Asimov,Isaac
1984,9780451524935,Orwell,George
```

### Schritt C.3 — Management-Command schreiben

Datei `catalog/management/commands/import_books.py`:

```python
# catalog/management/commands/import_books.py
import csv

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Author, Book


class Command(BaseCommand):
    help = 'Importiert Bücher aus einer CSV-Datei (Spalten: title,isbn,author_last,author_first).'

    def add_arguments(self, parser):
        # Positionsargument: Pfad zur CSV-Datei
        parser.add_argument('csv_path', type=str)

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        created_books = 0
        created_authors = 0

        try:
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Autor idempotent anlegen/holen
                    author, author_new = Author.objects.get_or_create(
                        last_name=row['author_last'].strip(),
                        first_name=row['author_first'].strip(),
                    )
                    if author_new:
                        created_authors += 1

                    # Buch idempotent über die eindeutige ISBN anlegen/holen
                    book, book_new = Book.objects.get_or_create(
                        isbn=row['isbn'].strip(),
                        defaults={
                            'title': row['title'].strip(),
                            'author': author,
                        },
                    )
                    if book_new:
                        created_books += 1
        except FileNotFoundError:
            raise CommandError(f'Datei nicht gefunden: {csv_path}')

        # self.stdout.write nutzt das Command-eigene Ausgabe-Handling (testbar)
        self.stdout.write(self.style.SUCCESS(
            f'Import fertig: {created_books} Bücher und {created_authors} Autor:innen neu angelegt.'
        ))
```

Hinweise:

- `get_or_create` macht den Import **idempotent**: Es sucht erst nach dem eindeutigen Merkmal (hier `isbn` bzw. die Autor-Namenskombination); nur wenn nichts gefunden wird, legt es einen neuen Datensatz mit den `defaults` an. Ein zweiter Lauf erzeugt deshalb keine Dubletten.
- `self.style.SUCCESS(...)` färbt die Ausgabe grün; `self.stdout.write(...)` ist gegenüber `print()` zu bevorzugen, weil es sich in Tests und bei Umleitung sauber verhält.

### Schritt C.4 — Import ausführen

```bash
python manage.py import_books books.csv
```

**Erwartet:**

- Beim **ersten** Lauf (ausgehend von den 3 Lab-2-Büchern, falls die ISBNs neu sind): grüne Meldung `Import fertig: 4 Bücher und 4 Autor:innen neu angelegt.`
- Beim **zweiten** Lauf derselben Datei: `Import fertig: 0 Bücher und 0 Autor:innen neu angelegt.` (Idempotenz — keine Dubletten).
- `python manage.py import_books fehlt.csv` mit nicht existierender Datei → Fehlermeldung `Datei nicht gefunden: fehlt.csv` (sauberer `CommandError`, kein Stacktrace).
- Kontrolle: `/catalog/books/` bzw. `/admin/` zeigen die importierten Titel.

### Schritt C.5 — Zusatz: externe JSON-API statt CSV (nur Snippet)

Statt einer CSV-Datei lässt sich genauso eine externe JSON-API als Quelle anbinden. Das Muster bleibt identisch (`get_or_create`), nur die Datenquelle ändert sich (`requests` ggf. per `pip install requests` nachziehen):

```python
# Snippet — analog im handle() eines Management-Commands einsetzbar
import requests

data = requests.get('https://api.example.com/books').json()
for item in data:
    Book.objects.get_or_create(
        isbn=item['isbn'],
        defaults={'title': item['title']},
    )
```

> Lange oder regelmäßige Importe gehören in einen Management-Command (per Cron/Scheduler) oder einen Hintergrund-Job (z. B. Celery) — **niemals** in einen normalen Web-Request, der sonst im Timeout läuft.

---

## Übung D — Mehrsprachigkeit (geführter Walkthrough)

> **Walkthrough.** Wir gehen den i18n-Workflow gemeinsam Schritt für Schritt durch. `makemessages`/`compilemessages` benötigen das Programm **`gettext`** im System (siehe Hinweis am Ende). Wenn `gettext` lokal fehlt, verfolgen Sie die Schritte mit und ergänzen die Übersetzung später — das Konzept ist auch ohne lauffähige Kompilierung vollständig nachvollziehbar.

### Aufgabe

Aktivieren Sie i18n in den Settings, markieren Sie einen Template-String als übersetzbar, erzeugen Sie die englische `.po`-Datei, tragen Sie die Übersetzung ein und kompilieren Sie sie.

### Schritt D.1 — i18n in den Settings prüfen/aktivieren

Stellen Sie in `locallibrary/settings.py` sicher, dass i18n aktiv ist, die `LocaleMiddleware` eingebunden ist und die verfügbaren Sprachen definiert sind:

```python
# locallibrary/settings.py (Auszug)
USE_I18N = True
LANGUAGE_CODE = 'de'                       # Standardsprache des Projekts
LANGUAGES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',   # <- nach Session, vor Common
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

Die `LocaleMiddleware` ermittelt pro Request die aktive Sprache (u. a. aus dem `Accept-Language`-Header des Browsers). Ihre Position ist wichtig: **nach** der `SessionMiddleware`, **vor** der `CommonMiddleware`.

Legen Sie außerdem das Verzeichnis für Übersetzungen an:

```bash
# macOS / Linux (bash)
mkdir -p locale
```

```bat
:: Windows (cmd.exe oder PowerShell)
mkdir locale
```

### Schritt D.2 — String im Template markieren

Markieren Sie in einem vorhandenen Template (z. B. `catalog/templates/catalog/book_list.html` aus Lab 4) die Überschrift als übersetzbar. Dazu `{% load i18n %}` laden und `{% translate %}` verwenden:

```html+django
{% extends "base_generic.html" %}
{% load i18n %}

{% block content %}
  <h1>{% translate "Bücherliste" %}</h1>
  {# ... restlicher Inhalt unverändert ... #}
{% endblock %}
```

`{% load i18n %}` muss vor der ersten Verwendung von `{% translate %}` stehen. (In Python-Code ist das Pendant `from django.utils.translation import gettext_lazy as _` und dann `_("Bücherliste")`.)

### Schritt D.3 — Übersetzungskatalog erzeugen

```bash
python manage.py makemessages -l en
```

**Erwartet:** Django legt die Datei `locale/en/LC_MESSAGES/django.po` an und meldet `processing locale en`. Darin findet sich ein Eintrag für den markierten String:

```text
#: catalog/templates/catalog/book_list.html
msgid "Bücherliste"
msgstr ""
```

### Schritt D.4 — Übersetzung eintragen

Füllen Sie in `locale/en/LC_MESSAGES/django.po` die `msgstr`-Zeile:

```text
#: catalog/templates/catalog/book_list.html
msgid "Bücherliste"
msgstr "Book list"
```

### Schritt D.5 — Katalog kompilieren

```bash
python manage.py compilemessages
```

**Erwartet:**

- Django erzeugt die binäre Datei `locale/en/LC_MESSAGES/django.mo` (Meldung `processing file django.po in …/locale/en/LC_MESSAGES`).
- Ruft ein Browser die Buchliste mit englischer Spracheinstellung auf (z. B. per Header `curl -H "Accept-Language: en" http://127.0.0.1:8000/catalog/books/`), erscheint die Überschrift als **„Book list"**; mit deutscher Einstellung weiterhin **„Bücherliste"**.

> **Hinweis (gettext):** `makemessages`/`compilemessages` rufen die GNU-`gettext`-Werkzeuge auf. Fehlt `gettext`, bricht der Befehl mit `CommandError: Can't find msguniq / msgfmt. Make sure you have GNU gettext tools 0.15 or newer installed.` ab. Installation: macOS `brew install gettext`, Debian/Ubuntu `sudo apt-get install gettext`, Windows über die vorkompilierten gettext-Binaries (im Doku-Verweis genannt).

---

## Übung E — Produktions-Checkliste (voll lauffähig, Anwendung)

### Aufgabe

Führen Sie Djangos eingebaute Deployment-Prüfung aus, gehen Sie die Warnungen durch und nehmen Sie die wichtigsten Härtungen vor. Beobachten Sie konkret, dass mit `DEBUG = False` die statischen Dateien nicht mehr automatisch ausgeliefert werden, und leiten Sie daraus den `collectstatic`-Schritt ab.

### Schritt E.1 — `check --deploy` ausführen

```bash
python manage.py check --deploy
```

**Erwartet:** Eine Liste von **Warnungen** (`WARNINGS:`) mit `security.W…`-Codes — bei einem frischen Entwicklungs-Setup typischerweise u. a.:

```text
?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting...
?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True...
?: (security.W009) Your SECRET_KEY has less than 50 characters... (bzw. unsicher)
?: (security.W012) SESSION_COOKIE_SECURE is not set to True...
?: (security.W016) You have 'django.middleware.csrf.CsrfViewMiddleware' ... CSRF_COOKIE_SECURE is not set to True...
?: (security.W018) You should not have DEBUG set to True in deployment.
System check identified some issues:
...
```

Jede Warnung benennt genau eine Einstellung, die für Produktion zu setzen ist. Die konkrete Liste/Anzahl hängt von Ihren aktuellen Settings ab.

### Schritt E.2 — `DEBUG = False` + `ALLOWED_HOSTS` setzen und Statik-Effekt beobachten

Setzen Sie in `locallibrary/settings.py`:

```python
# locallibrary/settings.py (Auszug)
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']   # in Produktion die echten Domains
```

Starten Sie den Server neu und rufen Sie eine Seite mit CSS auf (z. B. `/catalog/`):

```bash
# macOS / Linux (bash)
python manage.py runserver
curl -I http://127.0.0.1:8000/static/catalog/styles.css
```

```bat
:: Windows (cmd.exe oder PowerShell) — curl.exe statt curl
python manage.py runserver
curl.exe -I http://127.0.0.1:8000/static/catalog/styles.css
```

**Erwartet:**

- Bei leerem `ALLOWED_HOSTS` (statt der gesetzten Werte) würde jeder Request mit **`400 Bad Request`** abgewiesen — daher sind die Hosts oben gesetzt.
- Der direkte Aufruf der statischen Datei liefert jetzt **`404 Not Found`**: Mit `DEBUG = False` liefert der Entwicklungsserver statische Dateien **nicht** mehr automatisch aus den App-Ordnern aus. Die Seite lädt zwar (HTTP 200), aber ohne Styling.

Das ist beabsichtigt: Das automatische Ausliefern war eine reine Entwicklungs-Hilfe. In Produktion gilt:

```bash
# Alle App-Statics in ein Auslieferungsverzeichnis sammeln
python manage.py collectstatic
```

```python
# locallibrary/settings.py — Produktion
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Ausgeliefert werden die gesammelten Dateien dann vom Webserver (nginx o. Ä.) oder direkt aus Django via **WhiteNoise** (`pip install whitenoise`, `whitenoise.middleware.WhiteNoiseMiddleware` direkt nach der `SecurityMiddleware` einhängen).

> **Hinweis:** Setzen Sie nach dieser Übung `DEBUG = True` für die weitere lokale Arbeit wieder zurück, damit Statik und Fehlerseiten wie gewohnt funktionieren.

### Schritt E.3 — Produktions-Checkliste anwenden

Gehen Sie diese Punkte durch und haken Sie ab, was für ein Produktiv-Deployment gesetzt sein muss (zur Orientierung jeweils die zugehörige Einstellung):

- [ ] **`DEBUG = False`** — zeigt sonst Stacktraces und interne Pfade nach außen.
- [ ] **`ALLOWED_HOSTS`** auf die echten Domains gesetzt (sonst `400` bei jedem Request).
- [ ] **`SECRET_KEY` aus einer Umgebungsvariable** gelesen, nicht im Code/Repo: z. B. `SECRET_KEY = os.environ['DJANGO_SECRET_KEY']`.
- [ ] **`SECURE_*` / HTTPS erzwingen:** `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_HSTS_SECONDS` gesetzt.
- [ ] **Echte Datenbank** statt SQLite (z. B. **PostgreSQL**) in `DATABASES` konfiguriert.
- [ ] **`collectstatic`** ausgeführt und Statik-Auslieferung über Webserver/WhiteNoise eingerichtet (`STATIC_ROOT` gesetzt).
- [ ] **Logging** konfiguriert (Ausgabe in Datei/Logging-Dienst statt nur Konsole).
- [ ] **`python manage.py check --deploy`** läuft ohne sicherheitskritische Warnungen durch.

**Erwartet:** Nachdem Sie `DEBUG = False`, `ALLOWED_HOSTS` und die `SECURE_*`-Flags gesetzt sowie `SECRET_KEY` aus der Umgebung gelesen haben, verschwinden die entsprechenden Warnungen aus `check --deploy` Stück für Stück — die Ausgabe wird kürzer.

---

## Checkpoint

Gehen Sie diese Liste durch — A, B, C und F sind voll überprüfbar, D und E nachvollziehbar nachgebaut:

- [ ] **REST-API (A):** `GET /catalog/api/books/` liefert **ohne** Token **401**; die Browsable API ist im Browser erreichbar.
- [ ] **Token (B):** Token per `drf_create_token` **oder** POST geholt; `curl -H "Authorization: Token <key>" …/catalog/api/books/` liefert **200 + JSON**; POST legt ein neues Buch an (**201**); falscher Token → **401**.
- [ ] **CSV-Import (C):** `python manage.py import_books books.csv` legt beim ersten Lauf die CSV-Bücher an; ein zweiter Lauf erzeugt **0** Dubletten (Idempotenz via `get_or_create`); fehlende Datei → sauberer `CommandError`.
- [ ] **i18n (D):** String mit `{% translate %}` markiert, `makemessages -l en` erzeugt die `.po`, `msgstr` gefüllt, `compilemessages` erzeugt die `.mo`; englische Spracheinstellung zeigt die Übersetzung.
- [ ] **Produktion (E):** `check --deploy` durchgegangen; mit `DEBUG = False` lädt die statische Datei **nicht** mehr automatisch (404) → `collectstatic`/WhiteNoise verstanden; Checkliste angewendet.

Wenn alle Punkte erfüllt sind, haben Sie die `catalog`-App über die HTML-Oberfläche hinaus erweitert: eine authentifizierte REST-API, einen robusten Datenimport, den i18n-Workflow und das Rüstzeug für ein produktionsreifes Deployment. Echtzeit per WebSockets bauen Sie im optionalen [Lab 6](lab6_realtime_checklist.md).

> Vergleichen Sie die erwarteten Ausgaben (Statuscodes, Konsolenausgaben) mit **EXPECTED_RESULTS.md**.
