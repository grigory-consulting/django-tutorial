# Lab 6 (optional) — Echtzeit-Prüfliste mit Django Channels und HTMX

> **Optionales Bonus-Lab** der Django-Einsteiger-Intensiv-Schulung (Django 5.2). Durchgehendes Projekt: **MDN LocalLibrary**, Projekt `locallibrary`, App `catalog`. Dieses Lab erweitert die **bestehende App `catalog`** um eine Echtzeit-Prüfliste.
>
> **Reihenfolge:** Optionales Bonus-Lab nach **Lab 5**. Setzt ein lauffähiges Projekt aus den Labs 1 bis 5 voraus (virtuelle Umgebung aktiv, `manage.py` erreichbar). Es baut **nicht** auf der REST-API aus Lab 5 auf, sondern steht für sich.

## Worum es geht

In Lab 5 war Channels nur ein geführter Walkthrough. Hier bauen Sie eine **voll lauffähige** geteilte Prüfliste: Mehrere Personen öffnen dieselbe Seite, und sobald **eine** Person einen Punkt abhakt, sehen **alle** anderen die Änderung sofort, ohne die Seite neu zu laden. Das ist das klassische Einsatzgebiet von WebSockets.

Das Besondere an diesem Lab: Sie schreiben **kein eigenes JavaScript**. Das Frontend wird über **HTMX** gesteuert, eine kleine Bibliothek, die WebSockets über HTML-Attribute anbindet. Die gesamte Server-Seite (Daphne, Channels, Consumer, Gruppen-Broadcast) bleibt dabei genau die, die man auch mit handgeschriebenem JavaScript brauchen würde. HTMX ersetzt nur den Browser-Code.

Konkret: Sie öffnen die Seite in zwei Browser-Tabs, klicken in Tab A einen Haken, und Tab B aktualisiert sich in derselben Sekunde.

## Lernziel

Nach diesem Lab können Sie:

- den Unterschied zwischen dem klassischen **Request/Response** (HTTP) und einer **dauerhaften WebSocket-Verbindung** erklären,
- **Django Channels** installieren, `asgi.py` auf einen `ProtocolTypeRouter` umstellen und einen **WebSocket-Consumer** schreiben,
- in einem Consumer eine Änderung in der **Datenbank** persistieren und sie als **HTML-Fragment** rendern,
- ein Update per **Channel Layer** an eine **Gruppe** verteilen (`group_send` → Handler → `send`), sodass alle verbundenen Clients es erhalten,
- ein Frontend ganz **ohne eigenes JavaScript** über HTMX (`hx-ext="ws"`, `ws-send`, `hx-swap-oob`) anbinden und den Live-Effekt nachvollziehen.

Vergleichen Sie Ihre Ergebnisse am Ende mit **EXPECTED_RESULTS.md**.

### Voraussetzungen

- Sie haben ein lauffähiges Projekt `locallibrary` mit der App `catalog` (Labs 1 bis 5). Die virtuelle Umgebung ist aktiv.
- Alle Befehle führen Sie im **Projektordner** aus, dort wo `manage.py` liegt.

> **Warum braucht das einen anderen Server?** Der klassische `runserver` ist ein **WSGI**-Server: Er kennt nur Request → Response und schließt die Verbindung danach. WebSockets brauchen eine **offene** Verbindung über die ganze Sitzung. Dafür gibt es **ASGI** (das asynchrone Gegenstück) und einen ASGI-Server wie **daphne**. Channels bringt daphne mit; sobald `daphne` in `INSTALLED_APPS` steht, läuft `runserver` automatisch als ASGI-Server.

---

## Überblick über die Schritte

| Schritt | Thema |
|---|---|
| A | Channels installieren und Settings vorbereiten |
| B | Modell `ChecklistItem` in `catalog` anlegen und migrieren |
| C | Consumer schreiben (Verbindung, Toggle, HTML-Broadcast) |
| D | Routing und `asgi.py` auf `ProtocolTypeRouter` umstellen |
| E | Seite + Frontend (HTMX statt eigenem JavaScript) |
| F | Starten und den Live-Effekt in zwei Tabs nachvollziehen |

---

## Schritt A — Channels installieren und registrieren

```bash
pip install "channels[daphne]"
```

In `locallibrary/settings.py` ergänzen Sie `INSTALLED_APPS`. Wichtig: **`daphne` ganz oben** (es übernimmt den `runserver`-Befehl), und `channels` mit aufnehmen. Die App `catalog` ist bereits vorhanden:

```python
INSTALLED_APPS = [
    "daphne",                       # MUSS vor django.contrib.staticfiles stehen
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "catalog",
]
```

Darunter (z. B. ans Ende der Datei) den ASGI-Einstiegspunkt und das Channel-Layer-Backend eintragen:

```python
ASGI_APPLICATION = "locallibrary.asgi.application"

# In-Memory-Backend: genügt für eine lokale Single-Process-Demo.
# In Produktion ist hier Redis nötig (mehrere Prozesse teilen sich die Nachrichten).
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}
```

> **Channel Layer in einem Satz:** ein gemeinsamer „Briefkasten", über den verschiedene WebSocket-Verbindungen einander Nachrichten schicken. Ohne ihn wüsste Verbindung A nichts von Verbindung B. Lokal reicht In-Memory; sobald mehrere Server-Prozesse laufen, muss der Briefkasten außerhalb der Prozesse liegen, deshalb Redis.

**Erwartet:** `pip` installiert `channels`, `daphne`, `asgiref` und Abhängigkeiten. `python manage.py check` läuft durch.

---

## Schritt B — Modell anlegen

Sie legen **keine neue App** an, sondern erweitern `catalog`. In `catalog/models.py` ergänzen Sie:

```python
class ChecklistItem(models.Model):
    """Ein abhakbarer Punkt fuer die Echtzeit-Checkliste (Realtime-Lab)."""
    text = models.CharField(max_length=200)
    done = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"[{'x' if self.done else ' '}] {self.text}"
```

Migrieren und ein paar Beispiel-Einträge anlegen:

```bash
python manage.py makemigrations catalog
python manage.py migrate
python manage.py shell -c "from catalog.models import ChecklistItem; [ChecklistItem.objects.create(text=t) for t in ['Repo geklont', 'Migrationen OK', 'Server gestartet', 'Tests OK']]"
```

**Erwartet:** `Migrations for 'catalog'` → eine neue Migration (*Create model ChecklistItem*); nach `migrate` die Zeile `Applying catalog.000X_checklistitem... OK`. Der `shell -c`-Befehl legt die Einträge an (keine Ausgabe ist normal).

---

## Schritt C — Consumer schreiben

Der **Consumer** ist das WebSocket-Gegenstück zur View. Eine View beantwortet **einen** Request; ein Consumer begleitet eine **dauerhafte** Verbindung über ihre ganze Lebensdauer: Verbindungsaufbau, eingehende Nachrichten, Verbindungsabbau.

Der entscheidende Unterschied zur reinen JavaScript-Variante: Der Consumer broadcastet **kein JSON**, sondern ein **fertiges HTML-Fragment** der betroffenen Zeile. HTMX setzt dieses Fragment im Browser automatisch an die richtige Stelle. Sie müssen im Browser also nichts mehr von Hand zusammenbauen.

`catalog/consumers.py` (neu anlegen):

```python
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string

from .models import ChecklistItem

GROUP = "checklist"  # alle verbundenen Tabs landen in dieser Gruppe


class ChecklistConsumer(AsyncWebsocketConsumer):
    """Server-Seite der Echtzeit-Checkliste (asynchron).

    Ablauf bei einem Toggle:
    1. Ein Tab sendet {"action": "toggle", "id": ...} ueber den WebSocket.
    2. Wir aendern den Datensatz in der DB (einzige Quelle der Wahrheit).
    3. Wir rendern die Zeile als HTML-Fragment und schicken es an die GANZE
       Gruppe. HTMX tauscht das Fragment per Out-of-Band-Swap in jeden Tab ein.

    Async-Variante: Channel-Layer-Aufrufe werden direkt ge-await-et. Nur der
    blockierende DB-Zugriff laeuft ueber database_sync_to_async in einem Thread.
    """

    async def connect(self):
        await self.channel_layer.group_add(GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(GROUP, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("action") != "toggle":
            return

        html = await self.toggle_and_render(data["id"])
        await self.channel_layer.group_send(
            GROUP, {"type": "checklist_update", "html": html}
        )

    # Wird fuer jeden in der Gruppe aufgerufen (Name = "type" oben mit _ statt .).
    async def checklist_update(self, event):
        await self.send(text_data=event["html"])

    @database_sync_to_async
    def toggle_and_render(self, item_id):
        # Laeuft im Thread: hier ist normaler, synchroner ORM-Zugriff erlaubt.
        item = ChecklistItem.objects.get(pk=item_id)
        item.done = not item.done
        item.save()
        return render_to_string(
            "catalog/_checklist_item.html", {"item": item, "oob": True}
        )
```

Vier Dinge sind hier zentral:

- **Asynchroner Consumer:** `AsyncWebsocketConsumer` passt zum asynchronen Server (Daphne). Die Methoden sind `async def`, und die Channel-Layer-Aufrufe (`group_add`, `group_send`, ...) werden direkt mit `await` aufgerufen, ohne Verpackung.
- **DB-Zugriff im Thread:** In einem `async`-Consumer darf **kein** direkter, blockierender ORM-Aufruf stehen, der würde die Event-Loop ausbremsen. Deshalb steckt der DB-Zugriff (`get`, `save`) in der Methode `toggle_and_render`, die mit `@database_sync_to_async` in einen Thread verlagert wird. `await self.toggle_and_render(...)` wartet auf das Ergebnis. Auch das Rendern der Zeile passiert dort, solange das Objekt schon geladen ist.
- **HTML statt JSON:** `render_to_string("catalog/_checklist_item.html", {"item": item, "oob": True})` erzeugt genau die eine Listenzeile als HTML. `oob=True` schaltet im Template das Attribut `hx-swap-oob` an, damit HTMX die Zeile **am richtigen Platz** ersetzt.
- **Gruppe statt einzelner Verbindung:** `group_send` schickt **nicht** direkt an einen Client, sondern an die **Gruppe**. Jede Verbindung in der Gruppe ruft den Handler `checklist_update` auf, der das HTML an ihren Browser weiterreicht. So erreichen Sie alle offenen Tabs. Der `"type"`-Wert `"checklist_update"` wird dabei zum Methodennamen `checklist_update`.

---

## Schritt D — Routing und `asgi.py`

`catalog/routing.py` (neu anlegen):

```python
from django.urls import path

from . import consumers

# WebSocket-Routen (analog zu urlpatterns, aber fuer das ws-Protokoll).
websocket_urlpatterns = [
    path("ws/checklist/", consumers.ChecklistConsumer.as_asgi()),
]
```

`locallibrary/asgi.py` auf einen **`ProtocolTypeRouter`** umstellen. Er ist die Weiche: HTTP-Anfragen laufen weiter über die normale Django-App, WebSocket-Verbindungen gehen an die Channels-Router.

```python
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "locallibrary.settings")

# Django zuerst initialisieren, dann erst Channels-Importe (Reihenfolge wichtig).
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from catalog.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
```

> **Reihenfolge der Importe:** `get_asgi_application()` muss laufen, **bevor** `from catalog.routing ...` die Modelle importiert. Sonst sind die Apps noch nicht geladen und Sie bekommen `AppRegistryNotReady`. Deshalb stehen die Channels-Importe bewusst **unter** dieser Zeile.

---

## Schritt E — Seite und Frontend (HTMX)

### HTMX lokal einbinden

Damit das Lab auch ohne Internet läuft, legen Sie HTMX und die WebSocket-Extension lokal ab (statt sie von einem CDN zu laden).

**macOS / Linux (bash):**

```bash
mkdir -p catalog/static/catalog/vendor
curl -fsSL https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js     -o catalog/static/catalog/vendor/htmx.min.js
curl -fsSL https://unpkg.com/htmx.org@1.9.12/dist/ext/ws.js       -o catalog/static/catalog/vendor/htmx-ext-ws.js
```

**Windows (PowerShell):** In PowerShell ist `curl` ein Alias für `Invoke-WebRequest`, deshalb hier `curl.exe` (das echte curl, ab Windows 10 enthalten):

```powershell
New-Item -ItemType Directory -Force catalog\static\catalog\vendor | Out-Null
curl.exe -fsSL https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js -o catalog\static\catalog\vendor\htmx.min.js
curl.exe -fsSL https://unpkg.com/htmx.org@1.9.12/dist/ext/ws.js   -o catalog\static\catalog\vendor\htmx-ext-ws.js
```

**Windows (Eingabeaufforderung / cmd.exe):**

```bat
mkdir catalog\static\catalog\vendor
curl.exe -fsSL https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js -o catalog\static\catalog\vendor\htmx.min.js
curl.exe -fsSL https://unpkg.com/htmx.org@1.9.12/dist/ext/ws.js   -o catalog\static\catalog\vendor\htmx-ext-ws.js
```

### View und URL

`catalog/views.py` ergänzen:

```python
from .models import Author, Book, ChecklistItem


def checklist(request):
    return render(request, "catalog/checklist.html", {"items": ChecklistItem.objects.all()})
```

In `catalog/urls.py` die Route ergänzen:

```python
urlpatterns = [
    # ... bestehende Routen ...
    path("checklist/", views.checklist, name="checklist"),
]
```

> Da `catalog.urls` in `locallibrary/urls.py` unter `path("catalog/", include("catalog.urls"))` eingebunden ist, erreichen Sie die Seite später unter **`/catalog/checklist/`**.

### Das Zeilen-Fragment

`catalog/templates/catalog/_checklist_item.html` (neu anlegen). Dieses Fragment wird **zweimal** verwendet: beim ersten Laden der Seite (ohne `oob`) und beim Broadcast vom Server (mit `oob=True`).

```html
{% comment %}
Eine Checklisten-Zeile. Wird zweimal genutzt:
- beim ersten Laden der Seite (ohne oob)
- beim Broadcast vom Server (mit oob=True) -> HTMX ersetzt die Zeile in-place
ws-send: bei einer Aenderung schickt HTMX die Formularfelder ueber den WebSocket.
{% endcomment %}
<form id="item-{{ item.id }}" ws-send hx-trigger="change"
      {% if oob %}hx-swap-oob="true"{% endif %}>
  <input type="hidden" name="action" value="toggle">
  <input type="hidden" name="id" value="{{ item.id }}">
  <label>
    <input type="checkbox" {% if item.done %}checked{% endif %}>
    <span class="{% if item.done %}done{% endif %}">{{ item.text }}</span>
  </label>
</form>
```

### Die Seite

`catalog/templates/catalog/checklist.html` (neu anlegen). Sie erbt vom vorhandenen `base_generic.html`, bindet HTMX lokal ein und öffnet **eine** WebSocket-Leitung für die ganze Liste:

```html
{% extends "catalog/base_generic.html" %}
{% load static %}

{% block content %}
  <script src="{% static 'catalog/vendor/htmx.min.js' %}"></script>
  <script src="{% static 'catalog/vendor/htmx-ext-ws.js' %}"></script>
  <style>.done { text-decoration: line-through; color: #888; }</style>

  <h1>Checkliste (Echtzeit)</h1>
  <p>Oeffnen Sie diese Seite in zwei Browser-Tabs. Ein Haken in einem Tab
     erscheint sofort auch im anderen, ohne Neuladen.</p>

  {# hx-ext="ws" + ws-connect: oeffnet EINE WebSocket-Leitung fuer alles darin. #}
  <div hx-ext="ws" ws-connect="/ws/checklist/">
    <div id="list">
      {% for item in items %}
        {% include "catalog/_checklist_item.html" %}
      {% endfor %}
    </div>
  </div>
{% endblock %}
```

So greift das ohne eine Zeile selbstgeschriebenes JavaScript ineinander:

- **`hx-ext="ws" ws-connect="/ws/checklist/"`** am `<div>` öffnet die WebSocket-Verbindung. Alles darin kann darüber senden und empfangen.
- **`ws-send` + `hx-trigger="change"`** am `<form>` jeder Zeile: Sobald Sie die Checkbox anklicken (Ereignis `change`), schickt HTMX die Formularfelder (`action=toggle`, `id=…`) als JSON über den WebSocket. Genau dieses JSON liest der Consumer in `receive`.
- **`hx-swap-oob="true"`** im Broadcast-Fragment: Wenn der Server die geänderte Zeile zurückschickt, sucht HTMX im DOM das Element mit derselben `id` (`item-<pk>`) und **ersetzt es**. Das passiert in **jedem** verbundenen Tab.

> **Wo bleibt die „single source of truth"?** Beim Klick schaltet der Browser die Checkbox kurz selbst um. Diese lokale Anzeige wird aber sofort durch das HTML überschrieben, das der Server zurückschickt. Maßgeblich ist also immer der **vom Server gerenderte, in der DB gespeicherte** Zustand, in allen Tabs identisch. Bei der reinen JavaScript-Variante mussten Sie dieses Überschreiben von Hand programmieren; HTMX erledigt es über den Out-of-Band-Swap automatisch.

---

## Schritt F — Starten und den Live-Effekt nachvollziehen

```bash
python manage.py runserver
```

**Erwartet:** In der Startausgabe erscheint ein Hinweis auf **ASGI/Daphne** (statt des reinen WSGI-Servers), z. B. `Starting ASGI/Daphne ... development server`. Genau das zeigt, dass WebSockets jetzt bedient werden.

Öffnen Sie `http://127.0.0.1:8000/catalog/checklist/` in **zwei** Browser-Tabs nebeneinander.

1. Beide Tabs bauen beim Laden die WebSocket-Verbindung auf (`connect` → `group_add` → `accept`).
2. Klicken Sie in **Tab A** einen Eintrag an.
3. HTMX schickt `{"action":"toggle","id":…}` an den Server, der den Eintrag in der DB umschaltet, die Zeile als HTML rendert und an die **Gruppe** verteilt.
4. **Beide** Tabs erhalten das HTML-Fragment und HTMX tauscht genau diese Zeile aus, durchgestrichen oder wieder normal.

**Erwartet:** Die Änderung in Tab A erscheint **ohne Reload** sofort auch in Tab B. Laden Sie Tab B trotzdem neu, bleibt der Haken erhalten, der Zustand ist **persistiert** (in der Datenbank, nicht nur im Browser).

> So sähen zwei Mitarbeiter:innen, die dieselbe Prüfliste offen haben, jede Änderung der anderen Person in Echtzeit, und beim erneuten Öffnen ist der Stand noch da.

---

## Checkpoint

- [ ] `channels[daphne]` installiert; `daphne` steht **oben** in `INSTALLED_APPS`, `channels` ebenfalls.
- [ ] `ASGI_APPLICATION` und `CHANNEL_LAYERS` (InMemory) in den Settings gesetzt.
- [ ] Modell `ChecklistItem` in `catalog` migriert; Beispiel-Einträge vorhanden.
- [ ] `ChecklistConsumer` (async) mit `connect`/`disconnect`/`receive`/`checklist_update` vorhanden; `toggle_and_render` (per `@database_sync_to_async`) ändert die DB und liefert das HTML-Fragment, das per `group_send` an die Gruppe geht.
- [ ] `catalog/routing.py` angelegt; `asgi.py` auf `ProtocolTypeRouter` umgestellt (HTTP + WebSocket getrennt geroutet).
- [ ] HTMX und ws-Extension liegen lokal unter `catalog/static/catalog/vendor/`.
- [ ] `/catalog/checklist/` rendert die Liste; `runserver` startet als **ASGI/Daphne**.
- [ ] Zwei Tabs: ein Klick in Tab A erscheint **live** in Tab B; nach Reload ist der Zustand **persistiert**.

## Über dieses Lab hinaus

- **Redis statt In-Memory:** Sobald die App auf mehreren Prozessen läuft (Produktion), ersetzen Sie das Backend durch `channels_redis.core.RedisChannelLayer`. Der übrige Code bleibt unverändert.
- **Authentifizierung:** `AuthMiddlewareStack` stellt im Consumer `self.scope["user"]` bereit; Sie könnten anonyme Zugriffe ablehnen oder protokollieren, wer welchen Punkt gesetzt hat.
- **Neue Einträge live:** Aktuell wird nur das Abhaken verteilt. Als Übung könnten Sie das Anlegen eines neuen Eintrags ebenfalls über den Consumer broadcasten (ein zweites `ws-send`-Formular, ein weiterer `action`-Wert).
- **Variante mit eigenem JavaScript:** Wer den WebSocket lieber von Hand anbindet (ohne HTMX), schickt im Consumer JSON statt HTML und baut die Zeile im Browser mit `sock.onmessage` selbst zusammen. Funktional gleich, nur mehr Frontend-Code.
