from django.urls import include, path

from mosoon_massage_backend.views import get_system_status

urlpatterns = [
    path('', get_system_status),
    path('member/', include('member_api.urls')),
    path('service/', include('service_api.urls')),
    path('event/', include('event_api.urls')),
    path('therapist/', include('therapist_api.urls')),
    path('reservation/', include('reservation_api.urls')),
    path('calendar/', include('calendar_api.urls')),
    path('order/', include('order_api.urls')),
    path('image/', include('image_api.urls'))
]
