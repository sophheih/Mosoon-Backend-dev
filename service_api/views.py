import boto3
from django.http.response import JsonResponse
from mongoengine.errors import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from mosoon_massage_backend.models import Service, Member, Image
from service_api.serializers import ServiceSerializer
from config import config
from utils.jsonview import json_view


@json_view
@api_view(['GET', 'POST'])
def service_handler(request):
    if request.method == 'GET':
        return service_get_all(request)
    elif request.method == 'POST':
        return service_create(request)


@json_view
@api_view(['GET', 'DELETE', 'PUT'])
def service_id_handler(request, service_id):
    if request.method == 'GET':
        return service_get(request, service_id)
    elif request.method == 'DELETE':
        return service_delete(request, service_id)
    elif request.method == 'PUT':
        return service_update(request, service_id)


@json_view
@api_view(['PUT', 'DELETE'])
def service_image_handler(request, service_id):
    if request.method == 'PUT':
        return service_image_add(request, service_id)
    elif request.method == 'DELETE':
        return service_image_delete(request, service_id)


def service_get_all(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin'):
        pass
    elif token_payload.get('id'):
        try:
            user_id = token_payload.get('id')
            user = Member.objects.get(id=user_id)

        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    skip = request.GET.get('skip', '0')
    limit = request.GET.get('limit', '20')
    skip = int(skip) if str(skip).isnumeric() else 0
    limit = int(limit) if str(limit).isnumeric() else 20
    services = Service.objects.all().skip(skip).limit(limit)
    service_serializer = ServiceSerializer(services, many=True)
    return JsonResponse(service_serializer.data, safe=False, status=status.HTTP_200_OK)


def service_get(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin'):
        pass
    elif token_payload.get('id'):
        try:
            user_id = token_payload.get('id')
            user = Member.objects.get(id=user_id)

        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return JsonResponse(
            {'message': 'The service does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValidationError:
        return JsonResponse(
            {'message': 'The service does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )

    service_serializer = ServiceSerializer(service)
    return JsonResponse(service_serializer.data, safe=False, status=status.HTTP_200_OK)


def service_create(request):
    image_url = request.POST.getlist('image_url')
    if len(image_url) == 0: image_url = request.POST.getlist('image_url[]')
    title = request.POST.get('title', None)
    short_description = request.POST.get('short_description', None)
    long_description = request.POST.get('long_description', None)
    duration = request.POST.get('duration', None)
    price = request.POST.get('price', None)
    vip_per = request.POST.get('vip_per', '1')
    nor_per = request.POST.get('nor_per', '1')
    minus = request.POST.get('minus', '0')

    if title is None:
        msg = {'message': 'body parameter "title" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif short_description is None:
        msg = {'message': 'body parameter "short_description" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif long_description is None:
        msg = {'message': 'body parameter "long_description" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif duration is None:
        msg = {'message': 'body parameter "duration" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif price is None:
        msg = {'message': 'body parameter "price" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif not str(minus).isnumeric():
        msg = {'message': 'body parameter "minus" should be an integer'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    try:
        vip_per = float(vip_per)
        nor_per = float(nor_per)
    except ValueError:
        msg = {
            'message': 'body parameter "vip_per" or "nor_per" should be a float number'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        for url in image_url:
            Image.objects.get(url=url)
        for url in image_url:
            Image.increaseUsage(url, 1)
    except Image.DoesNotExist:
        msg = {'message': 'The image_url "' + url +'" is not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    service = ServiceSerializer(data={
        'title': title,
        'image_url': image_url,
        'short_description': short_description,
        'long_description': long_description,
        'duration': duration,
        'price': price,
        'vip_per': vip_per,
        'nor_per': nor_per,
        'minus': minus
    })
    if service.is_valid():
        service.save()
        return JsonResponse(service.data)
    return JsonResponse(service.errors, status=status.HTTP_400_BAD_REQUEST)


def service_update(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({"message": "Permission Denied"}, status=status.HTTP_403_FORBIDDEN)

    image_url = request.POST.getlist('image_url')
    if len(image_url) == 0: image_url = request.POST.getlist('image_url[]')

    title = request.POST.get('title', None)
    short_description = request.POST.get('short_description', None)
    long_description = request.POST.get('long_description', None)
    duration = request.POST.get('duration', None)
    price = request.POST.get('price', None)
    vip_per = request.POST.get('vip_per', None)
    nor_per = request.POST.get('nor_per', None)
    minus = request.POST.get('minus', None)
    if not minus is None and not str(minus).isdigit():
        msg = {'message': 'body parameter "minus" should be an integer'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    try:
        if not vip_per is None:
            vip_per = float(vip_per)
        if not nor_per is None:
            nor_per = float(nor_per)
    except ValidationError:
        msg = {
            'message': 'body parameter "vip_per" or "nor_per" should be a float number'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        msg = {'message': 'The service does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The service id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        for url in image_url:
            Image.objects.get(url=url)
    except Image.DoesNotExist:
        msg = {'message': 'The image_url "' + url +'" is not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    if not title is None:
        service.title = title
    if not short_description is None:
        service.short_description = short_description
    if not long_description is None:
        service.long_description = long_description
    if not duration is None:
        service.duration = duration
    if not price is None:
        service.price = price
    if not vip_per is None:
        service.vip_per = vip_per
    if not nor_per is None:
        service.nor_per = nor_per
    if not minus is None:
        service.minus = minus

    for url in image_url:
        Image.increaseUsage(url, 1, ignore_check_exist=True)
    for url in service.image_url:
        Image.increaseUsage(url, -1, ignore_check_exist=True)

    service.image_url = image_url
    service.save()
    return JsonResponse(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)

def service_content_update(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({"message": "Permission Denied"}, status=status.HTTP_403_FORBIDDEN)

    title = request.POST.get('title', None)
    short_description = request.POST.get('short_description', None)
    long_description = request.POST.get('long_description', None)
    duration = request.POST.get('duration', None)
    price = request.POST.get('price', None)
    vip_per = request.POST.get('vip_per', None)
    nor_per = request.POST.get('nor_per', None)
    minus = request.POST.get('minus', None)
    if not minus is None and not str(minus).isdigit():
        msg = {'message': 'body parameter "minus" should be an integer'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    try:
        if not vip_per is None:
            vip_per = float(vip_per)
        if not nor_per is None:
            nor_per = float(nor_per)
    except ValidationError:
        msg = {
            'message': 'body parameter "vip_per" or "nor_per" should be a float number'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        msg = {'message': 'The service does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The service id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    if not title is None:
        service.title = title
    if not short_description is None:
        service.short_description = short_description
    if not long_description is None:
        service.long_description = long_description
    if not duration is None:
        service.duration = duration
    if not price is None:
        service.price = price
    if not vip_per is None:
        service.vip_per = vip_per
    if not nor_per is None:
        service.nor_per = nor_per
    if not minus is None:
        service.minus = minus

    service.save()
    return JsonResponse(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)


def service_delete(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        service = Service.objects.get(id=service_id)
        for url in service.image_url:
            Image.increaseUsage(url, -1, ignore_check_exist=True)
    except Service.DoesNotExist:
        msg = {'message': 'The service does not exist'}
        return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    service.delete()
    msg = {'message': 'The service was deleted successfully!'}
    return JsonResponse(msg, status=status.HTTP_202_ACCEPTED)


def service_image_add(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        msg = {'message': 'Permission Denied'}
        return JsonResponse(msg, status=status.HTTP_403_FORBIDDEN)

    image_url = request.POST.get('image_url', None)
    if image_url is None:
        msg = {'message': 'body parameter "image_url" should be given'}
        return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)

    try:
        Service.objects.get(id=service_id)
        Image.increaseUsage(image_url, 1)
        result = Service.objects(id=service_id).update_one(
            add_to_set__image_url=image_url, full_result=True)
        if (result.modified_count == 0):
            Image.increaseUsage(image_url, -1)
            msg = {'message': 'The image is already in this service'}
            return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except Service.DoesNotExist:
        msg = {'message': 'The service does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except Image.DoesNotExist:
        msg = {'message': 'The image is not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse(ServiceSerializer(Service.objects.get(id=service_id)).data, status=status.HTTP_201_CREATED)


def service_image_delete(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    image_url = request.POST.get('image_url', None)
    if image_url is None:
        msg = {'message': 'body parameter "image_url" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        service = Service.objects.get(id=service_id)
        result = Service.objects(id=service_id).update_one(
            pull__image_url=image_url, full_result=True)
        if (result.modified_count == 1):
            Image.increaseUsage(image_url, -1)
        else:
            msg = {'message': 'The image does not exist in this service'}
            return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    except Service.DoesNotExist:
        msg = {'message': 'The service does not exist'}
        return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    except Image.DoesNotExist:
        pass
    return JsonResponse(ServiceSerializer(Service.objects.get(id=service_id)).data, status=status.HTTP_202_ACCEPTED)
