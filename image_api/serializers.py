from rest_framework_mongoengine import serializers

from mosoon_massage_backend.models import Image


class ImageSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Image
        fields = '__all__'
