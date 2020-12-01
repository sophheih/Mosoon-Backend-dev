from rest_framework_mongoengine import serializers

from mosoon_massage_backend.models import Reservation


class ReservationSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'


class GetReservationSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Reservation
        exclude = ['buffer_start', 'buffer_end']
