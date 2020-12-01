import random
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view
from rest_framework import status
from django.http.response import JsonResponse
from mongoengine.errors import ValidationError
from mosoon_massage_backend.models import Reservation, Member, Therapist, Service, Calendar, Address
from reservation_api.serializers import GetReservationSerializer, ReservationSerializer
from utils.jsonview import json_view
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import pytz
import json


@json_view
@api_view(['GET'])
def reservation_handler(request):
    if request.method == 'GET':
        reservation_filter = {}
        token_payload = request.META.get('TOKEN_PAYLOAD')
        therapist_id = request.GET.get('therapist_id', '')
        member_id = request.GET.get('member_id', '')
        date = request.GET.get('date', '')

        skip = request.GET.get('skip', '0')
        limit = request.GET.get('limit', '20')
        skip = int(skip) if str(skip).isnumeric() else 0
        limit = int(limit) if str(limit).isnumeric() else 20

        if not (token_payload.get('admin')):
            if token_payload.get('id'):
                try:
                    member = Member.objects.get(id=token_payload.get('id'))
                except Member.DoesNotExist:
                    return JsonResponse(
                        {'message': 'The member does not exist'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return JsonResponse(
                    {'message': 'Permission Denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if therapist_id != '':
            try:
                Therapist.objects.get(id=therapist_id)
                reservation_filter['therapist_id'] = ObjectId(therapist_id)
            except Therapist.DoesNotExist:
                return JsonResponse(
                    {'message': 'The therapist does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValidationError:
                return JsonResponse(
                    {'message': 'Invalid ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if member_id != '':

            if not (token_payload.get('admin')):
                if ObjectId(member_id) != member.id:
                    return JsonResponse(
                        {'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
            try:
                member = Member.objects.get(id=member_id)
                reservation_filter['member_id'] = ObjectId(member_id)
            except Member.DoesNotExist:
                return JsonResponse(
                    {'message': 'The member does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValidationError:
                return JsonResponse(
                    {'message': 'Invalid ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if date != '':
            time_end = datetime.fromtimestamp(int(date)+86400)
            time = datetime.fromtimestamp(int(date))
            reservation_filter['start_time'] = {'$gte': time}
            reservation_filter['end_time'] = {'$lte': time_end}
        if request.GET == {}:
            if not token_payload.get('admin'):
                return JsonResponse(
                    {'message': 'Permission Denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        if token_payload.get('id'):
            reservation_filter['member_id'] = member.id
        reservations = Reservation.objects(
            __raw__=reservation_filter).skip(skip).limit(limit)

        if token_payload.get('admin'):
            serializer = ReservationSerializer(reservations, many=True)
        else:
            serializer = GetReservationSerializer(reservations, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


@json_view
@api_view(['PUT', 'DELETE', 'GET'])
def reservation_withid(request, reservation_id):

    if request.method == 'GET':
        token_payload = request.META.get('TOKEN_PAYLOAD')

        if not (token_payload.get('admin')):
            if token_payload.get('id'):
                try:
                    member = Member.objects.get(id=token_payload.get('id'))
                except Member.DoesNotExist:
                    return JsonResponse(
                        {'message': 'The member does not exist'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return JsonResponse(
                    {'message': 'Permission Denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return JsonResponse(
                {'message': 'The reservation does not exist'}, safe=False,
                status=status.HTTP_404_NOT_FOUND
            )
        if not (token_payload.get('admin')):
            if reservation.member_id != member.id:
                return JsonResponse(
                    {'message': 'Permission Denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        serializer = ReservationSerializer(reservation)
        return JsonResponse(
            serializer.data, safe=False
        )
    elif request.method == 'PUT':
        token_payload = request.META.get('TOKEN_PAYLOAD')
        if not token_payload.get('admin'):
            return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

        new_data = JSONParser().parse(request)

        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return JsonResponse(
                {'message': 'The reservation does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        if 'therapist_id' in new_data.keys():
            new_data['therapist_id'] = ObjectId(new_data['therapist_id'])

        if 'member_id' in new_data.keys():
            new_data['member_id'] = ObjectId(new_data['member_id'])

        if 'services_id' in new_data.keys():

            duration_min = 0
            for service in new_data["services_id"]:
                duration_min += service['duration']

        if 'start_time' in new_data.keys():
            new_data['start_time'] = int(new_data['start_time'])

            new_data['end_time'] = int(
                new_data['start_time'])+int(duration_min)*60
        else:
            new_data['start_time'] = datetime.timestamp(reservation.start_time)
            new_data['end_time'] = datetime.timestamp(
                reservation.start_time)+(duration_min)*60

        new_data['start_time'] = datetime.fromtimestamp(
            int(new_data['start_time'])+3600*8)
        new_data['end_time'] = datetime.fromtimestamp(
            int(new_data['end_time'])+3600*8)

        serializer = ReservationSerializer(reservation, data=new_data)
        if serializer.is_valid():
            serializer.save()
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        reservation_2 = Reservation.objects.get(id=reservation_id)
        reservation_2 = reservation_2.to_json()
        reservation_2 = json.loads(reservation_2, encoding='utf-8')
        reservation_2['start_time'] = int(datetime.timestamp(
            new_data['start_time']-timedelta(hours=8)))
        reservation_2['end_time'] = int(datetime.timestamp(
            new_data['end_time']-timedelta(hours=8)))
        reservation_2['id'] = reservation_2['_id']['$oid']
        reservation_2.pop('_id')
        reservation_2['member_id'] = reservation_2['member_id']['$oid']
        reservation_2['therapist_id'] = reservation_2['therapist_id']['$oid']
        return JsonResponse(reservation_2, status=status.HTTP_200_OK, safe=False)

    elif request.method == 'DELETE':

        token_payload = request.META.get('TOKEN_PAYLOAD')
        if not token_payload.get('admin'):
            return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
        try:
            reservation = Reservation.objects.get(
                id=reservation_id)
        except Reservation.DoesNotExist:
            return JsonResponse(
                {'message': 'The reservation does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        reservation.delete()
        return JsonResponse(
            {'message': 'The reservation has been deleted.'},
            status=status.HTTP_200_OK
        )


@ json_view
@ api_view(['POST', 'GET'])
def reservation_new(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('id'):
        try:
            user = Member.objects.get(id=token_payload.get('id'))
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        therapist_id = request.GET.get('therapist_id', '')
        duration = request.GET.get('duration', '')
        time = request.GET.get('time', '')
        if duration == '':
            return JsonResponse(
                {'message': 'duration must be given.'},
                status.HTTP_400_BAD_REQUEST
            )
        if time == '':
            return JsonResponse(
                {'message': 'time must be given.'},
                status.HTTP_400_BAD_REQUEST
            )

        time = int(time)
        time_near = time + (900-time % 900)
        time_date = time - ((time+28800) % 86400)
        time_10am = time_date+3600*10
        begin = datetime.fromtimestamp(time_10am)
        end = datetime.fromtimestamp(time_10am+3600*14)

        if therapist_id == '':
            reservations = Reservation.objects(__raw__={
                '$or': [

                    {'start_time': {'$lte': end},
                        'end_time': {'$gte': end}},
                    {'start_time': {'$lte': begin},
                        'end_time': {'$gte': begin}},
                    {'start_time': {'$gte': begin},
                        'end_time': {'$lte': end}},
                    {'start_time': {'$lte': begin},
                        'end_time': {'$gte': end}},
                ]
            })

            calendars = Calendar.objects(__raw__={
                '$or': [
                    {'time_begin': {'$lte': end},
                        'time_end': {'$gte': end}},
                    {'time_begin': {'$lte': begin},
                        'time_end': {'$gte': begin}},
                    {'time_begin': {'$gte': begin},
                        'time_end': {'$lte': end}},
                    {'time_begin': {'$lte': begin},
                        'time_end': {'$gte': end}},
                ]
            })
        elif therapist_id != '':
            reservations = Reservation.objects(__raw__={
                '$or': [

                    {'start_time': {'$lte': end},
                        'end_time': {'$gte': end}},
                    {'start_time': {'$lte': begin},
                        'end_time': {'$gte': begin}},
                    {'start_time': {'$gte': begin},
                        'end_time': {'$lte': end}},
                    {'start_time': {'$lte': begin},
                        'end_time': {'$gte': end}},
                ]
            }).filter(therapist_id=therapist_id)

            calendars = Calendar.objects(__raw__={
                '$or': [
                    {'time_begin': {'$lte': end},
                        'time_end': {'$gte': end}},
                    {'time_begin': {'$lte': begin},
                        'time_end': {'$gte': begin}},
                    {'time_begin': {'$gte': begin},
                        'time_end': {'$lte': end}},
                    {'time_begin': {'$lte': begin},
                        'time_end': {'$gte': end}},
                ]
            }).filter(therapist_id=therapist_id)
        if time_10am >= time_near:
            n = (3600*14//900)
        else:
            n = ((time_10am+3600*14)-(time_near-time_10am)//900)
        avliable_time = []
        if therapist_id == '':
            therapists = Therapist.objects.all()
            for i in range(n+1):
                if time_10am > time_near:
                    start = time_10am+(i)*900
                    over = start+int(duration)*60+1800
                else:
                    start = time_near+(i)*900
                    over = start+int(duration)*60+1800
                start = datetime.fromtimestamp(start)
                over = datetime.fromtimestamp(over)
                if over > end:
                    break
                if len(reservations) == 0:
                    avliable_time.append(
                        int(datetime.timestamp(start))+900)

                else:
                    therapists_list = []
                    for reservation in reservations:
                        start_time = reservation['start_time'] - \
                            timedelta(
                            minutes=(reservation['buffer_start']))
                        end_time = reservation['end_time'] + \
                            timedelta(
                            minutes=(reservation['buffer_end']))

                        if (start < start_time and over > start_time) or (
                            start == start_time and over > start_time
                        ) or (
                            start < start_time and over > end_time
                        ) or (
                            start > start_time and over < end_time
                        ) or (
                            start < end_time and over == end_time
                        ) or (
                            start < end_time and over > end_time
                        ):
                            if reservation['therapist_id'] not in therapists_list:
                                therapists_list.append(
                                    reservation['therapist_id'])

                    if len(therapists_list) != len(therapists):
                        avliable_time.append(
                            int(datetime.timestamp(start))+900)
                        
            return JsonResponse(avliable_time, safe=False, status=status.HTTP_200_OK)

        elif therapist_id != '':
            for i in range(n):
                c = 0
                if time_10am > time_near:
                    start = time_10am+(i)*900
                    over = start+int(duration)*60+1800
                else:
                    start = time_near+(i)*900
                    over = start+int(duration)*60+1800
                start = datetime.fromtimestamp(start)
                over = datetime.fromtimestamp(over)
                if over > end:
                    break
                if len(reservations) == 0:
                    avliable_time.append(
                        int(datetime.timestamp(start))+900)

                else:
                    for reservation in reservations:

                        start_time = reservation['start_time'] - \
                            timedelta(
                            minutes=(reservation['buffer_start']))
                        end_time = reservation['end_time'] + \
                            timedelta(
                            minutes=(reservation['buffer_end']))

                        if (start < start_time and over > start_time) or (
                            start == start_time and over > start_time
                        ) or (
                            start < start_time and over > end_time
                        ) or (
                            start > start_time and over < end_time
                        ) or (
                            start < end_time and over == end_time
                        ) or (
                            start < end_time and over > end_time
                        ):
                            c += 1
                            break

                    if c == 0:
                        avliable_time.append(
                            int(datetime.timestamp(start))+900)
                        print(datetime.fromtimestamp(int(datetime.timestamp(start))+900))
            return JsonResponse(avliable_time, safe=False, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        reservation_data = JSONParser().parse(request)
        reservation_data["member_id"] = user.id
        total_price = 0
        duration_min = 0
        if user['vip'] is True:
            for service_id in reservation_data["services_id"]:
                try:
                    service = Service.objects.get(id=service_id)
                    service['price'] *= service['vip_per']

                    total_price += service['price']
                    duration_min += service['duration']
                except Service.DoesNotExist:
                    return JsonResponse(
                        {'message': 'The service does not exist'},
                        status=status.HTTP_404_NOT_FOUND
                    )
        else:
            for service_id in reservation_data["services_id"]:
                try:
                    service = Service.objects.get(id=service_id)

                    if service['minus'] != 0:
                        if service['price'] <= service['minus']:
                            service['price'] = 0
                        else:
                            service['price'] -= service['minus']
                    else:
                        service['price'] *= service['nor_per']

                    total_price += service['price']
                    duration_min += service['duration']
                except Service.DoesNotExist:
                    return JsonResponse(
                        {'message': 'The service does not exist'},
                        status=status.HTTP_404_NOT_FOUND
                    )

        reservation_data['total_price'] = int(total_price)

        reservation_data['end_time'] = int(
            reservation_data['start_time'])+int(duration_min)*60
        time = int(reservation_data['start_time'])
        time_date = time - ((time+28800) % 86400)
        time_10am = time_date+3600*10

        if not('therapist_id' in reservation_data.keys()):
            avliable_therapist = []
            begin = datetime.fromtimestamp(time_date)
            end = datetime.fromtimestamp(time_10am+3600*14)
            for therapist in Therapist.objects.all():
                c = 0
                reservations = Reservation.objects(therapist_id=therapist.id, __raw__={
                    '$or': [
                        {'start_time': {'$lte': end},
                            'end_time': {'$gte': end}},
                        {'start_time': {'$lte': begin},
                            'end_time': {'$gte': begin}},
                        {'start_time': {'$gte': begin},
                            'end_time': {'$lte': end}},
                        {'start_time': {'$lte': begin},
                            'end_time': {'$gte': end}},
                    ]
                })

                calendars = Calendar.objects(therapist_id=therapist.id, __raw__={
                    '$or': [

                        {'time_begin': {'$lte': end},
                            'time_end': {'$gte': end}},
                        {'time_begin': {'$lte': begin},
                            'time_end': {'$gte': begin}},
                        {'time_begin': {'$gte': begin},
                            'time_end': {'$lte': end}},
                        {'time_begin': {'$lte': begin},
                            'time_end': {'$gte': end}},
                    ]
                })

                if (len(reservations)+len(calendars)) == 0:
                    avliable_therapist.append(therapist.id)

                else:
                    start = datetime.fromtimestamp(
                        int(reservation_data['start_time'])-900)
                    over = datetime.fromtimestamp(
                        int(reservation_data['end_time'])+900)
                    for reservation in reservations:
                        start_time = reservation['start_time'] - \
                            timedelta(
                            minutes=(reservation['buffer_start']))
                        end_time = reservation['end_time'] + \
                            timedelta(
                            minutes=(reservation['buffer_end']))

                        if (start < start_time and over > start_time) or (
                            start == start_time and over > start_time
                        ) or (
                            start < start_time and over > end_time
                        ) or (
                            start > start_time and over < end_time
                        ) or (
                            start < end_time and over == end_time
                        ) or (
                            start < end_time and over > end_time
                        ):
                            c += 1
                            break

                    if c == 0:
                        avliable_therapist.append(str(therapist.id))

            if avliable_therapist != []:
                random.shuffle(avliable_therapist)
                reservation_data['therapist_id'] = avliable_therapist[0]
            else:
                return JsonResponse(
                    avliable_therapist, safe=False,
                    status=status.HTTP_201_CREATED
                )

        begin = datetime.fromtimestamp(time_date)
        end = datetime.fromtimestamp(time_10am+3600*14)

        reservations = Reservation.objects(__raw__={
            '$or': [

                {'start_time': {'$lte': end}, 'end_time': {'$gte': end}},
                {'start_time': {'$lte': begin},
                    'end_time': {'$gte': begin}},
                {'start_time': {'$gte': begin}, 'end_time': {'$lte': end}},
                {'start_time': {'$lte': begin}, 'end_time': {'$gte': end}},
            ]
        }).filter(therapist_id=ObjectId(reservation_data['therapist_id']))

        calendars = Calendar.objects(__raw__={
            '$or': [

                {'time_begin': {'$lte': end}, 'time_end': {'$gte': end}},
                {'time_begin': {'$lte': begin},
                    'time_end': {'$gte': begin}},
                {'time_begin': {'$gte': begin}, 'time_end': {'$lte': end}},
                {'time_begin': {'$lte': begin}, 'time_end': {'$gte': end}},
            ]
        }).filter(therapist_id=ObjectId(reservation_data['therapist_id']))

        if (len(calendars) + len(reservations)) != 0:
            start = datetime.fromtimestamp(
                int(reservation_data['start_time'])-900)
            over = datetime.fromtimestamp(
                int(reservation_data['end_time'])+900)
            for reservation in reservations:
                start_time = reservation['start_time'] - \
                    timedelta(
                    minutes=(reservation['buffer_start']))
                end_time = reservation['end_time'] + \
                    timedelta(
                    minutes=(reservation['buffer_end']))

                if (start < start_time and over > start_time) or (
                    start == start_time and over > start_time
                ) or (
                    start < start_time and over > end_time
                ) or (
                    start > start_time and over < end_time
                ) or (
                    start < end_time and over == end_time
                ) or (
                    start < end_time and over > end_time
                ):

                    return JsonResponse(
                        {'message': 'sorry! time interval had been taken by others.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if user['balance'] >= total_price >= 0:
            user['balance'] -= total_price
            user.save()

        else:
            return JsonResponse(
                {'message': 'User balance not enough.'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        reservation_fordb = reservation_data.copy()
        reservation_fordb['start_time'] = datetime.fromtimestamp(
            int(reservation_fordb['start_time'])+3600*8)
        reservation_fordb['end_time'] = datetime.fromtimestamp(
            int(reservation_fordb['end_time'])+3600*8)
        services = []
        for service_id in reservation_data['services_id']:
            try:
                service = Service.objects.get(
                    id=ObjectId(str(service_id))).to_json()

                service = json.loads(service, encoding='utf-8')
                service['id'] = str(service['_id']['$oid'])
                service.pop('_id')
                service.pop('long_description')
                services.append(service)
            except Service.DoesNotExist:
                return JsonResponse(
                    {'message': 'Service does not exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        reservation_fordb['services_id'] = services
        reservation_data['services_id'] = services
        try:
            address = Address.objects.get(
                id=reservation_fordb['address']).to_json()
            reservation_fordb['address'] = json.loads(
                address, encoding='utf-8')
            reservation_fordb['address']['id'] = str(
                reservation_fordb['address']['_id']['$oid'])
            reservation_fordb['address'].pop('_id')
            reservation_fordb['address'].pop('member_id')
            reservation_data['address'] = reservation_fordb['address']

        except Address.DoesNotExist:
            return JsonResponse(
                {'message': 'Address does not exists'}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer_2 = ReservationSerializer(data=reservation_fordb)

        if serializer_2.is_valid():
            serializer_2.save()
        reservation = Reservation.objects.get(id=serializer_2.data['id'])
        reservation_data['id'] = str(reservation.id)
        reservation_data['member_id'] = str(reservation.member_id)
        reservation_data['therapist_id'] = str(reservation.therapist_id)

        return JsonResponse(
            reservation_data,
            status=status.HTTP_201_CREATED
        )
