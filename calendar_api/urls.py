from django.urls import path
from calendar_api import views

urlpatterns = [
    path('<slug:calendar_id>', views.calendar_withid),
    path('', views.calendar_handler),

]
