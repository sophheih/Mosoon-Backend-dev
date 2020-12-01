
from rest_framework_mongoengine import serializers

from mosoon_massage_backend.models import Service


class ServiceSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Service
        fields = '__all__'
