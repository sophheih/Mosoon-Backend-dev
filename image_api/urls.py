from django.urls import path

from image_api import views

urlpatterns = [
    path('', views.image_handler),
    path('<slug:image_id>', views.image_id_handler),
]
