from rest_framework_mongoengine import serializers

from mosoon_massage_backend.models import Therapist


class TherapistSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Therapist
        fields = '__all__'
