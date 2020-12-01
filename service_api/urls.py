from django.urls import path

from service_api import views

urlpatterns = [
    path('', views.service_handler),
    path('<slug:service_id>', views.service_id_handler),
    path('<slug:service_id>/image', views.service_image_handler),
]
