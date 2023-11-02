# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('upload-extract-entity/', views.upload_file_extract_entity, name='upload_file_extract_entity'),
    path('update/', views.update, name='update'),
]
