

from rest_framework_mongoengine import serializers

from mosoon_massage_backend.models import Member, Address


class MemberSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Member
        fields = '__all__'


class AdminMemberSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Member
        exclude = ['password_md5']


class MemMemberSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Member
        fields = ['real_name', 'gender', 'email',
                  'birthday', 'password_md5', 'cellphone']


class AddressSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Address
        fields = '__all__'
