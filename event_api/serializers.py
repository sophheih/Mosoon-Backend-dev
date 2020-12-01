from rest_framework_mongoengine import serializers

from mosoon_massage_backend.models import Event


class EventSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Event
        fields = '__all__'
