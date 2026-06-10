import uuid
from datetime import date

from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class ChecklistItem(models.Model):
    """Ein abhakbarer Punkt fuer die Echtzeit-Checkliste (Realtime-Lab)."""
    text = models.CharField(max_length=200)
    done = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"[{'x' if self.done else ' '}] {self.text}"


class Genre(models.Model):
    name = models.CharField(
        max_length=200, 
        unique=True,
        help_text="Geben Sie ein Buchgenre ein." ,      
    )

    def __str__(self):
        return self.name
    
class Language(models.Model):
    """Die Sprache eines Buches (De, En, ... )"""
    name = models.CharField(
        max_length=200, 
        unique=True,
        help_text="Geben Sie die Sprache ein." ,      
    )

    def __str__(self):
        return self.name 

class Author(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(verbose_name="died", null=True, blank=True) # verbose_name = died
    cv = models.FileField(upload_to="cv/", blank=True)  # hochgeladene Datei (Upload-Demo)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"
    
class Book(models.Model):
    title = models.CharField(max_length=200)
    publication_year = models.IntegerField(null=True, blank=True)
    # Foreign Key (FK) 
    author = models.ForeignKey(Author, on_delete=models.RESTRICT, null=True) 
    summary = models.TextField(max_length=1000, help_text="Kurzbeschreibung")
    isbn = models.CharField(verbose_name="ISBN", max_length=13, unique=True)

    genre = models.ManyToManyField(Genre, help_text="Genre für dieses Buch")
    language = models.ForeignKey(Language, on_delete = models.SET_NULL, null=True, blank=True)

    class Meta: 
        ordering = ["title"]
    
    def display_genre(self): # später in Admin-list_display einbinden 
        return ", ".join(g.name for g in self.genre.all()[:3])
    
    def __str__(self):
        return self.title
    

class BookInstance(models.Model):
    """konkrete physische Kopie eines Buches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    book = models.ForeignKey(Book, on_delete=models.RESTRICT, null=True)
    due_back = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    LOAN_STATUS = (
        
        ("m", "Maintenance"),
        ("o", "On loan"),
        ("a", "Available"),
        ("r", "Reserved"),
    )
    status = models.CharField(
        max_length=1, choices=LOAN_STATUS, blank=True,
        default="m", help_text="Verfügbarkeit des Exemplars.",
    )

    class Meta:
        ordering = ["due_back"]

    # anstatt b.overdue() -> b.overdue

    @property
    def overdue(self):
        return bool(self.due_back and date.today() > self.due_back)
    
    def __str__(self):
        return f"{self.id} ({self.book.title if self.book else "-"})"
    

