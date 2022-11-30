from django.urls import path

from .views import Author, Tech

app_name = 'about'

urlpatterns = [
    path('author/', Author.as_view(), name='author'),
    path('tech/', Tech.as_view(), name='tech')
]
