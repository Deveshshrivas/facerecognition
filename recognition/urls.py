from django.urls import path
from . import views

urlpatterns = [
    path('videos/', views.upload_video, name='upload_video'),
]