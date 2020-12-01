from django.urls import path
from reservation_api import views

urlpatterns = [
    path('', views.reservation_handler),
    path('new', views.reservation_new),
    path('<slug:reservation_id>', views.reservation_withid),
]
