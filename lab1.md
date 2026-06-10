---
marp: true
---

python -m venv .venv

In Windows 

.venv\Scripts\activate.bat 

.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

python -m pip install "django==5.2.*"


django-admin --version

django-admin startproject locallibrary .  

python manage.py startapp catalog


## Registrierung
python manage.py check


python -m pip install cookiecutter

cookiecutter https://github.com/cookiecutter/cookiecutter-django



python manage.py makemigrations catalog

python manage.py showmigrations catalog


python manage.py migrate catalog zero  


python manage.py migrate catalog 0001

python manage.py makemigrations catalog --empty -n backfill_publication_year





pip install gunicorn whitenoise

python manage.py collectstatic

gunicorn locallibrary.wsgi:application --bind 127.0.0.1:8000

http://127.0.0.1:8000/static/admin/css/base.css


python manage.py createsuperuser



set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python -Xutf8

python manage.py dumpdata catalog --indent 2 -o catalog\fixtures\catalog.json




app_template -> *.py-tpl schreiben 
python manage.py startapp my_app --template app_template

pip install djangorestframework

python manage.py drf_create_token grigo

pip install "channels[daphne]"


python manage.py makemigrations catalog
python manage.py migrate
python manage.py shell -c "from catalog.models import ChecklistItem; [ChecklistItem.objects.create(text=t) for t in ['Repo geklont', 'Migrationen OK', 'Server gestartet', 'Tests OK']]"



python manage.py makemessages -l en