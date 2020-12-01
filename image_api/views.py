import uuid
import base64
import datetime
import boto3
from bson.objectid import ObjectId
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework import status
from django.http.response import JsonResponse
from mosoon_massage_backend.models import Image
from image_api.serializers import ImageSerializer
from config import config
from utils.jsonview import json_view
from utils.awsS3Saver import awsS3Saver


@json_view
@api_view(['GET', 'POST'])
def image_handler(request):
    if request.method == 'GET':
        return image_get_all(request)
    elif request.method == 'POST':
        return image_create(request)


@json_view
@api_view(['GET', 'DELETE'])
def image_id_handler(request, image_id):
    if request.method == 'GET':
        return image_get(request, image_id)
    elif request.method == 'DELETE':
        return image_delete(request, image_id)


def image_create(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    photo = request.FILES.get('image', None)
    ext = request.data.get('ext', None)

    if photo is None:
        return JsonResponse(
            {'message': 'image file should be given in form-data'},
            status=status.HTTP_400_BAD_REQUEST)
    elif ext is None:
        return JsonResponse(
            {'message': '"ext" parameter should be given in form-data'},
            status=status.HTTP_400_BAD_REQUEST)

    if not ext in ['jpg', 'jpeg', 'png', 'gif']:
        return JsonResponse(
            {'message': '"ext" parameter in form-data should be "jpg" or "jpeg" or "png" or "gif"'},
            status=status.HTTP_400_BAD_REQUEST)

    unique_file_name = base64.urlsafe_b64encode(
        uuid.uuid1().bytes).rstrip(b'=').decode('ascii')
    file_key = 'image/%s.%s' % (unique_file_name, ext)
    url = awsS3Saver.upload(file_key, photo)

    serializer = ImageSerializer(data={
        'url': url, 'usage': 0
    })
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def image_get(request, image_id):
    try:
        image = Image.objects.get(id=image_id)
        serializer = ImageSerializer(image)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
    except Image.DoesNotExist:
        return JsonResponse(
            {'message': 'The image does not exist'},
            status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return JsonResponse(
            {'message': 'Invalid ID'},
            status=status.HTTP_400_BAD_REQUEST)


def image_get_all(request):
    image_filter = {}
    image_id = request.GET.get('id', '')
    url = request.GET.get('url', '')
    skip = request.GET.get('skip', '0')
    limit = request.GET.get('limit', '20')
    if not image_id == '':
        image_filter['_id'] = ObjectId(image_id)
    if not url == '':
        image_filter['url'] = url
    skip = int(skip) if str(skip).isnumeric() else 0
    limit = int(limit) if str(limit).isnumeric() else 20

    images = Image.objects(__raw__=image_filter).skip(skip).limit(limit)

    serializer = ImageSerializer(images, many=True)
    return JsonResponse(serializer.data, safe=False)


def image_delete(request, image_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        return JsonResponse(
            {'message': 'The image does not exist'},
            status=status.HTTP_404_NOT_FOUND)

    if image['usage'] == 0:
        image.delete()
        file_name = image['url'].split('/')[-1]
        awsS3Saver.remove('image/%s' % (file_name))
        return JsonResponse({'message': 'The image was deleted successfully!'}, status=status.HTTP_200_OK)
    return JsonResponse({'message': 'The image is used in other api'}, status=status.HTTP_400_BAD_REQUEST)
