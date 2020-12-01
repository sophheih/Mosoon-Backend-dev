from django.urls import path

from order_api import views

urlpatterns = [
    path('', views.orders_handler),
    path('<slug:order_id>', views.order_handler),
    path('complete/<slug:header>/<slug:payload>/<slug:signature>',
         views.payment_complete),
]
