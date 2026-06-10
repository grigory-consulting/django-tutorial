# Labs — Reihenfolge & Abhängigkeiten

Die fünf Labs bauen **strikt aufeinander auf** und werden in dieser Reihenfolge bearbeitet (Lab 1 → Lab 5). Jedes Lab setzt den Endzustand des vorigen voraus. Durchgehendes Projekt: **MDN LocalLibrary** (Projekt `locallibrary`, App `catalog`).

| # | Datei | Thema | Baut auf | Tag |
|---|---|---|---|---|
| 1 | [`lab1_setup_and_views.md`](lab1_setup_and_views.md) | Setup, Projekt, App, URLs, erste View | — (Start) | Tag 1 |
| 2 | [`lab2_orm_queries.ipynb`](lab2_orm_queries.ipynb) | Modelle, ORM-Abfragen, Admin (Notebook) | Lab 1 | Tag 2 |
| 3 | [`lab3_migrations_tests.md`](lab3_migrations_tests.md) | Migration-Rollback, Datenmigration, Fixtures, Seed, Unit-Tests | Lab 2 | Tag 2 |
| 4 | [`lab4_templates_forms_cbv.md`](lab4_templates_forms_cbv.md) | Templates, Formulare, generische CBVs | Lab 2 (+ Lab 3) | Tag 3 |
| 5 | [`lab5_rest_realtime_prod.md`](lab5_rest_realtime_prod.md) | REST-API + Token-Auth, CSV-Import, i18n, Produktion | Lab 4 | Tag 3 |
| 6 | [`lab6_realtime_checklist.md`](lab6_realtime_checklist.md) | **Optional/Bonus:** Echtzeit-Prüfliste mit Django Channels (WebSockets) | Lab 5 | Tag 3 / Take-home |

## Was nach was, und warum

1. **Lab 1** legt das Fundament: lauffähiges Projekt, App `catalog`, URL→View. Ohne das läuft nichts Weiteres.
2. **Lab 2** definiert die Modelle (`Author`, `Genre`, `Language`, `Book`, `BookInstance`) und erkundet das ORM interaktiv im Notebook. Erzeugt `0001_initial` und Beispieldaten.
3. **Lab 3** arbeitet auf genau diesen Modellen weiter: Rollback, Datenmigration (neue Spalte), Fixtures, Seed-Command, erster Unit-Test. Der View-Test überspringt sich hier noch selbst, weil die `books`-Route erst in **Lab 4** entsteht.
4. **Lab 4** baut die Oberfläche: Template-Vererbung, Renew-Formular, generische `ListView`/`DetailView`. Legt die `books`-Route an, womit der in Lab 3 übersprungene View-Test grün wird.
5. **Lab 5** öffnet die App nach außen: REST-API mit Token-Auth, CSV-Import, i18n und Produktions-Checkliste. Setzt die Views/Templates aus Lab 4 voraus.
6. **Lab 6 (optional)** ist ein eigenständiges Bonus-Lab: eine voll lauffähige geteilte Echtzeit-Prüfliste mit Django Channels (WebSockets, Gruppen-Broadcast, Persistenz). Legt eine **neue App `checklist`** an und steht für sich; setzt nur ein lauffähiges Projekt voraus, nicht die REST-API aus Lab 5.

## Tag-Zuordnung (3-Tage-Schulung)

- **Tag 1:** Lab 1
- **Tag 2:** Lab 2 + Lab 3
- **Tag 3:** Lab 4 + Lab 5
- **Optional/Take-home:** Lab 6 (wenn an Tag 3 Zeit bleibt, sonst zum Nacharbeiten)

Die Labs 1 bis 5 tragen oben eine **Reihenfolge-Navigation** (Schritt X von 5, Vorher/Danach); Lab 6 ist als optionales Bonus-Lab markiert. Trainer-Sollzustände stehen in [`../EXPECTED_RESULTS.md`](../EXPECTED_RESULTS.md), fertige Referenzstände in [`../snapshots/`](../snapshots/).
