from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from calendar_api.serializers import CalendarSerializer
from mosoon_massage_backend.models import Therapist
from mosoon_massage_backend.models import Calendar
from utils.jsonview import json_view
from datetime import datetime


@json_view
@api_view(['GET', 'POST'])
def calendar_handler(request):
    if request.method == 'GET':
        try:
            therapist_id = request.GET.get('therapist_id')
            return get_calendar_therapist(request, therapist_id)
        except:
            return get_calendar_all(request)
    elif request.method == 'POST':
        return calendar_new(request)


@ json_view
@ api_view(['GET', 'PUT', 'DELETE'])
def calendar_withid(request, calendar_id):
    if request.method == 'GET':
        return get_calendar(request, calendar_id)
    elif request.method == 'PUT':
        return calendar_update(request, calendar_id)
    elif request.method == 'DELETE':
        return calendar_delete(request, calendar_id)


def get_calendar_all(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    skip = request.GET.get('skip', '0')
    limit = request.GET.get('limit', '20')
    skip = int(skip) if str(skip).isnumeric() else 0
    limit = int(limit) if str(limit).isnumeric() else 20
    calendar_info = Calendar.objects.all().skip(skip).limit(limit)
    serializer = CalendarSerializer(calendar_info, many=True)
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


def get_calendar_therapist(request, therapist_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')

    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        Therapist.objects.get(id=therapist_id)
    except Therapist.DoesNotExist:
        return JsonResponse(
            {'message': 'The therapist does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    try:
        Calendar.objects(therapist_id=therapist_id)
    except Calendar.DoesNotExist:
        return JsonResponse(
            {'message': 'The therapist does not have any calendars'},
            status=status.HTTP_404_NOT_FOUND
        )
    calendar_info = Calendar.objects(therapist_id=therapist_id)
    serializer = CalendarSerializer(calendar_info, many=True)
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


def get_calendar(request, calendar_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        calendar_info = Calendar.objects.get(id=calendar_id)
    except Calendar.DoesNotExist:
        return JsonResponse(
            {'message': 'The calendar does not in the database'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = CalendarSerializer(calendar_info)
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


def calendar_update(request, calendar_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    calendar_data = JSONParser().parse(request)
    try:
        calendar = Calendar.objects.get(id=calendar_id)
    except Calendar.DoesNotExist:
        return JsonResponse(
            {'message': 'The calendar does not in the database'},
            status=status.HTTP_404_NOT_FOUND
        )
    calendar_data["time_begin"] = datetime.fromtimestamp(
        calendar_data["time_begin"])
    calendar_data["time_end"] = datetime.fromtimestamp(
        calendar_data["time_end"])
    serializer = CalendarSerializer(calendar, data=calendar_data)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def calendar_delete(request, calendar_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        calendar = Calendar.objects.get(id=calendar_id)
    except Calendar.DoesNotExist:
        return JsonResponse(
            {'message': 'The calendar already deleted or never input to the database'},
            status=status.HTTP_404_NOT_FOUND
        )
    calendar.delete()
    return JsonResponse(
        {'message': 'This calendar was deleted successfully!'}, status=status.HTTP_202_ACCEPTED
    )


def calendar_new(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    calendar_data = JSONParser().parse(request)
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    therapist_id = calendar_data["therapist_id"]
    try:
        Therapist.objects.get(id=therapist_id)
    except Therapist.DoesNotExist:
        return JsonResponse(
            {'message': 'The therapist does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    if calendar_data["time_begin"] >= calendar_data["time_end"]:
        return JsonResponse({'message': 'setting time error'}, status=status.HTTP_400_BAD_REQUEST)

    calendar_data["time_begin"] = datetime.fromtimestamp(
        calendar_data["time_begin"])
    calendar_data["time_end"] = datetime.fromtimestamp(
        calendar_data["time_end"])
    serializer = CalendarSerializer(data=calendar_data)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
