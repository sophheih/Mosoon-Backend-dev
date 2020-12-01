from rest_framework_mongoengine.serializers import DocumentSerializer

from mosoon_massage_backend.models import Order


class OrderSerializer(DocumentSerializer):
    class Meta:
        model = Order
        fields = '__all__'
