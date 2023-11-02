# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('complete/', views.complete, name='complete'),
    path('complete-translation/', views.complete_translation, name='complete-translation'),
]
