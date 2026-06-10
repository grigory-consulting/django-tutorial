





from django.contrib import admin

from .models import Author, Genre, Language, Book, BookInstance

# Register your models here.

# Einfacher Weg

admin.site.register(Genre)
admin.site.register(Language)

class BooksInline(admin.StackedInline):
    """Bücher direkt beim Author bearbeiten"""
    model = Book 

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "date_of_birth", "date_of_death")
    fields = ["first_name", "last_name", ("date_of_birth", "date_of_death"), "cv"]
    inlines = [BooksInline]



class BookInstanceInline(admin.StackedInline):
    """Exemplare direkt in der Buch-Seite bearbeiten."""
    model = BookInstance

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "display_genre")  # display_genre: Methode am Model
    list_filter = ("language",)
    inlines = [BookInstanceInline]

@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ("book", "status", "borrower", "due_back", "ist_ueberfaellig")
    list_filter = ("status", "due_back")
    fieldsets = (
        (None, {"fields": ("book", "id")}),
        ("Verfügbarkeit", {"fields": ("status", "due_back", "borrower")}),
    )

    @admin.display(description="Überfällig?", boolean=True)
    def ist_ueberfaellig(self, obj):
        return obj.overdue