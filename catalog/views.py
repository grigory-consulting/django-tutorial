from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import generic

from .models import Author, Book, ChecklistItem
from .forms import AuthorForm
# Create your views here.

def author_create(request):
    if request.method == "POST":
        # WICHTIG: request.FILES mitgeben, sonst kommt die Datei nicht an.
        form = AuthorForm(request.POST, request.FILES)
        if form.is_valid():
            author = form.save()
            return redirect("author-created", pk=author.pk)
    else:
        form = AuthorForm()
    return render(request, "catalog/author_form.html", {"form": form})


def author_created(request, pk):
    return render(request, "catalog/author_created.html", {"author": Author.objects.get(pk=pk)})

def checklist(request):
    # Nur die Seite ausliefern; das Umschalten laeuft danach ueber den WebSocket.
    return render(request, "catalog/checklist.html", {"items": ChecklistItem.objects.all()})

def index(request):

    num_books = Book.objects.count()
    num_authors = Author.objects.count()

    context = {
        "num_books": num_books,
        "num_authors": num_authors,
    }
    #return HttpResponse("Willkommen in der LocalLibrary! StatReloader funktioniert sehr gut.")
    return render(request, "catalog/index.html", context=context)

class BookListView(generic.ListView):
    model = Book 
    paginate_by = 3 # Max 10 auf einer Seite
    context_object_name = 'book_list'
    template_name = "catalog/book_list.html" # hier ist explizit und optional


def checklist(request):
    return render(request, "catalog/checklist.html", {"items": ChecklistItem.objects.all()})