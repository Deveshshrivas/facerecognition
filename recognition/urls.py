from django.urls import path
from . import views

urlpatterns = [
    path('videos/', views.upload_video, name='upload_video'),
    path('images/', views.upload_image, name='upload_image'),
    path('check-person/', views.check_person_in_group, name='check_person_in_group'),
]