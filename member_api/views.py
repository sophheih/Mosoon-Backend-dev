import hashlib
from datetime import datetime

from django.http.response import JsonResponse
from mongoengine.errors import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from member_api.serializers import MemberSerializer,  MemMemberSerializer, AdminMemberSerializer, AddressSerializer
from mosoon_massage_backend.models import Member, Address
from utils.jsonview import json_view
from datetime import datetime
from rest_framework.renderers import JSONRenderer


@json_view
@api_view(['GET'])
def member(request):
    if request.method == 'GET':
        token_payload = request.META.get('TOKEN_PAYLOAD')
        if token_payload.get('admin'):
            skip = request.GET.get('skip', '0')
            limit = request.GET.get('limit', '20')
            skip = int(skip) if str(skip).isnumeric() else 0
            limit = int(limit) if str(limit).isnumeric() else 20
            user_info = Member.objects.all().skip(skip).limit(limit)

            try:
                user_info_serializer = AdminMemberSerializer(
                    user_info, many=True)
                return JsonResponse(
                    user_info_serializer.data, safe=False
                )
            except:
                return JsonResponse({"message": "User Data In Database Is Invalid."}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return JsonResponse(
                {'message': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )


@json_view
@api_view(['POST'])
def register(request):
    user_data = JSONParser().parse(request)

    if len(user_data["password"]) >= 8:
        password_md5 = hashlib.md5()
        password_md5.update(
            user_data['password'].encode(encoding='utf-8'))
        user_data["password_md5"] = password_md5.hexdigest()
        del user_data['password']
    else:
        return JsonResponse({"message": "password unqualified"},
                            status=status.HTTP_400_BAD_REQUEST)
    ts = datetime.now().timestamp()
    if int(user_data['birthday']) > ts:
        return JsonResponse(
            {'message': 'Date is not avaliable.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    user_data['birthday'] = datetime.fromtimestamp(
        int(user_data['birthday']))

    if len(user_data['cellphone']) > 10:
        return JsonResponse(
            {'message': 'Cellphone has no more than 10 characters.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    user_data['token_time'] = datetime.now()

    serializer = MemberSerializer(data=user_data)
    if serializer.is_valid():
        try:
            Member.objects.get(username=user_data["username"])
        except Member.DoesNotExist:
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse({"message": "user already exists."}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@json_view
@api_view(['GET', 'PUT', 'DELETE'])
def member_id(request, user_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')

    if request.method == 'GET':
        if token_payload.get('admin') or token_payload.get('id'):

            try:
                user = Member.objects.get(id=user_id)
            except Member.DoesNotExist:
                return JsonResponse(
                    {'message': 'The user does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValidationError:
                return JsonResponse(
                    {'message': 'Invaildated ID.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if token_payload.get('id'):
                member = Member.objects.get(id=token_payload.get('id'))
                if user.id != member.id:
                    return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_400_BAD_REQUEST)
            serializer = AdminMemberSerializer(user)
            return JsonResponse(
                serializer.data, safe=False
            )

        else:
            return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        if token_payload.get('admin') or token_payload.get('id'):
            new_user_data = JSONParser().parse(request)

            try:
                user = Member.objects.get(id=user_id)
            except Member.DoesNotExist:
                return JsonResponse(
                    {'message': 'The user does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if token_payload.get('id'):
                member = Member.objects.get(id=token_payload.get('id'))
                if user.id != member.id:
                    return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_400_BAD_REQUEST)
            if 'password' in new_user_data:
                if len(new_user_data["password"]) >= 8:
                    password_md5 = hashlib.md5()
                    password_md5.update(
                        new_user_data['password'].encode(encoding='utf-8'))
                    new_user_data["password_md5"] = password_md5.hexdigest()
                    del new_user_data['password']
                else:
                    return JsonResponse({"message": "password unqualified"},
                                        status=status.HTTP_400_BAD_REQUEST)

                new_user_data['token_time'] = datetime.now()
            if 'birthday' in new_user_data:
                ts = datetime.now().timestamp()
                if int(new_user_data['birthday']) > ts:
                    return JsonResponse(
                        {'message': 'Date is not avaliable.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                new_user_data["birthday"] = datetime.fromtimestamp(
                    int(new_user_data["birthday"]))
            if 'cellphone' in new_user_data:
                if len(new_user_data['cellphone']) > 10:
                    return JsonResponse(
                        {'message': 'Cellphone has no more than 10 characters.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            if token_payload.get('admin'):
                serializer = MemberSerializer(user, data=new_user_data)
            else:
                serializer = MemMemberSerializer(user, data=new_user_data)

            if serializer.is_valid():
                serializer.save()

                return JsonResponse(serializer.data, safe=False, status=status.HTTP_201_CREATED, json_dumps_params={'ensure_ascii': False})
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse(
            {'message': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    elif request.method == 'DELETE':
        try:
            user = Member.objects.get(id=user_id)
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The user does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        user.delete()
        return JsonResponse(
            {'message': 'The user was deleted successfully!'}, status=status.HTTP_200_OK
        )


@ json_view
@ api_view(['POST'])
def login(request):
    data = JSONParser().parse(request)
    username = data['username']
    password = data['password']

    try:
        user = Member.objects.get(username=username)
    except Member.DoesNotExist:
        return JsonResponse(
            {'message': 'Username or password is wrong.'},
            status=status.HTTP_404_NOT_FOUND
        )

    md5_encrypt = hashlib.md5()
    md5_encrypt.update(password.encode("utf-8"))
    compare_password = md5_encrypt.hexdigest()

    if user.password_md5 == compare_password:

        get_user_data_serializer = AdminMemberSerializer(user)
        return JsonResponse({"user": get_user_data_serializer.data, "token": user.token})

    return JsonResponse(
        {'message': 'Username or password is wrong.'},
        status=status.HTTP_404_NOT_FOUND
    )


@ json_view
@ api_view(['PUT', 'DELETE', 'GET'])
def address_withid(request, address_id):
    if request.method == 'PUT':
        return update_address(request, address_id)
    elif request.method == 'DELETE':
        return del_address(request, address_id)
    elif request.method == 'GET':
        return get_address(request, address_id)


def update_address(request, address_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not (token_payload.get('admin') or token_payload.get('id')):

        return JsonResponse(
            {'message': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    try:
        address = Address.objects.get(id=address_id)
    except Address.DoesNotExist:
        return JsonResponse(
            {'message': 'The address does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    if token_payload.get('id'):

        try:
            user = Member.objects.get(id=token_payload.get('id'))
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The user does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        print(user.id, address.member_id)
        if user.id != address.member_id:
            return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN)

    address_data = JSONParser().parse(request)

    serializer = AddressSerializer(address, data=address_data)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def del_address(request, address_id):

    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not (token_payload.get('admin') or token_payload.get('id')):
        return JsonResponse(
            {'message': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    try:
        address = Address.objects.get(id=address_id)
    except Address.DoesNotExist:
        return JsonResponse(
            {'message': 'The address does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    if token_payload.get('id'):
        try:
            user = Member.objects.get(id=token_payload.get('id'))
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The user does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        if user.id != address.member_id:
            return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN)

    address.delete()
    return JsonResponse({'message': 'The address has been deleted.'}, status=status.HTTP_201_CREATED)


def get_address(request, address_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not (token_payload.get('admin') or token_payload.get('id')):
        return JsonResponse(
            {'message': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    try:
        address = Address.objects.get(id=address_id)
    except Address.DoesNotExist:
        return JsonResponse(
            {'message': 'The address does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    if token_payload.get('id'):
        try:
            user = Member.objects.get(id=token_payload.get('id'))
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The user does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        if user.id != address.member_id:
            return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN)
    serializer = AddressSerializer(address)
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


@ json_view
@ api_view(['POST', 'GET'])
def address_mem(request):

    if request.method == 'POST':
        token_payload = request.META.get('TOKEN_PAYLOAD')
        try:
            user = Member.objects.get(id=token_payload.get('id'))
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The user does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        address_data = JSONParser().parse(request)
        address_data['member_id'] = token_payload.get('id')
        serializer = AddressSerializer(data=address_data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        token_payload = request.META.get('TOKEN_PAYLOAD')
        if token_payload.get('admin'):
            try:
                memberid = request.GET.get('memberid')
                try:
                    user = Member.objects.get(id=memberid)
                except Member.DoesNotExist:
                    return JsonResponse(
                        {'message': 'The user does not exist'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                try:
                    address_data = Address.objects(member_id=memberid)
                except Address.DoesNotExist:
                    return JsonResponse(
                        {'message': 'The user does not have any address'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                serializer = AddressSerializer(address_data, many=True)
                return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
            except:
                skip = request.GET.get('skip', '0')
                limit = request.GET.get('limit', '20')
                skip = int(skip) if str(skip).isnumeric() else 0
                limit = int(limit) if str(limit).isnumeric() else 20
                addresses = Address.objects.all().skip(skip).limit(limit)
                try:
                    serializer = AddressSerializer(addresses, many=True)
                    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
                except Address.DoesNotExist:
                    return JsonResponse(
                        {'message': 'The user does not have any address'},
                        status=status.HTTP_404_NOT_FOUND
                    )
        elif token_payload.get('id'):

            try:
                user = Member.objects.get(id=token_payload.get('id'))
            except Member.DoesNotExist:
                return JsonResponse(
                    {'message': 'The user does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )

            memberid = request.GET.get('memberid')
            if str(memberid) != str(user.id):
                return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN)
            try:
                address_data = Address.objects(member_id=user.id)
            except Address.DoesNotExist:
                return JsonResponse(
                    {'message': 'The user does not have any address'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = AddressSerializer(address_data, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

        else:
            return JsonResponse(
                {'message': 'Permission Denied'},
                status=status.HTTP_404_NOT_FOUND
            )
