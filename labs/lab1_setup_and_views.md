# Lab 1 — Setup, Projekt, App, URLs und erste View

> **Durchgehendes Projekt:** Wir bauen über alle Labs hinweg die **LocalLibrary** nach dem
> [MDN Django-Tutorial](https://github.com/mdn/django-locallibrary-tutorial).
> Projektname: `locallibrary`, App-Name: `catalog`.
> Dieses Lab legt das **Fundament**: die Labs 2 bis 5 bauen direkt darauf auf.
>
> **Reihenfolge:** Schritt 1 von 5 · Start der Reihe · Danach: **Lab 2** (Modelle, ORM & Admin, `lab2_orm_queries.ipynb`).

## Lernziel

Nach diesem Lab können Sie:

- ein Django-Projekt aufsetzen — **manuell** *und* mit **Cookiecutter**,
- eine **App** zum Projekt hinzufügen und in `INSTALLED_APPS` registrieren,
- die **URL-Konfiguration** über `include()` und benannte Routen einrichten,
- eine erste **View** mit `HttpResponse` schreiben und im Browser testen.

> Erwartete Ergebnisse (Konsolenausgaben, Verzeichnisbäume, Browser-Inhalte) finden Sie
> gebündelt in **EXPECTED_RESULTS.md**.

Wir verwenden **Django 5.2** und **Python 3.12+**.

---

## 1. Setup-Voraussetzungen

**Aufgabe:** Prüfen Sie Ihre Python-Version, legen Sie eine virtuelle Umgebung an, aktivieren Sie diese und installieren Sie Django.

### 1.1 Python-Version prüfen

Django 5.2 unterstützt **Python 3.10–3.13**; wir setzen für die Schulung **3.12+** voraus.

```bash
python --version
```

> Falls `python` bei Ihnen auf Python 2 zeigt oder nicht gefunden wird, verwenden Sie `python3`.

**Erwartet:**

```text
Python 3.12.x
```

### 1.2 Virtuelle Umgebung anlegen

Wir legen die Umgebung im Ordner `.venv` an. Wechseln Sie zunächst in Ihren Arbeitsordner (z. B. `~/django-kurs` bzw. `C:\django-kurs`).

```bash
python -m venv .venv
```

**Erwartet:** Kein sichtbarer Output. Es entsteht ein Ordner `.venv/` mit dem Python-Interpreter und einer isolierten Paketumgebung.

### 1.3 Virtuelle Umgebung aktivieren

Die Aktivierung unterscheidet sich je nach Betriebssystem:

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Eingabeaufforderung / cmd):**

```bat
.venv\Scripts\activate.bat
```

> **Hinweis Windows/PowerShell:** Falls die Aktivierung mit einer Ausführungsrichtlinien-Fehlermeldung abbricht, erlauben Sie Skripte einmalig für die aktuelle Sitzung:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> ```

**Erwartet:** Der Prompt wird der virtuellen Umgebung vorangestellt:

```text
(.venv) ~/django-kurs $
```

### 1.4 Django installieren

```bash
python -m pip install --upgrade pip
python -m pip install "django==5.2.*"
```

> **Wichtig: Version pinnen.** `pip install django` allein installiert immer die **neueste** Version (aktuell 6.0.x). Die Schulung läuft auf **5.2**, weil das die **LTS**-Version ist (Long-Term Support, Sicherheits-Updates bis ~2028). Der Pin `"django==5.2.*"` holt die aktuellste 5.2-Patch-Version (z. B. 5.2.6) und schließt 6.0 aus.

**Erwartet (gekürzt):**

```text
Successfully installed asgiref-3.x.x django-5.2.x sqlparse-0.x.x
```

### 1.5 Installation verifizieren

```bash
django-admin --version
```

**Erwartet:**

```text
5.2
```

> Damit ist die Werkbank eingerichtet. Lassen Sie die virtuelle Umgebung für den Rest des Labs aktiviert.

---

## 2. Übung A — Projekt manuell anlegen

**Aufgabe:** Legen Sie das Django-Projekt `locallibrary` an, verstehen Sie das Verzeichnis-Layout und starten Sie den Entwicklungsserver.

### 2.1 Projekt erzeugen

```bash
django-admin startproject locallibrary
```

**Erwartet:** Kein Output. Es entsteht folgendes Layout:

```text
locallibrary/
├── manage.py
└── locallibrary/
    ├── __init__.py
    ├── asgi.py
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

> **Layout erklärt:**
> - `manage.py` — Kommandozeilen-Werkzeug für administrative Aufgaben (`runserver`, `migrate`, `startapp`, …). Damit arbeiten Sie ab jetzt.
> - `locallibrary/` (innen) — das **Projektpaket** (Konfiguration). Verwechselbar gleichnamig mit dem äußeren Ordner.
> - `settings.py` — zentrale Konfiguration (installierte Apps, Datenbank, Sprache, Zeitzone, statische Dateien).
> - `urls.py` — Wurzel-URL-Konfiguration; verteilt Anfragen auf die Views.
> - `asgi.py` / `wsgi.py` — Einstiegspunkte für Produktions-Webserver (asynchron bzw. synchron).

### 2.2 In den Projektordner wechseln

Alle weiteren `manage.py`-Befehle führen Sie im **äußeren** `locallibrary/`-Ordner aus (dort, wo `manage.py` liegt):

```bash
cd locallibrary
```

### 2.3 Entwicklungsserver starten

```bash
python manage.py runserver
```

**Erwartet (gekürzt):**

```text
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).

You have 18 unapplied migration(s). Your project may not work properly until you apply
the migrations for app(s): admin, auth, contenttypes, sessions.
Run 'python manage.py migrate' to apply them.

Django version 5.2.x, using settings 'locallibrary.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

> Die Warnung zu „unapplied migration(s)“ ist für dieses Lab erwartbar und unkritisch — die Datenbank behandeln wir in Lab 2.

### 2.4 Im Browser öffnen

Öffnen Sie **http://127.0.0.1:8000/**

**Erwartet:** Die Django-Willkommensseite mit der startenden **Rakete** und dem Text *„The install worked successfully! Congratulations!“*.

Stoppen Sie den Server anschließend mit **STRG + C** (Windows/Linux) bzw. **CONTROL + C** (macOS).

---

## 3. Übung B — App hinzufügen

**Aufgabe:** Erzeugen Sie die App `catalog` und registrieren Sie diese in `INSTALLED_APPS`.

### 3.1 App erzeugen

Im Ordner mit `manage.py`:

```bash
python manage.py startapp catalog
```

**Erwartet:** Kein Output. Es entsteht der App-Ordner:

```text
catalog/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
│   └── __init__.py
├── models.py
├── tests.py
└── views.py
```

> **Projekt vs. App:** Ein **Projekt** ist die Gesamtanwendung samt Konfiguration. Eine **App** ist ein in sich geschlossener Funktionsbaustein (hier: der Bibliothekskatalog). Ein Projekt kann mehrere Apps enthalten.

### 3.2 App registrieren

Öffnen Sie `locallibrary/settings.py` und ergänzen Sie `'catalog'` in der Liste `INSTALLED_APPS`:

```python
# locallibrary/settings.py

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalog",  # <-- neu hinzugefügt
]
```

### 3.3 Registrierung prüfen

```bash
python manage.py check
```

**Erwartet:**

```text
System check identified no issues (0 silenced).
```

> Ohne erkannte Fehler ist die App korrekt eingebunden. Django kennt `catalog` nun und durchsucht z. B. dessen `migrations/`- und (später) `templates/`-Ordner.

---

## 4. Übung C — URL-Konfiguration

**Aufgabe:** Legen Sie eine eigene `catalog/urls.py` an und binden Sie diese per `include()` in die Projekt-URLs ein. Die Route erhält den Namen `index`.

### 4.1 URL-Konfiguration der App anlegen

Erstellen Sie die **neue** Datei `catalog/urls.py`:

```python
# catalog/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
]
```

> Das leere Muster `""` bedeutet: relativ zum eingebundenen Pfad die „Wurzel“. Der Name `index` erlaubt es später, die URL per `reverse('index')` bzw. `{% url 'index' %}` aufzulösen, statt sie fest zu verdrahten.

### 4.2 App-URLs ins Projekt einbinden

Öffnen Sie `locallibrary/urls.py` und binden Sie die App-URLs per `include()` ein:

```python
# locallibrary/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("catalog/", include("catalog.urls")),
]
```

> Mit `include("catalog.urls")` delegiert das Projekt alle Anfragen unter `catalog/` an die URL-Konfiguration der App. Die in 4.1 definierte Wurzel `""` ist damit über **http://127.0.0.1:8000/catalog/** erreichbar.

**Erwartet (an dieser Stelle):** Die View `views.index` existiert noch nicht — das beheben wir in Übung D. Starten Sie den Server hier noch **nicht**.

---

## 5. Übung D — Erste View mit HttpResponse

**Aufgabe:** Schreiben Sie die `index`-View, die mit `HttpResponse` einen einfachen Text zurückgibt, und testen Sie diese im Browser.

### 5.1 View schreiben

Öffnen Sie `catalog/views.py` und ergänzen Sie:

```python
# catalog/views.py
from django.http import HttpResponse


def index(request):
    """Einfachste View: gibt eine Textantwort zurück."""
    return HttpResponse("Willkommen in der LocalLibrary")
```

> Eine **View** ist eine Funktion, die ein `request`-Objekt entgegennimmt und ein `HttpResponse`-Objekt zurückgibt. `HttpResponse` ist die einfachste Antwort: reiner Inhalt ohne Template. Templates und Datenbankzugriff folgen in den nächsten Labs.

### 5.2 Verdrahtung prüfen

Die URL→View-Verdrahtung steht bereits:
`locallibrary/urls.py` → `include("catalog.urls")` → `catalog/urls.py` → `path("", views.index, name="index")`.

### 5.3 Server starten und testen

```bash
python manage.py runserver
```

Öffnen Sie **http://127.0.0.1:8000/catalog/**

**Erwartet im Browser:**

```text
Willkommen in der LocalLibrary
```

> Rufen Sie zum Vergleich die Wurzel **http://127.0.0.1:8000/** auf — dort erscheint nun eine **404**-Seite, da unter `""` keine Route registriert ist (nur unter `catalog/` und `admin/`). Das ist korrekt; eine Weiterleitung der Wurzel auf `catalog/` richten wir in Lab 2 ein.

Stoppen Sie den Server anschließend wieder mit **STRG + C** / **CONTROL + C**.

---

## 6. Übung E — Cookiecutter (alternativer Weg)

**Aufgabe:** Lernen Sie kennen, wie Projekte über **Templates** generiert werden. Sie erzeugen ein Projekt aus einem Cookiecutter-Template, verstehen die Rolle von `cookiecutter.json` und lernen `cookiecutter-django` als Produktions-Scaffold kennen.

> **Wichtig für die Schulung:** Wir arbeiten anschließend mit dem **manuell** angelegten Projekt aus den Übungen A–D weiter. Cookiecutter zeigt hier nur den **professionellen Scaffold-Weg**. Erzeugen Sie das Beispielprojekt daher **außerhalb** Ihres `locallibrary/`-Ordners (z. B. eine Ebene höher).

### 6.1 Cookiecutter installieren

```bash
python -m pip install cookiecutter
```

**Erwartet (gekürzt):**

```text
Successfully installed cookiecutter-2.x.x ...
```

### 6.2 Ein lokales Mini-Template anlegen

Damit die Übung **offline** und ohne GitHub-Zugriff funktioniert, bauen wir ein winziges eigenes Template. Wechseln Sie eine Ebene über `locallibrary/` und legen Sie folgende Struktur an:

```text
mini-template/
├── cookiecutter.json
└── {{ cookiecutter.project_slug }}/
    └── README.md
```

**`mini-template/cookiecutter.json`:**

```json
{
    "project_name": "Meine App",
    "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}",
    "author": "Ihr Name"
}
```

> **`cookiecutter.json` erklärt:** Diese Datei definiert die **Variablen** des Templates und ihre Vorgabewerte. Beim Generieren fragt Cookiecutter jede Variable interaktiv ab (Enter übernimmt die Vorgabe). Werte können von anderen Variablen abgeleitet werden — hier wird `project_slug` automatisch aus `project_name` gebildet (Kleinschreibung, Leerzeichen → Unterstrich).

**`mini-template/{{ cookiecutter.project_slug }}/README.md`:**

```text
# {{ cookiecutter.project_name }}

Erstellt von {{ cookiecutter.author }}.
```

> Platzhalter in Datei-/Ordnernamen **und** in Dateiinhalten folgen der Jinja2-Syntax `{{ cookiecutter.<variable> }}` und werden beim Generieren ersetzt.

### 6.3 Projekt aus dem Template generieren

```bash
cookiecutter mini-template
```

Cookiecutter fragt die Variablen ab (Vorgaben in eckigen Klammern):

**Erwartet (interaktiver Dialog):**

```text
  [1/3] project_name (Meine App):
  [2/3] project_slug (meine_app):
  [3/3] author (Ihr Name):
```

Bestätigen Sie die Vorgaben jeweils mit Enter. **Erwartet (Ergebnis):**

```text
meine_app/
└── README.md
```

> Cookiecutter hat den Ordner `{{ cookiecutter.project_slug }}` zu `meine_app` aufgelöst und alle Platzhalter ersetzt.

### 6.4 Alternative: Template direkt von GitHub

Cookiecutter kann ein Template auch direkt aus einem Git-Repository ziehen (Internetzugang erforderlich):

```bash
cookiecutter https://github.com/cookiecutter/cookiecutter-django
```

### 6.5 `cookiecutter-django` als Produktions-Scaffold

[`cookiecutter-django`](https://github.com/cookiecutter/cookiecutter-django) ist ein etabliertes, **produktionsreifes** Template. Statt eines minimalen Projekts erzeugt es ein vollständiges Setup mit sinnvollen Voreinstellungen und einem ausführlichen Optionen-Dialog.

**Erwartet (Auszug aus dem Optionen-Dialog, gekürzt):**

```text
  [1/...] project_name (My Awesome Project):
  [2/...] project_slug (my_awesome_project):
  [3/...] description (Behold My Awesome Project!):
  [4/...] author_name (Daniel Roy Greenfeld):
  [5/...] domain_name (example.com):
  [6/...] email (daniel-roy-greenfeld@example.com):
  [7/...] username_type (username):
  [8/...] timezone (UTC):
  [9/...] use_async (No):
  [10/...] use_drf (No):
  [11/...] frontend_pipeline (None):
  [12/...] use_celery (No):
  [13/...] use_mailpit (No):
  [14/...] use_sentry (No):
  [15/...] use_whitenoise (No):
  [16/...] cloud_provider (None):
  [17/...] postgresql_version (...):
  ...
```

> Solche Templates beantworten typische Produktionsfragen vorab: Asynchron (`use_async`), REST-API (`use_drf`), Hintergrundaufgaben (`use_celery`), Fehler-Monitoring (`use_sentry`), Cloud-Provider, Datenbankversion u. a. So entsteht in Minuten ein konsistentes, gut strukturiertes Projektgerüst.
>
> **Für diese Schulung** bleiben wir beim manuell angelegten `locallibrary` — so bleibt jeder Baustein nachvollziehbar.

---

## 7. Bonus / Checkpoint

**Was sollte jetzt laufen?** Prüfen Sie Ihre Checkliste:

- [ ] `python --version` zeigt **3.12+**.
- [ ] Die virtuelle Umgebung **(.venv)** ist aktiviert (Prompt-Präfix).
- [ ] `django-admin --version` zeigt **5.2**.
- [ ] Projekt `locallibrary` existiert; `manage.py` liegt im äußeren Ordner.
- [ ] App `catalog` existiert und steht in `INSTALLED_APPS`.
- [ ] `python manage.py check` meldet **keine** Probleme.
- [ ] `catalog/urls.py` definiert die Route `path("", views.index, name="index")`.
- [ ] `locallibrary/urls.py` bindet `include("catalog.urls")` unter `catalog/` ein.
- [ ] `catalog/views.py` enthält die `index`-View mit `HttpResponse`.
- [ ] **http://127.0.0.1:8000/catalog/** zeigt *„Willkommen in der LocalLibrary“*.
- [ ] Sie haben mit Cookiecutter ein Projekt aus einem Template generiert und `cookiecutter.json` verstanden.

**Bonusaufgabe (optional):** Ändern Sie den Text der `index`-View auf *„Willkommen in der LocalLibrary — Tag 1 geschafft!“*, speichern Sie und beobachten Sie, wie der laufende Server dank **StatReloader** automatisch neu lädt. Aktualisieren Sie die Browser-Seite.

**Bonusaufgabe 2 (optional) — Eine eigene Middleware:** Middleware sitzt in der Verarbeitungskette vor und nach jeder View. Schreiben Sie eine winzige Middleware, die jeden Request-Pfad protokolliert.

Datei `catalog/middleware.py`:

```python
# catalog/middleware.py
class PathLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response          # einmalig beim Start

    def __call__(self, request):
        print(f"[Middleware] eingehend: {request.path}")
        response = self.get_response(request)     # ruft die nächste Schicht / die View
        print(f"[Middleware] Status: {response.status_code}")
        return response
```

Tragen Sie die Klasse in `locallibrary/settings.py` **am Ende** der Liste `MIDDLEWARE` ein:

```python
MIDDLEWARE = [
    # ... die bestehenden Django-Middlewares ...
    "catalog.middleware.PathLogMiddleware",
]
```

**Erwartet:** Bei jedem Aufruf von `http://127.0.0.1:8000/catalog/` erscheinen in der Server-Konsole zwei Zeilen, z. B. `[Middleware] eingehend: /catalog/` und `[Middleware] Status: 200`. Verschieben Sie den Eintrag an den Anfang der Liste und beobachten Sie, dass die Reihenfolge in `MIDDLEWARE` bestimmt, wann Ihre Middleware in der Kette läuft.

> **Ausblick Lab 2:** Wir definieren Datenmodelle (`Book`, `Author`, `Genre`, …), führen Migrationen aus und ersetzen die einfache `HttpResponse` durch echte Templates.

Erwartete Ergebnisse zu allen Schritten finden Sie in **EXPECTED_RESULTS.md**.
