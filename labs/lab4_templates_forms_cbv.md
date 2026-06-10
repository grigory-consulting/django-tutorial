# Lab 4 — Templates, Formulare & klassenbasierte Views

> **Lab 4** der Django-Einsteiger-Intensiv-Schulung (Django 5.2). Durchgehendes Projekt: **MDN LocalLibrary** (`github.com/mdn/django-locallibrary-tutorial`), Projekt `locallibrary`, App `catalog`, mit den Modellen `Author`, `Book`, `BookInstance` aus Lab 2.
>
> **Reihenfolge:** Schritt 4 von 5 · Vorher: **Lab 3** (Migrationen, Fixtures & Tests, `lab3_migrations_tests.md`) · Danach: **Lab 5** (REST-API, Import & Produktion, `lab5_rest_realtime_prod.md`).

## Lernziel

Nach diesem Lab können Sie:

- Templates mit **Vererbung** (`{% extends %}` / `{% block %}`) schreiben und ein gemeinsames Grundgerüst wiederverwenden,
- **statische Dateien** (CSS) korrekt mit `{% load static %}` und `{% static %}` einbinden,
- ein **Formular mit serverseitiger Validierung** (`forms.Form`, `clean_*`, `ValidationError`) verarbeiten — inklusive GET/POST/`is_valid()`/`redirect`-Muster,
- Boilerplate-Views durch **generische klassenbasierte Views** (`ListView`, `DetailView`) ersetzen und diese gezielt anpassen.

Vergleichen Sie Ihre Ergebnisse am Ende mit **EXPECTED_RESULTS.md**.

### Voraussetzungen

- Sie haben die **Labs 1 bis 3** abgeschlossen (Setup, Modelle/ORM/Admin, Migrationen/Fixtures/Tests).
- Die virtuelle Umgebung ist aktiv und der Entwicklungsserver lässt sich starten:

```bash
python manage.py runserver
```

- Die Modelle `Author`, `Book`, `BookInstance` existieren und sind migriert. In der Datenbank liegen einige Test-Datensätze (über den Admin in Lab 2 angelegt).

---

## Übung A — Template-Vererbung

### Aufgabe

Bauen Sie ein gemeinsames Grundgerüst `base_generic.html` mit den Blöcken `content` und `sidebar`, binden Sie eine CSS-Datei als statische Datei ein und lassen Sie die Startseite `index.html` per `{% extends %}` davon erben. Stellen Sie anschließend die `index`-View vom direkten `HttpResponse` auf den `render()`-Shortcut mit Context um.

### Schritt A.1 — Template-Verzeichnis und statische Datei anlegen

Django sucht App-Templates per Konvention unter `<app>/templates/<app>/…` und statische Dateien unter `<app>/static/<app>/…`. Der doppelte App-Name ist **Absicht** (Namespacing — siehe Übung D).

```bash
mkdir -p catalog/templates/catalog
mkdir -p catalog/static/catalog
```

Prüfen Sie, dass `INSTALLED_APPS` in `locallibrary/settings.py` `'catalog'` enthält (sonst werden weder Templates noch Statics gefunden) und dass die `APP_DIRS`-Template-Suche aktiv ist:

```python
# locallibrary/settings.py (Auszug — sollte bereits so vorliegen)
INSTALLED_APPS = [
    'catalog.apps.CatalogConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,   # <- aktiviert die Suche in <app>/templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Statische Dateien
STATIC_URL = 'static/'
```

**Erwartet:** `python manage.py check` läuft ohne Fehler durch. Die beiden neuen Verzeichnisse existieren.

### Schritt A.2 — Stylesheet anlegen

Datei `catalog/static/catalog/styles.css`:

```css
.sidebar-nav {
    margin-top: 20px;
    padding: 0;
    list-style: none;
}

body {
    font-family: sans-serif;
    margin: 0;
    padding: 1rem 2rem;
}

h1 {
    color: #2b5797;
}
```

### Schritt A.3 — Basis-Template `base_generic.html`

Datei `catalog/templates/base_generic.html`:

```html+django
<!DOCTYPE html>
<html lang="de">
<head>
  {% block title %}<title>Lokale Bibliothek</title>{% endblock %}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  {% load static %}
  <link rel="stylesheet" href="{% static 'catalog/styles.css' %}">
</head>

<body>
  {% block sidebar %}
    <ul class="sidebar-nav">
      <li><a href="{% url 'index' %}">Startseite</a></li>
      {# Link zur Buchliste folgt später, sobald die Route 'books' existiert #}
    </ul>
  {% endblock %}

  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

Hinweise:

- `{% load static %}` muss **vor** der ersten Verwendung von `{% static %}` stehen.
- `{% block sidebar %}` enthält eine Standard-Navigation. Kindtemplates können diesen Block überschreiben oder mit `{{ block.super }}` ergänzen.
- `{% url 'index' %}` zeigt auf die benannte Route `index` aus Lab 1. **Wichtig:** Den Link zur Buchliste ergänzen wir erst in **Übung B** — ein `{% url 'books' %}` auf eine noch nicht angelegte Route würde sofort einen `NoReverseMatch`-Fehler (HTTP 500) auslösen, nicht nur einen toten Link.

### Schritt A.4 — `index.html` erbt vom Grundgerüst

Datei `catalog/templates/catalog/index.html`:

```html+django
{% extends "base_generic.html" %}

{% block content %}
  <h1>Startseite der lokalen Bibliothek</h1>

  <p>Willkommen in <em>LocalLibrary</em>, einer Beispielanwendung der
     Django-Einsteigerschulung.</p>

  <h2>Bestand</h2>
  <ul>
    <li><strong>Bücher:</strong> {{ num_books }}</li>
    <li><strong>Autoren:</strong> {{ num_authors }}</li>
  </ul>
{% endblock %}
```

### Schritt A.5 — `index`-View auf `render()` umstellen

Öffnen Sie `catalog/views.py` und ersetzen Sie die bisherige `index`-View durch eine Variante, die ihren Context per `render()` an das Template übergibt:

```python
# catalog/views.py
from django.shortcuts import render

from .models import Author, Book


def index(request):
    """Startseite mit einfachen Bestandszahlen."""
    num_books = Book.objects.count()
    num_authors = Author.objects.count()

    context = {
        'num_books': num_books,
        'num_authors': num_authors,
    }

    # render() lädt das Template, füllt es mit dem Context und gibt ein
    # HttpResponse-Objekt zurück.
    return render(request, 'catalog/index.html', context=context)
```

Stellen Sie sicher, dass die URL für die Startseite den Namen `index` trägt. In `catalog/urls.py`:

```python
# catalog/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
]
```

Und dass `catalog/urls.py` in `locallibrary/urls.py` eingebunden ist:

```python
# locallibrary/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('catalog/', include('catalog.urls')),
]
```

**Erwartet:**

- Aufruf von `http://127.0.0.1:8000/catalog/` zeigt die Startseite mit Überschrift, Navigations-Sidebar und den Zahlen aus der Datenbank (z. B. „Bücher: 3 / Autoren: 2", abhängig von Ihren Testdaten).
- Das Stylesheet greift (serifenlose Schrift, blaue Überschrift). Im Quelltext der Seite verweist `<link rel="stylesheet" href="/static/catalog/styles.css">` auf eine erreichbare Datei (kein 404 im Server-Log).

---

## Übung B — ListView / DetailView (CBV)

### Aufgabe

Ersetzen Sie das Anzeigen einer Bücherliste und einer Buch-Detailseite durch die generischen klassenbasierten Views `ListView` und `DetailView`. Konfigurieren Sie Pagination und einen sprechenden Context-Namen, verdrahten Sie die URLs mit einem `<int:pk>`-Konverter und schreiben Sie die zugehörigen Templates.

### Schritt B.1 — Views als Klassen

Ergänzen Sie `catalog/views.py`:

```python
# catalog/views.py
from django.shortcuts import render
from django.views import generic

from .models import Author, Book


def index(request):
    num_books = Book.objects.count()
    num_authors = Author.objects.count()
    context = {
        'num_books': num_books,
        'num_authors': num_authors,
    }
    return render(request, 'catalog/index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10
    context_object_name = 'book_list'   # Name der Liste im Template
    # template_name ist hier explizit — entspricht der Standardableitung
    # <app>/<model>_list.html, also catalog/book_list.html.
    template_name = 'catalog/book_list.html'


class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'catalog/book_detail.html'
```

Was die generische `ListView` automatisch erledigt: QuerySet (`Book.objects.all()`), Pagination, Übergabe an das Template als `object_list` bzw. unter dem hier gesetzten `context_object_name`. Die `DetailView` lädt anhand des `pk` aus der URL genau ein `Book`-Objekt (oder liefert 404).

### Schritt B.2 — URLs mit `<int:pk>`

Ergänzen Sie `catalog/urls.py`:

```python
# catalog/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
]
```

Wichtig: `DetailView` erwartet den Parameter exakt unter dem Namen `pk`. `<int:pk>` akzeptiert nur ganzzahlige IDs.

### Schritt B.3 — Template `book_list.html`

Datei `catalog/templates/catalog/book_list.html`:

```html+django
{% extends "base_generic.html" %}

{% block content %}
  <h1>Bücherliste</h1>

  {% if book_list %}
    <ul>
      {% for book in book_list %}
        <li>
          <a href="{% url 'book-detail' book.id %}">{{ book.title }}</a>
          ({{ book.author|default:"unbekannter Autor" }})
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p>Es sind keine Bücher in der Bibliothek vorhanden.</p>
  {% endif %}
{% endblock %}

{% block pagination %}
  {% if is_paginated %}
    <div class="pagination">
      <span class="page-links">
        {% if page_obj.has_previous %}
          <a href="{{ request.path }}?page={{ page_obj.previous_page_number }}">&laquo; zurück</a>
        {% endif %}
        <span class="page-current">
          Seite {{ page_obj.number }} von {{ page_obj.paginator.num_pages }}
        </span>
        {% if page_obj.has_next %}
          <a href="{{ request.path }}?page={{ page_obj.next_page_number }}">weiter &raquo;</a>
        {% endif %}
      </span>
    </div>
  {% endif %}
{% endblock %}
```

Damit der Paginierungs-Block auch erscheint, ergänzen Sie in `base_generic.html` unter dem `content`-Block eine Aufnahmestelle:

```html+django
  <main>
    {% block content %}{% endblock %}
    {% block pagination %}{% endblock %}
  </main>
```

Jetzt, da die Route `books` aus Schritt B.2 existiert, ergänzen Sie in `base_generic.html` den zweiten Navigationslink in der Sidebar:

```html+django
  {% block sidebar %}
    <ul class="sidebar-nav">
      <li><a href="{% url 'index' %}">Startseite</a></li>
      <li><a href="{% url 'books' %}">Alle Bücher</a></li>
    </ul>
  {% endblock %}
```

Der Filter `|default:"unbekannter Autor"` greift nur bei „falsy" Werten. (Für tatsächlich leere Felder wäre `|default_if_none` passender — hier dient `default` als Demonstration eines Template-Filters.)

### Schritt B.4 — Template `book_detail.html`

Datei `catalog/templates/catalog/book_detail.html`:

```html+django
{% extends "base_generic.html" %}

{% block content %}
  <h1>Titel: {{ book.title }}</h1>

  <p><strong>Autor:</strong> {{ book.author|default:"unbekannt" }}</p>
  <p><strong>Zusammenfassung:</strong> {{ book.summary|default:"—" }}</p>
  <p><strong>ISBN:</strong> {{ book.isbn|default:"—" }}</p>

  <div style="margin-left:20px; margin-top:20px">
    <h4>Exemplare</h4>
    {% for copy in book.bookinstance_set.all %}
      <hr>
      <p
        {% if copy.status == 'a' %}style="color:green"
        {% elif copy.status == 'm' %}style="color:orange"
        {% else %}style="color:red"{% endif %}>
        {{ copy.get_status_display }}
      </p>
      {% if copy.status != 'a' %}
        <p><strong>Fällig:</strong> {{ copy.due_back|default:"—" }}</p>
      {% endif %}
      <p class="text-muted"><strong>Imprint:</strong> {{ copy.imprint }}</p>
      <p class="text-muted"><strong>Id:</strong> {{ copy.id }}</p>
    {% empty %}
      <p>Keine Exemplare erfasst.</p>
    {% endfor %}
  </div>
{% endblock %}
```

`book.bookinstance_set.all` nutzt den Reverse-Accessor der ForeignKey-Beziehung (siehe Lab 2). `get_status_display` liefert das Klartext-Label des `choices`-Feldes.

### Schritt B.5 — Vertiefung: `get_queryset()` / `get_context_data()` überschreiben

Generische Views lassen sich gezielt anpassen, ohne den Boilerplate-Nutzen aufzugeben. Beispiel — eine zweite View, die nur Bücher mit „war" im Titel zeigt und zusätzlichen Context liefert:

```python
# catalog/views.py — optionale Vertiefung
class WarBookListView(generic.ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'book_list'

    def get_queryset(self):
        # eigene Filterung statt des Standard-QuerySets Book.objects.all()
        return Book.objects.filter(title__icontains='war')[:5]

    def get_context_data(self, **kwargs):
        # zuerst den Standard-Context holen ...
        context = super().get_context_data(**kwargs)
        # ... dann eigene Werte ergänzen
        context['filter_hinweis'] = 'Gefiltert nach Titel enthält "war".'
        return context
```

Diese View dient nur der Demonstration des Anpassungsmusters; sie muss nicht zwingend verdrahtet werden.

**Erwartet:**

- `http://127.0.0.1:8000/catalog/books/` zeigt eine Liste verlinkter Buchtitel. Bei mehr als 10 Büchern erscheint die Pagination, und `?page=2` zeigt die zweite Seite.
- Ein Klick auf einen Titel führt zu `http://127.0.0.1:8000/catalog/book/<id>/` mit Detail- und Exemplar-Informationen.
- Der Aufruf einer nicht existierenden ID (z. B. `/catalog/book/9999/`) liefert eine **404**-Antwort.

---

## Übung C — Ein Formular mit Validierung

### Aufgabe

Bibliothekare sollen das Rückgabedatum eines ausgeliehenen Exemplars verlängern können. Bauen Sie dazu ein `forms.Form` mit einem Datumsfeld, einer `clean_*`-Validierung (Datum nicht in der Vergangenheit, höchstens 4 Wochen in der Zukunft) und eine View nach dem GET/POST-Muster, die nur mit der passenden Berechtigung erreichbar ist.

### Schritt C.1 — Formularklasse

Datei `catalog/forms.py`:

```python
# catalog/forms.py
import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_('Neues Rückgabedatum (max. 4 Wochen ab heute).'),
    )

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # 1) nicht in der Vergangenheit
        if data < datetime.date.today():
            raise ValidationError(_('Ungültiges Datum — liegt in der Vergangenheit.'))

        # 2) höchstens 4 Wochen in der Zukunft
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Ungültiges Datum — mehr als 4 Wochen voraus.'))

        # validierte (und ggf. bereinigte) Daten immer zurückgeben
        return data
```

Eine `clean_<feldname>`-Methode wird automatisch beim Aufruf von `is_valid()` ausgeführt. Sie muss den bereinigten Wert zurückgeben oder eine `ValidationError` auslösen.

### Schritt C.2 — View nach GET/POST-Muster

Ergänzen Sie `catalog/views.py`:

```python
# catalog/views.py
import datetime

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .forms import RenewBookForm
from .models import BookInstance


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        # gebundenes Formular aus den POST-Daten erzeugen
        form = RenewBookForm(request.POST)

        if form.is_valid():
            # cleaned_data nach erfolgreicher Validierung übernehmen
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # nach erfolgreichem POST immer weiterleiten (PRG-Muster)
            return HttpResponseRedirect(reverse('all-borrowed'))

    else:
        # GET: ungebundenes Formular mit Vorschlagswert (in 3 Wochen)
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }
    return render(request, 'catalog/book_renew_librarian.html', context)
```

Hinweise:

- `@permission_required('catalog.can_mark_returned')` setzt voraus, dass das Modell `BookInstance` diese Permission definiert (in der Meta-Klasse via `permissions = [('can_mark_returned', 'Set book as returned')]`). Falls noch nicht vorhanden, ergänzen Sie sie und führen `makemigrations`/`migrate` aus.
- Der Redirect zeigt auf die Route `all-borrowed`. Falls diese Liste in Ihrem Projekt nicht existiert, leiten Sie ersatzweise auf `reverse('books')` um.
- `get_object_or_404` liefert eine 404-Antwort, wenn die angegebene `BookInstance`-`pk` nicht existiert.

### Schritt C.3 — URL verdrahten

Ergänzen Sie `catalog/urls.py`:

```python
# catalog/urls.py
urlpatterns += [
    path('book/<uuid:pk>/renew/', views.renew_book_librarian, name='renew-book-librarian'),
]
```

Hinweis zum Konverter: Das LocalLibrary-`BookInstance`-Modell verwendet einen `UUIDField` als Primärschlüssel — daher `<uuid:pk>`. Falls Ihr `BookInstance` einen normalen Integer-PK nutzt, verwenden Sie stattdessen `<int:pk>`.

### Schritt C.4 — Template `book_renew_librarian.html`

Datei `catalog/templates/catalog/book_renew_librarian.html`:

```html+django
{% extends "base_generic.html" %}

{% block content %}
  <h1>Exemplar verlängern: {{ book_instance.book.title }}</h1>

  <p>
    <strong>Aktuelles Rückgabedatum:</strong>
    {{ book_instance.due_back|default:"—" }}
  </p>

  <form action="" method="post">
    {% csrf_token %}
    <table>
      {{ form.as_p }}
    </table>
    <input type="submit" value="Absenden">
  </form>

  {% if form.errors %}
    <div class="form-errors" style="color:red">
      <p>Bitte korrigieren Sie die folgenden Fehler:</p>
      {{ form.non_field_errors }}
      {% for field in form %}
        {% for error in field.errors %}
          <p>{{ field.label }}: {{ error }}</p>
        {% endfor %}
      {% endfor %}
    </div>
  {% endif %}
{% endblock %}
```

`{% csrf_token %}` ist bei jedem POST-Formular Pflicht — ohne dieses Tag lehnt Django die Anfrage mit **403** ab. `{{ form.as_p }}` rendert alle Felder inklusive Label, Widget und Feldfehlern; die zusätzliche Fehlerschleife zeigt das manuelle Auslesen von `form.errors`.

**Erwartet:**

- Als angemeldeter Benutzer **mit** der Permission `can_mark_returned`: Aufruf von `http://127.0.0.1:8000/catalog/book/<uuid>/renew/` zeigt das Formular mit vorbelegtem Datum (heute + 3 Wochen).
- Absenden eines Datums in der Vergangenheit oder mehr als 4 Wochen voraus → Formular wird erneut angezeigt mit Fehlermeldung („Ungültiges Datum — liegt in der Vergangenheit." bzw. „… mehr als 4 Wochen voraus.").
- Absenden eines gültigen Datums → Weiterleitung; `due_back` des Exemplars ist in der Datenbank aktualisiert.
- Ohne Berechtigung → Weiterleitung zur Login-Seite (bzw. 403).

---

## Übung D — Statische Dateien & Namespacing-Check

### Aufgabe

Verstehen Sie, warum statische Dateien unter `<app>/static/<app>/` liegen, und prüfen Sie die korrekte Einbindung. Notieren Sie den Unterschied zwischen Entwicklung und Produktion.

### Schritt D.1 — Namespacing prüfen

Ihre Verzeichnisstruktur sollte so aussehen:

```text
catalog/
├── static/
│   └── catalog/          # <- App-Name als Unterordner (Namespacing!)
│       └── styles.css
└── templates/
    ├── base_generic.html
    └── catalog/
        ├── index.html
        ├── book_list.html
        ├── book_detail.html
        └── book_renew_librarian.html
```

Django sammelt im Produktionsfall die Statics **aller** Apps in einem gemeinsamen Verzeichnis. Lägen alle Dateien direkt unter `static/styles.css`, würden gleichnamige Dateien verschiedener Apps kollidieren. Der App-Unterordner (`static/catalog/`) macht den Pfad eindeutig — deshalb auch `{% static 'catalog/styles.css' %}` mit App-Präfix.

### Schritt D.2 — `{% static %}` korrekt verwenden

Im Template wird der Pfad **niemals** hartcodiert, sondern über das Tag aufgelöst:

```html+django
{% load static %}
<link rel="stylesheet" href="{% static 'catalog/styles.css' %}">
```

`{% static %}` setzt das `STATIC_URL`-Präfix davor. Bei `STATIC_URL = 'static/'` ergibt das im Entwicklungsmodus `/static/catalog/styles.css`, das von `django.contrib.staticfiles` automatisch ausgeliefert wird.

### Schritt D.3 — Hinweis Produktion

Im Entwicklungsserver (`runserver`, `DEBUG = True`) liefert Django Statics automatisch aus den App-Ordnern aus. In Produktion ist das **nicht** der Fall — dort sammeln Sie alle Statics einmalig in ein Auslieferungsverzeichnis und lassen sie vom Webserver (nginx o. Ä.) ausliefern:

```python
# locallibrary/settings.py (nur für Produktion relevant)
import os
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

```bash
# sammelt alle App-Statics nach STATIC_ROOT
python manage.py collectstatic
```

`collectstatic` ist ausschließlich ein Produktions-/Deployment-Schritt und in der lokalen Entwicklung mit `DEBUG = True` nicht erforderlich.

**Erwartet:**

- `styles.css` liegt unter `catalog/static/catalog/styles.css`.
- Im gerenderten HTML steht `href="/static/catalog/styles.css"`; der Aufruf dieser URL liefert das CSS (Status 200), kein 404.
- Sie können in eigenen Worten erklären, wofür `collectstatic`/`STATIC_ROOT` da sind und dass sie in der lokalen Entwicklung nicht gebraucht werden.

---

## Checkpoint

Starten Sie den Server und gehen Sie diese Liste durch. Sie sollten alles im Browser nachvollziehen können:

- [ ] **Startseite** (`/catalog/`): erbt sichtbar von `base_generic.html` (Sidebar-Navigation + gestyltes CSS), zeigt die korrekten Bestandszahlen (Bücher/Autoren) aus der Datenbank.
- [ ] **Buchliste** (`/catalog/books/`): zeigt verlinkte Buchtitel; bei > 10 Büchern erscheint die **Pagination**, `?page=2` blättert weiter.
- [ ] **Buchdetail** (`/catalog/book/<id>/`): zeigt Titel, Autor, Zusammenfassung und Exemplarstatus; eine nicht existierende ID liefert **404**.
- [ ] **Renew-Formular** (`/catalog/book/<uuid>/renew/`): mit Berechtigung erreichbar, vorbelegtes Datum.
- [ ] **Validierung greift**: ein **Vergangenheitsdatum** (oder > 4 Wochen voraus) führt zu einem **Validierungsfehler** im Formular, nicht zu einem Absturz.
- [ ] **Gültige Eingabe**: speichert `due_back` und leitet weiter (Post/Redirect/Get).
- [ ] **Statische Dateien**: CSS lädt korrekt über `{% static %}`, kein 404 im Server-Log.

Wenn alle Punkte erfüllt sind, ist die `catalog`-App funktional vollständig: Templates mit Vererbung, generische CBVs gegen Boilerplate, ein validiertes Formular und sauber eingebundene statische Dateien.

> Vergleichen Sie die erwarteten Ausgaben (Screenshots/Konsolenausgaben) mit **EXPECTED_RESULTS.md**.
