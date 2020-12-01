from rest_framework_mongoengine import serializers
from mosoon_massage_backend.models import Calendar

class CalendarSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Calendar
        fields = '__all__'
        