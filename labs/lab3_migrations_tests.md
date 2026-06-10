# Lab 3 — Migrationen, Fixtures, Seed-Command & Tests

> **Lab 3** der Django-Einsteiger-Intensiv-Schulung (Django 5.2). Durchgehendes Projekt: **MDN LocalLibrary**, Projekt `locallibrary`, App `catalog`. Baut direkt auf **Lab 2** (`lab2_orm_queries.ipynb`) auf: Die Modelle `Author`, `Genre`, `Language`, `Book` und `BookInstance` sind angelegt, `0001_initial` ist migriert, und es liegen Beispieldaten in der Datenbank (3 Bücher, 3 Autor:innen, 3 Exemplare).
>
> **Reihenfolge:** Schritt 3 von 5 · Vorher: **Lab 2** (Modelle, ORM & Admin, `lab2_orm_queries.ipynb`) · Danach: **Lab 4** (Templates, Formulare & CBVs, `lab4_templates_forms_cbv.md`).

## Lernziel

Nach diesem Lab können Sie:

- **Migrationen rückgängig machen** und gezielt auf einen bestimmten Stand fahren (`showmigrations`, `migrate <app> <nummer>`, `migrate <app> zero`),
- eine **neue Spalte** sauber in drei Schritten einführen und bestehende Einträge per **Datenmigration** (`RunPython`) befüllen,
- Testdaten als **Fixtures** sichern und wieder laden (`dumpdata` / `loaddata`),
- reproduzierbare Dev-Daten über einen eigenen **Management-Command** (`manage.py seed`) erzeugen,
- einen **Unit-Test** mit `TestCase` und dem Test-`Client` schreiben und ausführen.

Vergleichen Sie Ihre Ergebnisse am Ende mit **EXPECTED_RESULTS.md**.

### Voraussetzungen

- Sie haben **Lab 2** (`lab2_orm_queries.ipynb`) abgeschlossen: Modelle definiert, `makemigrations catalog` + `migrate` ausgeführt, Beispieldaten angelegt.
- Die virtuelle Umgebung aus Lab 1 ist aktiv (Django installiert).
- Alle `manage.py`-Befehle führen Sie im **Projektordner** aus — dort, wo `manage.py` liegt.

> **Hinweis zu Migrationsnummern:** Die Nummern (`0002`, `0003`, …) hängen davon ab, wie viele Migrationen Sie bereits erzeugt haben. Nach **Lab 2** existiert nur `0001_initial`. Lesen Sie die **tatsächlichen** Dateinamen aus der Ausgabe von `makemigrations` bzw. `showmigrations` ab und setzen Sie sie an den passenden Stellen ein. Die Befehle unten gehen von diesem Ausgangsstand aus.

---

## Übung A — Migration-Rollback ansehen

### Aufgabe

Verschaffen Sie sich einen Überblick über den Migrationsstand der App `catalog`, verstehen Sie, wie Sie gezielt vor- und zurückfahren, und üben Sie einen sicheren Rollback auf `0001` mit anschließendem Vorwärtsfahren auf den neuesten Stand.

### Schritt A.1 — Migrationsstand anzeigen

```bash
python manage.py showmigrations catalog
```

**Erwartet:** Eine Liste der `catalog`-Migrationen. Angewendete Migrationen sind mit `[X]` markiert, noch offene mit `[ ]`. Direkt nach **Lab 2**:

```text
catalog
 [X] 0001_initial
```

### Schritt A.2 — Gezielt auf einen Stand fahren (Theorie)

`migrate` fährt das Schema **vorwärts oder rückwärts** auf einen Zielstand:

```bash
# Auf einen bestimmten Stand zurück: kehrt alle SPÄTEREN Migrationen um.
# Beispiel (sobald spätere Migrationen existieren): zurück auf 0001
python manage.py migrate catalog 0001

# ALLE catalog-Migrationen zurücknehmen (Tabellen der App werden entfernt):
python manage.py migrate catalog zero
```

- `migrate <app> <nummer>` setzt die App **genau** auf den Stand dieser Migration. Liegt der aktuelle Stand höher, werden die dazwischenliegenden Migrationen **rückwärts** ausgeführt; liegt er tiefer, **vorwärts**.
- `migrate <app> zero` nimmt **alle** Migrationen der App zurück — das Schema der App ist danach leer.

> **Warum geht das überhaupt?** Jede Migration ist umkehrbar: Zu jeder `Create`/`AddField`-Operation kennt Django die Gegenoperation (`Delete`/`RemoveField`). Bei Datenmigrationen (Übung B) geben **Sie** die Rückwärtsrichtung an.

> **Warnung — Datenverlust:** **Rückwärtsmigrieren kann Daten verlieren.** Wird beim Rollback eine Spalte oder Tabelle gedroppt (`RemoveField` / `DeleteModel`), sind die enthaltenen Werte unwiederbringlich weg. In Produktion nur mit Bedacht und **nur nach einem Backup**. In dieser Übung arbeiten wir auf der lokalen SQLite-Entwicklungsdatenbank — unkritisch.

### Schritt A.3 — Sicherer Rollback auf `0001` und zurück

Solange nur `0001_initial` existiert, ist `0001` bereits der niedrigste echte Stand. Den vollständigen Rollback/Roll-forward-Zyklus üben wir daher mit `zero` (alles zurück) und anschließendem Vorwärtsfahren:

```bash
# 1) Alle catalog-Migrationen zurücknehmen (entfernt die catalog-Tabellen samt Daten)
python manage.py migrate catalog zero

# 2) Stand prüfen — jetzt sind alle catalog-Migrationen offen
python manage.py showmigrations catalog

# 3) Wieder vorwärts auf den neuesten Stand
python manage.py migrate catalog
```

**Erwartet:**

- Nach Schritt 1 meldet Django das Rückwärts-Unapplying, z. B. `Unapplying catalog.0001_initial... OK`.
- Nach Schritt 2 steht die Migration wieder als offen da:

  ```text
  catalog
   [ ] 0001_initial
  ```

- Nach Schritt 3 ist `0001_initial` erneut angewendet (`Applying catalog.0001_initial... OK`), und die Tabellen existieren wieder — **aber leer**: Der `zero`-Rollback hat die `catalog`-Tabellen und damit Ihre Beispieldaten gelöscht.

> **Daten weg?** Das ist nach `migrate catalog zero` erwartbar (siehe Warnung oben). Sie stellen die Beispieldaten in Übung C wieder her (Fixture laden) oder in Übung D (Seed-Command). Wer den Datenverlust vermeiden möchte, überspringt Schritt A.3 und liest nur Schritt A.2.

---

## Übung B — Neue Spalte `publication_year` (3-Schritte-Pattern)

### Aufgabe

`Book` soll ein Erscheinungsjahr bekommen. Bestehende Bücher haben noch keinen Wert. Führen Sie das Feld in **drei** kleinen, umkehrbaren Schritten ein, statt in einem riskanten: (a) Feld nullbar hinzufügen und migrieren, (b) bestehende Zeilen per Datenmigration befüllen, (c) optional auf `null=False` verschärfen.

### Schritt B.1 — Feld hinzufügen und migrieren

Öffnen Sie `catalog/models.py` und ergänzen Sie im Modell `Book` ein Feld (z. B. direkt nach `title`):

```python
class Book(models.Model):
    """Ein Buch (das Werk, nicht die physische Kopie)."""
    title = models.CharField(max_length=200)
    publication_year = models.IntegerField(null=True, blank=True)
    # ... die übrigen Felder (author, summary, isbn, genre, language) bleiben unverändert
```

`null=True` ist hier entscheidend: Bestehende Zeilen bekommen den Wert `NULL`, ohne dass Django nach einem One-off-Default fragt. (Versuchen Sie es testweise **ohne** `null=True`, fragt `makemigrations` interaktiv nach einem Default für die vorhandenen Zeilen — brechen Sie dann mit `Strg+C` ab und fügen Sie `null=True` hinzu.)

```bash
python manage.py makemigrations catalog
python manage.py migrate
```

**Erwartet:** `makemigrations` erzeugt eine neue Migrationsdatei und meldet sinngemäß:

```text
Migrations for 'catalog':
  catalog/migrations/0002_book_publication_year.py
    - Add field publication_year to book
```

`migrate` wendet sie an (`Applying catalog.0002_book_publication_year... OK`).

Sehen Sie sich die generierte Migration an:

```bash
python manage.py sqlmigrate catalog 0002
```

Der Kern der Datei `catalog/migrations/0002_book_publication_year.py` sieht so aus:

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="publication_year",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
```

> Notieren Sie den **tatsächlichen** Dateinamen (hier `0002_book_publication_year`) — Sie brauchen ihn gleich als Abhängigkeit der Datenmigration.

### Schritt B.2 — Datenmigration: bestehende Einträge befüllen (`RunPython`)

Erzeugen Sie eine **leere** Migration mit sprechendem Namen:

```bash
python manage.py makemigrations catalog --empty -n backfill_publication_year
```

**Erwartet:** Eine leere Migrationsdatei, z. B. `catalog/migrations/0003_backfill_publication_year.py`, mit einer leeren `operations`-Liste und der Abhängigkeit auf `0002_book_publication_year`.

Öffnen Sie diese Datei und ersetzen Sie ihren Inhalt durch:

```python
from django.db import migrations


def set_default_year(apps, schema_editor):
    # WICHTIG: historische Modellversion über apps.get_model holen,
    # NICHT "from catalog.models import Book" verwenden.
    Book = apps.get_model("catalog", "Book")
    Book.objects.filter(publication_year__isnull=True).update(publication_year=2000)


class Migration(migrations.Migration):

    dependencies = [
        # An den TATSÄCHLICHEN Namen aus Schritt B.1 anpassen:
        ("catalog", "0002_book_publication_year"),
    ]

    operations = [
        migrations.RunPython(set_default_year, migrations.RunPython.noop),
    ]
```

Wenden Sie sie an:

```bash
python manage.py migrate
```

**Erwartet:** `Applying catalog.0003_backfill_publication_year... OK`. Alle Bücher, die zuvor `NULL` hatten, tragen jetzt `2000` (bzw. den von Ihnen gewählten Wert).

> **Warum `apps.get_model(...)` statt direktem Import?** Eine Migration läuft gegen den **historischen** Modellzustand zu diesem Migrationszeitpunkt — nicht gegen Ihr aktuelles `models.py`. `apps.get_model("catalog", "Book")` liefert genau diese historische Version. Ein direkter Import (`from catalog.models import Book`) zöge das **heutige** Modell heran und bräche, sobald sich das Modell später ändert (z. B. ein Feld dazukommt, das es zum Migrationszeitpunkt noch nicht gab).
>
> `migrations.RunPython.noop` als zweites Argument ist die **Rückwärtsrichtung**: Beim Zurückmigrieren ist hier nichts zu tun (die Spalte selbst entfernt Schritt `0002` rückwärts). Ohne ein zweites Argument wäre die Datenmigration nicht umkehrbar, und ein Rollback über diesen Punkt hinaus würde fehlschlagen.

Prüfung (optional, im Notebook oder über `python manage.py shell`):

```python
from catalog.models import Book
print(Book.objects.filter(publication_year__isnull=True).count())   # => 0
print(Book.objects.values_list("title", "publication_year"))
```

### Schritt B.3 — Optional: Feld auf `null=False` verschärfen

Da jetzt **alle** Zeilen einen Wert haben, könnten Sie das Feld verpflichtend machen. Setzen Sie dazu in `models.py` `null=True, blank=True` auf einen Pflichtwert und geben Sie einen `default` an (sonst fragt `makemigrations` erneut nach einem One-off-Default):

```python
publication_year = models.IntegerField(default=2000)
```

```bash
python manage.py makemigrations catalog   # erzeugt z. B. 0004_alter_book_publication_year
python manage.py migrate
```

**Erwartet:** Eine weitere Migration (`- Alter field publication_year on book`), die das Feld auf `NOT NULL` umstellt. Dieser Schritt ist nur sicher, **weil** Schritt B.2 vorher alle Zeilen befüllt hat — genau das ist der Sinn des 3-Schritte-Patterns: Schema-Änderung und Daten-Befüllung sind getrennt und jeweils umkehrbar.

> Dieser Schritt ist optional. Für den Rest des Labs genügt das nullbare Feld aus B.1/B.2. Lassen Sie B.3 weg, wenn Sie das Feld nullbar belassen möchten.

---

## Übung C — Fixtures (`dumpdata` / `loaddata`)

### Aufgabe

Sichern Sie den aktuellen Datenbestand der App `catalog` als versionierbares JSON-Fixture und stellen Sie ihn nach einem Leeren der Daten wieder her.

### Schritt C.1 — Fixture-Verzeichnis anlegen und Daten exportieren

Django sucht Fixtures standardmäßig in `<app>/fixtures/`. Legen Sie den Ordner an und exportieren Sie:

**macOS / Linux:**

```bash
mkdir -p catalog/fixtures
python manage.py dumpdata catalog --indent 2 -o catalog/fixtures/catalog.json
```

**Windows (PowerShell):**

```powershell
mkdir catalog\fixtures
python manage.py dumpdata catalog --indent 2 -o catalog\fixtures\catalog.json
```

**Erwartet:** Die Datei `catalog/fixtures/catalog.json` entsteht. `--indent 2` macht sie menschenlesbar; `-o` schreibt direkt in die Datei (plattformneutral, ohne `>`-Umleitung). Der Inhalt ist eine Liste von Objekten der Form:

```json
[
  {
    "model": "catalog.author",
    "pk": 1,
    "fields": {
      "first_name": "J. R. R.",
      "last_name": "Tolkien",
      "date_of_birth": "1892-01-03",
      "date_of_death": null
    }
  },
  {
    "model": "catalog.book",
    "pk": 1,
    "fields": {
      "title": "Der Hobbit",
      "publication_year": 2000,
      "author": 1,
      "...": "..."
    }
  }
]
```

(Exakte Reihenfolge, PKs und Anzahl hängen von Ihren Daten ab. `dumpdata catalog` exportiert **alle** Modelle der App: Author, Genre, Language, Book und BookInstance.)

### Schritt C.2 — Daten leeren und aus dem Fixture laden

Leeren Sie die Daten (eine der beiden Varianten genügt) und laden Sie das Fixture zurück:

```bash
# Variante 1: Ein einzelnes Exemplar löschen, um den Reimport sichtbar zu machen
#   (im Admin unter Book instances oder per shell). Reicht für eine schnelle Demonstration.

# Variante 2: Alle catalog-Tabellen leeren (drastischer) und neu aufbauen
python manage.py migrate catalog zero
python manage.py migrate

# Daten aus dem Fixture wieder einspielen — Dateiname genügt, Django sucht in <app>/fixtures/
python manage.py loaddata catalog.json
```

**Erwartet:** `loaddata` meldet sinngemäß `Installed <N> object(s) from 1 fixture(s)`, wobei `<N>` der Anzahl der exportierten Objekte entspricht (Autoren + Genres + Sprachen + Bücher + Exemplare). Der Bestand ist anschließend wieder vollständig.

> **Wichtig:** Sie übergeben `loaddata catalog.json` — **nur den Dateinamen**, keinen Pfad. Django durchsucht automatisch die `fixtures/`-Ordner aller installierten Apps (und ggf. `FIXTURE_DIRS`). Liegt das Fixture unter `catalog/fixtures/catalog.json`, wird es gefunden. Geben Sie hingegen einen Pfad an, behandelt Django das Argument als Pfad.
>
> Falls Sie in Übung B das Feld `publication_year` ergänzt haben, muss das Schema beim `loaddata` zu den Feldern im Fixture passen — exportieren Sie das Fixture daher **nach** Übung B (so wie hier in der Reihenfolge angelegt).

---

## Übung D — Seed-Management-Command (reproduzierbare Dev-Daten)

### Aufgabe

Schreiben Sie einen eigenen `manage.py`-Befehl `seed`, der ein paar Autoren, Bücher und Exemplare **idempotent** anlegt. So startet jede Entwicklungsumgebung mit denselben sinnvollen Beispieldaten — reproduzierbar und ohne manuelles Klicken im Admin.

### Schritt D.1 — Verzeichnisstruktur anlegen

Management-Commands erwartet Django unter `<app>/management/commands/`. Beide Ebenen brauchen ein `__init__.py`, damit sie als Python-Pakete gelten:

**macOS / Linux:**

```bash
mkdir -p catalog/management/commands
touch catalog/management/__init__.py
touch catalog/management/commands/__init__.py
```

**Windows (PowerShell):**

```powershell
mkdir catalog\management\commands
New-Item catalog\management\__init__.py
New-Item catalog\management\commands\__init__.py
```

Die Zielstruktur:

```text
catalog/
└── management/
    ├── __init__.py
    └── commands/
        ├── __init__.py
        └── seed.py
```

> Der Name der Datei (`seed.py`) wird zum Namen des Befehls (`manage.py seed`). Fehlt eines der `__init__.py`, findet Django den Befehl nicht (`Unknown command: 'seed'`).

### Schritt D.2 — `seed.py` schreiben

Datei `catalog/management/commands/seed.py`:

```python
# catalog/management/commands/seed.py
from datetime import date

from django.core.management.base import BaseCommand

from catalog.models import Author, Book, BookInstance, Genre, Language


class Command(BaseCommand):
    help = "Legt reproduzierbare Beispieldaten für den Katalog an (idempotent)."

    def handle(self, *args, **options):
        # get_or_create -> idempotent: mehrfaches Ausführen erzeugt keine Duplikate.
        sf, _ = Genre.objects.get_or_create(name="Science-Fiction")
        de, _ = Language.objects.get_or_create(name="Deutsch")

        le_guin, _ = Author.objects.get_or_create(
            first_name="Ursula K.",
            last_name="Le Guin",
            defaults={"date_of_birth": date(1929, 10, 21)},
        )

        book, _ = Book.objects.get_or_create(
            isbn="9780060512750",   # unique -> dient als idempotenter Match-Schlüssel
            defaults={
                "title": "The Dispossessed",
                "author": le_guin,
                "language": de,
                "summary": "Eine Physikerin zwischen zwei gegensätzlichen Welten.",
            },
        )
        book.genre.set([sf])

        BookInstance.objects.get_or_create(
            book=book,
            imprint="Gollancz, 2002",
            defaults={"status": "a"},
        )

        self.stdout.write(self.style.SUCCESS(
            f"Seed fertig: {Author.objects.count()} Autor:innen, "
            f"{Book.objects.count()} Bücher, "
            f"{BookInstance.objects.count()} Exemplare."
        ))
```

### Schritt D.3 — Befehl ausführen

```bash
python manage.py seed
```

**Erwartet:** Eine grün hervorgehobene Erfolgszeile (durch `self.style.SUCCESS`), z. B.:

```text
Seed fertig: 4 Autor:innen, 4 Bücher, 4 Exemplare.
```

Die konkreten Zahlen hängen davon ab, welche Daten bereits in der Datenbank lagen. Entscheidend ist die **Idempotenz**: Führen Sie `python manage.py seed` ein zweites Mal aus, **ändern sich die Zahlen nicht** — `get_or_create` findet die vorhandenen Objekte wieder, statt Duplikate anzulegen.

> Tipp: Möchten Sie sehen, wie der Befehl in der Liste auftaucht, rufen Sie `python manage.py help` auf — unter `[catalog]` erscheint `seed`. `python manage.py help seed` zeigt den `help`-Text aus der Klasse.

---

## Übung E — Unit-Test mit `TestCase` und `Client`

### Aufgabe

Schreiben Sie zwei Testklassen in `catalog/tests.py`: einen **Modell-Test**, der ein `Book` anlegt und `__str__` sowie eine Relation prüft, und einen **View-Test**, der über den Test-`Client` die Buchlisten-Seite aufruft und Status sowie Inhalt prüft. Führen Sie die Tests aus.

### Schritt E.1 — Tests schreiben

Ersetzen Sie den Inhalt von `catalog/tests.py` durch:

```python
# catalog/tests.py
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from catalog.models import Author, Book


class BookModelTests(TestCase):
    """Testet das Book-Modell — läuft eigenständig, ohne URLs/Views."""

    def setUp(self):
        # setUp() läuft VOR jeder Testmethode und legt frische Objekte an.
        self.author = Author.objects.create(first_name="Stanisław", last_name="Lem")
        self.book = Book.objects.create(
            title="Solaris",
            author=self.author,
            isbn="9780156027601",
            summary="Erstkontakt mit einem Ozean-Planeten.",
        )

    def test_str_ist_titel(self):
        # __str__ des Book gibt laut Modell den Titel zurück.
        self.assertEqual(str(self.book), "Solaris")

    def test_author_relation(self):
        # FK-Relation: das Buch kennt seine:n Autor:in ...
        self.assertEqual(self.book.author.last_name, "Lem")
        # ... und der Reverse-Accessor (book_set) findet das Buch zurück.
        self.assertIn(self.book, self.author.book_set.all())

    def test_author_str_format(self):
        # Author.__str__ ist "Nachname, Vorname".
        self.assertEqual(str(self.author), "Lem, Stanisław")


class BookListViewTests(TestCase):
    """
    Testet die Buchlisten-View über den Test-Client.

    Setzt die Route name='books' aus Lab 4 voraus. Existiert sie noch
    nicht, überspringt sich dieser Test selbst (skipTest); der
    Modell-Test oben läuft unabhängig davon.
    """

    def setUp(self):
        author = Author.objects.create(first_name="Ursula K.", last_name="Le Guin")
        Book.objects.create(
            title="The Left Hand of Darkness",
            author=author,
            isbn="9780441478125",
            summary="Geschlecht und Gesellschaft auf Gethen.",
        )

    def test_buchliste_status_und_inhalt(self):
        try:
            url = reverse("books")
        except NoReverseMatch:
            self.skipTest("Route 'books' existiert noch nicht (kommt in Lab 4).")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # assertContains prüft Status 200 UND das Vorkommen des Texts im Body.
        self.assertContains(response, "The Left Hand of Darkness")
```

Hinweise:

- `setUp()` läuft **vor jeder** Testmethode neu — jeder Test startet mit denselben frischen Objekten und ist von den anderen unabhängig.
- `self.client` ist ein in `TestCase` eingebauter Browser-Ersatz: `self.client.get(...)` setzt einen Request an Ihre URL-Konfiguration ab, ohne dass ein Server laufen muss.
- `reverse("books")` löst die **benannte** Route in ihre URL auf (statt sie fest zu verdrahten). Da diese Route erst in Lab 4 angelegt wird, fängt der View-Test ein `NoReverseMatch` ab und meldet sich selbst als übersprungen, so bleibt der Modell-Test grün, auch wenn Sie Lab 4 noch nicht bearbeitet haben.

### Schritt E.2 — Tests ausführen

```bash
python manage.py test catalog
```

**Erwartet (vor Lab 4, `books`-Route fehlt noch):** Die Modell-Tests laufen durch, der View-Test wird übersprungen. Die Ausgabe enthält ein `s` (skipped) und endet mit `OK`:

```text
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...s
----------------------------------------------------------------------
Ran 4 tests in 0.0XXs

OK (skipped=1)
Destroying test database for alias 'default'...
```

**Erwartet (nach Lab 4, `books`-Route vorhanden):** Alle vier Tests laufen durch:

```text
Ran 4 tests in 0.0XXs

OK
```

(Die genaue Laufzeit und die Reihenfolge der `.`/`s` variieren.)

> **Separate Test-DB:** Django legt für den Testlauf automatisch eine **eigene** Datenbank an (Zeile `Creating test database...`), führt alle Migrationen darauf aus, lässt die Tests laufen und **verwirft die DB am Ende** (`Destroying test database...`). Ihre Entwicklungsdaten bleiben dadurch unberührt — die in `setUp()` angelegten Objekte existieren nur während des Tests. Bei SQLite läuft die Test-DB standardmäßig im Arbeitsspeicher, was die Tests beschleunigt.

---

## Checkpoint

Gehen Sie diese Liste durch:

- [ ] **Rollback verstanden** (Übung A): `showmigrations catalog` zeigt `[X]`/`[ ]`-Status; Sie können erklären, was `migrate catalog <nummer>`, `migrate catalog zero` und das anschließende Vorwärtsfahren bewirken — und warum ein Rollback Daten verlieren kann.
- [ ] **Neue Spalte in 3 Schritten** (Übung B): `publication_year` ist als nullbares Feld hinzugefügt und migriert (`0002…`); eine Datenmigration (`0003_backfill_publication_year`) hat die bestehenden Bücher per `RunPython` + `apps.get_model(...)` befüllt; `Book.objects.filter(publication_year__isnull=True).count()` ist `0`.
- [ ] **Fixtures** (Übung C): `catalog/fixtures/catalog.json` existiert (lesbar dank `--indent 2`); nach Leeren der Daten stellt `loaddata catalog.json` den Bestand vollständig wieder her.
- [ ] **Seed-Command** (Übung D): `catalog/management/commands/seed.py` existiert (samt beider `__init__.py`); `python manage.py seed` gibt eine grüne Erfolgsmeldung aus und ist **idempotent** (zweiter Aufruf ändert die Zahlen nicht).
- [ ] **Unit-Test** (Übung E): `catalog/tests.py` enthält `BookModelTests` und `BookListViewTests`; `python manage.py test catalog` läuft mit `OK` (View-Test übersprungen, solange die `books`-Route fehlt); die separate Test-DB wird angelegt und wieder verworfen.
- [ ] Erwartete Ausgaben abgeglichen mit **EXPECTED_RESULTS.md**.

**Geschafft.** Sie beherrschen jetzt den vollständigen Datenlebenszyklus einer Django-App: Schema rückwärts/vorwärts fahren, Spalten samt Bestandsdaten sicher einführen, Daten sichern/laden, reproduzierbar seeden und das Ganze mit Tests absichern.
