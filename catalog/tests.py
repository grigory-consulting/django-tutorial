from django.test import TestCase

# Create your tests here.


from catalog.models import Author, Book

class BookModelTests(TestCase):

    def setUp(self):
        # läuft VOR jeder Testmethode und hier legt man neue/frische Objekte an
        self.author = Author.objects.create(first_name="Stanislaw", last_name="Lem")
    
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
        self.assertEqual(str(self.author), "Lem, Stanislaw")
