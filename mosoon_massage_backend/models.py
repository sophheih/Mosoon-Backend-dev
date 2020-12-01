from datetime import datetime, timedelta
from django.utils.timezone import now

import jwt
import mongoengine

from config import config
from utils.awsS3Saver import awsS3Saver


class Member(mongoengine.Document):
    username = mongoengine.StringField()
    real_name = mongoengine.StringField()
    password_md5 = mongoengine.StringField()
    balance = mongoengine.IntField(default=0)
    gender = mongoengine.StringField(choices=('男', '女'))
    cellphone = mongoengine.StringField()
    email = mongoengine.StringField()
    vip = mongoengine.BooleanField(default=False)
    birthday = mongoengine.DateTimeField()
    token_time = mongoengine.DateTimeField()

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        token = jwt.encode({
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'data': {
                'id': str(self.id),
                'admin': False
            }
        }, config['SECRET_KEY'], algorithm='HS256')

        return token.decode('utf-8')

    def first_buy(self):
        if Reservation.objects.get(member_id=self.id):
            return False
        return True


class Service(mongoengine.Document):
    title = mongoengine.StringField()
    short_description = mongoengine.StringField()
    long_description = mongoengine.StringField()
    image_url = mongoengine.ListField(allow_empty=True)
    duration = mongoengine.IntField()
    price = mongoengine.IntField()
    vip_per = mongoengine.FloatField(default=1)
    nor_per = mongoengine.FloatField(default=1)
    minus = mongoengine.IntField(default=0)


class Event(mongoengine.Document):
    title = mongoengine.StringField()
    content = mongoengine.StringField()
    begin_date = mongoengine.DateTimeField()
    end_date = mongoengine.DateTimeField()
    image_url = mongoengine.StringField()


class Therapist(mongoengine.Document):
    name = mongoengine.StringField()
    image_url = mongoengine.StringField()
    gender = mongoengine.StringField(choices=('男', '女'))
    description = mongoengine.StringField()


class Address(mongoengine.Document):
    city = mongoengine.StringField(required=True)
    district = mongoengine.StringField(required=True)
    detail = mongoengine.StringField(required=True)
    member_id = mongoengine.ObjectIdField()
    note = mongoengine.StringField(allow_empty=True)


class Reservation(mongoengine.Document):
    therapist_id = mongoengine.ObjectIdField()
    member_id = mongoengine.ObjectIdField()
    total_price = mongoengine.IntField()
    start_time = mongoengine.DateTimeField()
    end_time = mongoengine.DateTimeField()
    buffer_start = mongoengine.IntField(default=15)
    buffer_end = mongoengine.IntField(default=15)
    services_id = mongoengine.ListField()
    address = mongoengine.DictField()


class Order(mongoengine.Document):
    create_time = mongoengine.DateTimeField(required=True)
    ip = mongoengine.StringField(required=True)
    amount = mongoengine.IntField(required=True)
    member_id = mongoengine.ObjectIdField(required=True)
    status = mongoengine.StringField(required=True)
    payment_time = mongoengine.DateTimeField(required=False)
    error_msg = mongoengine.StringField(required=False)


class Calendar(mongoengine.Document):
    time_begin = mongoengine.DateTimeField(format='%s')
    time_end = mongoengine.DateTimeField(format='%s')
    therapist_id = mongoengine.ObjectIdField()
    note = mongoengine.StringField(allow_empty=True)


class Image(mongoengine.Document):
    url = mongoengine.StringField(required=True)
    usage = mongoengine.IntField(required=True)
    upload_time = mongoengine.DateTimeField(default=now)

    @staticmethod
    def increaseUsage(url, usage, ignore_check_exist=False):
        try:
            image = Image.objects.get(url=url)
            Image.objects(url=url).update_one(
                inc__usage=usage, full_result=True)
            if (image['usage'] + usage) <= 0:
                image.delete()
                file_name = url.split('/')[-1]
                awsS3Saver.remove('image/%s' % (file_name))
        except Image.DoesNotExist as e:
            if not ignore_check_exist:
                raise e
