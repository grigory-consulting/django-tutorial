from django import forms

from .models import Author


class AuthorForm(forms.ModelForm):
    """Formular zum Anlegen eines Autors samt hochgeladener Datei (cv)."""

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "cv"]
