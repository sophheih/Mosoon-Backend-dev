import datetime
from datetime import timedelta
import boto3
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework import status
from mongoengine.errors import ValidationError
from django.http.response import JsonResponse
from mosoon_massage_backend.models import Event, Member, Image
from event_api.serializers import EventSerializer
from config import config
from utils.jsonview import json_view
from utils.awsS3Saver import awsS3Saver


@json_view
@api_view(['GET', 'POST'])
def event_handler(request):
    if request.method == 'GET':
        return event_get_all(request)
    elif request.method == 'POST':
        return event_new(request)


@json_view
@api_view(['GET', 'DELETE', 'PUT'])
def event_id_handler(request, event_id):
    if request.method == 'GET':
        return event_get(request, event_id)
    elif request.method == 'DELETE':
        return event_delete(request, event_id)
    elif request.method == 'PUT':
        return event_update(request, event_id)


def event_update(request, event_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    title = request.POST.get('title', None)
    image_url = request.POST.get('image_url', None)
    content = request.POST.get('content', None)
    begin_date = request.POST.get('begin_date', None)
    end_date = request.POST.get('end_date', None)

    if not begin_date is None and not str(begin_date).isnumeric():
        msg = {'message': 'body parameter "begin_date" should be a number'},
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif not end_date is None and not str(begin_date).isnumeric():
        msg = {'message': 'body parameter "end_date" should be a number'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif int(end_date) <= datetime.datetime.now().timestamp():
        msg = {'message': 'The end date is not qulified.'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        msg = {'message': 'The event does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The event id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    if not title is None:
        event.title = title
    if not content is None:
        event.content = content
    if not begin_date is None:
        begin_date = datetime.datetime.fromtimestamp(int(begin_date))
        event.begin_date = begin_date
    if not end_date is None:
        end_date = datetime.datetime.fromtimestamp(int(end_date))
        event.end_date = end_date

    if not image_url is None:
        try:
            Image.increaseUsage(image_url, 1)
            Image.increaseUsage(event['image_url'], -1,
                                ignore_check_exist=True)
            event.image_url = image_url
        except Image.DoesNotExist:
            msg = {'message': 'The image does not exist'}
            return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    event.save()
    return JsonResponse(EventSerializer(event).data, status=status.HTTP_201_CREATED)


def event_get(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        msg = {'message': 'The event does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The event id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    serializer = EventSerializer(event)
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


def event_delete(request, event_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        msg = {'message': 'The event does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The event id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    event.delete()

    try:
        Image.increaseUsage(event['image_url'], -1)
    except Image.DoesNotExist:
        pass

    msg = {'message': 'The event was deleted successfully!'}
    return JsonResponse(msg, status=status.HTTP_202_ACCEPTED)


def event_get_all(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin'):
        pass
    elif token_payload.get('id'):
        try:
            user_id = token_payload.get('id')
            Member.objects.get(id=user_id)
        except Member.DoesNotExist:
            msg = {'message': 'The member does not exist'}
            return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    skip = request.GET.get('skip', '0')
    limit = request.GET.get('limit', '20')
    skip = int(skip) if str(skip).isnumeric() else 0
    limit = int(limit) if str(limit).isnumeric() else 20
    active = request.GET.get('active', None)

    if active != None:
        active = int(active)
        now = datetime.datetime.now()
        if active == 1:
            events = Event.objects(__raw__={
                'begin_date': {'$lte': now},
                'end_date': {'$gte': now}
            }).skip(skip).limit(limit)
            print(events)
        elif active == 0:
            events = Event.objects(__raw__={
                'end_date': {'$lte': now}
            }).skip(skip).limit(limit)
    else:
        events = Event.objects.all().skip(skip).limit(limit)
    serializer = EventSerializer(events, many=True)
    return JsonResponse(serializer.data, safe=False)


def event_new(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    image_url = request.POST.get('image_url', None)
    title = request.POST.get('title', None)
    content = request.POST.get('content', None)
    begin_date = request.POST.get('begin_date', None)
    end_date = request.POST.get('end_date', None)

    if image_url is None:
        return JsonResponse(
            {'message': 'body parameter "image_url" should be given'},
            status=status.HTTP_400_BAD_REQUEST)

    if title is None:
        return JsonResponse(
            {'message': 'body parameter "title" should be given'},
            status=status.HTTP_400_BAD_REQUEST)
    elif content is None:
        return JsonResponse(
            {'message': 'body parameter "content" should be given'},
            status=status.HTTP_400_BAD_REQUEST)
    elif begin_date is None or not str(begin_date).isnumeric():
        return JsonResponse(
            {'message': 'body parameter "begin_date" should be a number'},
            status=status.HTTP_400_BAD_REQUEST)
    elif end_date is None or not str(end_date).isnumeric():
        return JsonResponse(
            {'message': 'body parameter "end_date" should be a number'},
            status=status.HTTP_400_BAD_REQUEST)

    if int(end_date) <= datetime.datetime.now().timestamp():
        msg = {'message': 'The end date is not qulified.'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    begin_date_f = datetime.datetime.fromtimestamp(int(begin_date))
    end_date_f = datetime.datetime.fromtimestamp(int(end_date))
    begin_date = datetime.datetime.fromtimestamp(int(begin_date)+8*3600)
    end_date = datetime.datetime.fromtimestamp(int(end_date)+8*3600)

    try:
        Image.increaseUsage(image_url, 1)
    except Image.DoesNotExist:
        msg = {'message': 'The image does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    serializer = EventSerializer(data={
        'title': title,
        'content': content,
        'begin_date': begin_date,
        'end_date': end_date,
        'image_url': image_url,
    })

    serializer_2 = EventSerializer(data={
        'title': title,
        'content': content,
        'begin_date': begin_date_f,
        'end_date': end_date_f,
        'image_url': image_url,
    })
    if serializer.is_valid():
        serializer.save()
    if serializer_2.is_valid():
        return JsonResponse(serializer_2.data)

    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
