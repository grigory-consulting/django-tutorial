import csv

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Author, Book



# import requests

# data = requests.get('https://api.example.com/books').json()
# for item in data:
#     Book.objects.get_or_create(
#         isbn=item['isbn'],
#         defaults={'title': item['title']},
#     )









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