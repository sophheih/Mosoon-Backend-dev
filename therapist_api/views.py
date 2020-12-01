import boto3
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from mongoengine.errors import ValidationError
from rest_framework import status
from django.http.response import JsonResponse
from mosoon_massage_backend.models import Therapist, Member, Image
from therapist_api.serializers import TherapistSerializer
from config import config
from utils.jsonview import json_view


@json_view
@api_view(['GET', 'POST'])
def therapist_handler(request):
    if request.method == 'GET':
        return therapist_get_all(request)
    elif request.method == 'POST':
        return therapist_create(request)


@json_view
@api_view(['GET', 'DELETE', 'PUT'])
def therapist_id_handler(request, therapist_id):
    if request.method == 'GET':
        return therapist_get(request, therapist_id)
    elif request.method == 'DELETE':
        return therapist_delete(request, therapist_id)
    elif request.method == 'PUT':
        return therapist_update(request, therapist_id)


def therapist_get_all(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin'):
        pass
    elif token_payload.get('id'):
        try:
            user_id = token_payload.get('id')
            user = Member.objects.get(id=user_id)
        except Member.DoesNotExist:
            msg = {'message': 'The member does not exist'}
            return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    skip = request.GET.get('skip', '0')
    limit = request.GET.get('limit', '20')
    skip = int(skip) if str(skip).isnumeric() else 0
    limit = int(limit) if str(limit).isnumeric() else 20
    therapists = Therapist.objects.all().skip(skip).limit(limit)
    serializer = TherapistSerializer(therapists, many=True)
    return JsonResponse(serializer.data, safe=False)


def therapist_get(request, therapist_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin'):
        pass
    elif token_payload.get('id'):
        try:
            user_id = token_payload.get('id')
            user = Member.objects.get(id=user_id)
        except Member.DoesNotExist:
            msg = {'message': 'The member does not exist'}
            return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        therapist = Therapist.objects.get(id=therapist_id)
    except Therapist.DoesNotExist:
        msg = {'message': 'The therapist does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The therapist id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    serializer = TherapistSerializer(therapist)
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


def therapist_create(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    image_url = request.POST.get('image_url', None)
    name = request.POST.get('name', None)
    gender = request.POST.get('gender', None)
    description = request.POST.get('description', None)

    if image_url is None:
        msg = {'message': 'body parameter "image_url" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    if name is None:
        msg = {'message': 'body parameter "name" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    if gender is None:
        msg = {'message': 'body parameter "gender" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    if description is None:
        msg = {'message': 'body parameter "description" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        Image.increaseUsage(image_url, 1)
    except Image.DoesNotExist:
        msg = {'message': 'The image does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    serializer = TherapistSerializer(data={
        'image_url': image_url,
        'name': name,
        'gender': gender,
        'description': description
    })

    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data)

    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def therapist_delete(request, therapist_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        therapist = Therapist.objects.get(id=therapist_id)
    except Therapist.DoesNotExist:
        msg = {'message': 'The therapist already deleted or never created'}
        return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    except ValidationError:
        msg = {'message': 'The therapist id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    therapist.delete()

    try:
        Image.increaseUsage(therapist['image_url'], -1)
    except Image.DoesNotExist:
        pass
    msg = {'message': 'The therapist was deleted successfully!'}
    return JsonResponse(msg, status=status.HTTP_202_ACCEPTED)


def therapist_update(request, therapist_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    image_url = request.POST.get('image_url', None)
    name = request.POST.get('name', None)
    gender = request.POST.get('gender', None)
    description = request.POST.get('description', None)

    if image_url is None and name is None and gender is None and description is None:
        msg = {'message': 'body parameter "image_url" or "name" or "content" or "description" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        therapist = Therapist.objects.get(id=therapist_id)
    except Therapist.DoesNotExist:
        msg = {'message': 'The therapist does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The therapist id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    if not name is None:
        therapist.name = name
    if not gender is None:
        therapist.gender = gender
    if not description is None:
        therapist.description = description
    if not image_url is None:
        try:
            old_image_url = therapist['image_url']
            Image.increaseUsage(image_url, 1)
            therapist.image_url = image_url
        except Image.DoesNotExist:
            msg = {'message': 'The image does not exist'}
            return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
        try:
            Image.increaseUsage(old_image_url, -1)
        except Image.DoesNotExist:
            pass
    therapist.save()
    return JsonResponse(TherapistSerializer(therapist).data, status=status.HTTP_201_CREATED)
