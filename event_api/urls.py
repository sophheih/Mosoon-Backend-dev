from django.urls import path

from event_api import views

urlpatterns = [
    path('', views.event_handler),
    path('<slug:event_id>', views.event_id_handler),
]
