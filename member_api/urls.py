from django.urls import path

from member_api import views

urlpatterns = [
    path('login', views.login),
    path('register', views.register),
    path('', views.member),
    path('<slug:user_id>', views.member_id),
    path('address/<slug:address_id>', views.address_withid),
    path('address/', views.address_mem),


]
