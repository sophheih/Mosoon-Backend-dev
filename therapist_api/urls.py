from django.urls import path

from therapist_api import views

urlpatterns = [
    path('', views.therapist_handler),
    path('<slug:therapist_id>', views.therapist_id_handler),
]
