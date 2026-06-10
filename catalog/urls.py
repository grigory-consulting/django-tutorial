from django.urls import include, path
from . import views

from rest_framework.routers import DefaultRouter
from .api import BookViewSet
from rest_framework.authtoken.views import obtain_auth_token



urlpatterns = [
    path("", views.index, name="index"),
    path('books/', views.BookListView.as_view(), name='books'),
    path('checklist/', views.checklist, name='checklist'),
    path('author/new/', views.author_create, name='author-create'),
    path('author/<int:pk>/created/', views.author_created, name='author-created'),
]

router = DefaultRouter()
router.register(r'api/books', BookViewSet)

urlpatterns += [
    path('', include(router.urls)),
]

urlpatterns += [
    path('api/token/', obtain_auth_token, name='api-token'),
]