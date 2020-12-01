import uuid
from datetime import datetime
from urllib.parse import urlencode

import jwt
from bson import ObjectId
from config import config
from django.http.response import HttpResponse, JsonResponse
from mongoengine.errors import ValidationError
from mosoon_massage_backend.models import Member, Order
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from utils.get_client_ip import get_client_ip
from utils.jsonview import json_view
from utils.mpg_aes_handler import create_mpg_aes_encrypt
from utils.mpg_sha_handler import create_mpg_sha_encrypt

from order_api.serializer import OrderSerializer


@json_view
@api_view(['GET', 'POST'])
def orders_handler(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')

    if request.method == 'GET':
        member_id = request.GET.get('member_id', '')
        date = request.GET.get('date', '')

        order_filter = {}
        if member_id != '':
            order_filter['member_id'] = ObjectId(member_id)
        if date != '':
            order_filter['start_time'] = {'$gte': int(date)}
            order_filter['end_time'] = {'$lte': int(date)+86400}

        if token_payload.get('admin') or (
                not token_payload.get('admin') and member_id == token_payload.get("id")):

            orders = Order.objects(__raw__=order_filter)
            order_serializer = OrderSerializer(orders, many=True)
            return JsonResponse(order_serializer.data, safe=False)

        return JsonResponse({"message": "Permission Denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':

        amount = JSONParser().parse(request).get("amount")
        token_payload = request.META.get('TOKEN_PAYLOAD')

        try:
            member = Member.objects.get(id=token_payload['id'])
        except Member.DoesNotExist:
            return JsonResponse({"message": "Invalid Token"}, status=status.HTTP_401_UNAUTHORIZED)

        complete_token = jwt.encode(
            {'member_id': str(member.id), 'amount': amount, 'create_time': datetime.now().timestamp()}, config['SECRET_KEY'], algorithm='HS256')

        now = datetime.now()

        trade_info = {
            "MerchantID": config['MERCHANT_ID'],
            "Version": "1.5",
            "RespondType": "JSON",
            "TimeStamp": int(now.timestamp()),
            "MerchantOrderNo": str(uuid.uuid4())[:8],
            "Amt": amount,
            "ItemDesc": "魔松勁按摩金 " + str(amount) + " 元",
            "Email": member.email,
            "LoginType": 0,
            "NotifyURL": config['HOST_NAME'] + "/order/complete/" + complete_token.decode('utf-8').replace(".", "/"),
            "CVSCOM": 0
        }

        trade_info_aes = create_mpg_aes_encrypt(
            urlencode(trade_info), config['HASH_KEY'], config['HASH_IV'])

        trade_info_sha = create_mpg_sha_encrypt(
            trade_info_aes, config['HASH_KEY'], config['HASH_IV'])

        page_html = """
<html >
    <body style = "display: flex; align-items: center; justify-content: center" onload="setTimeout(function() {{ document.Newebpay.submit() }}, 100)" >
        <form name = "Newebpay" method = "post" action = "{MPG_GATEWAY}" >
            <input type = "text" name = "MerchantID" value = "{MerchantID}" hidden / >
            <input type = "text" name = "TradeInfo" value = "{TradeInfo}" hidden / >
            <input type = "text" name = "TradeSha" value = "{TradeSha}" hidden / >
            <input type = "text" name = "Version" value = "{Version}" hidden / >
            請稍候，正在前往藍新金流
        </form >
    </body >
</html >
""".format(MPG_GATEWAY=config['MPG_GATEWAY'],
           MerchantID=config['MERCHANT_ID'],
           TradeInfo=trade_info_aes,
           TradeSha=trade_info_sha,
           Version=1.5)

        return HttpResponse(page_html)


@ json_view
@ api_view(['GET'])
def order_handler(request, order_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"message": "ORDER_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)

    order_serializer = OrderSerializer(order)

    if token_payload.get('admin') or order.member_id == token_payload.id:
        return JsonResponse(order_serializer.data)

    return JsonResponse({"message": "PERMISSION_DENIED"}, status=status.HTTP_403_FORBIDDEN)


@ json_view
@ api_view(['POST'])
def payment_complete(request, header, payload, signature):

    complete_jwt = header + "." + payload + "." + signature

    try:
        complete_token_payload = jwt.decode(complete_jwt, config['SECRET_KEY'], algorithms=[
            'HS256'])
    except jwt.InvalidTokenError:
        return JsonResponse({"message": "Invalid Token"},
                            status=status.HTTP_403_FORBIDDEN)

    order_data = {
        "create_time": datetime.fromtimestamp(complete_token_payload['create_time']),
        "payment_time": datetime.now(),
        "ip": get_client_ip(request),
        "amount": complete_token_payload['amount'],
        "member_id": complete_token_payload['member_id'],
        "status": str(request.body).split('&')[0].split('=')[1]
    }

    order_serializer = OrderSerializer(data=order_data)

    if order_serializer.is_valid():
        try:
            member = Member.objects.get(id=complete_token_payload['member_id'])
        except member.DoesNotExist:
            return JsonResponse(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        member['balance'] += complete_token_payload['amount']
        member.save()
        order_serializer.save()
        return JsonResponse(order_serializer.data, status=status.HTTP_201_CREATED)

    return JsonResponse(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
