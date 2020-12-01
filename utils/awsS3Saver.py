import boto3
from config import config

class AwsS3Saver():
    def __init__(self):
        try:
            self.session = boto3.Session(
                aws_access_key_id=config['AWS_ACCESS_KEY'],
                aws_secret_access_key=config['AWS_SECRET_KEY'],
            )
            self.s3 = self.session.client('s3')
        except:
            print('Error: aws s3 connect failed.')

    def upload(self, key, content):
        self.s3.put_object(
            Bucket=config['bucket_name'], Key=(key), Body=content, ACL='public-read',
        )
        url = 'https://%s.s3-ap-northeast-1.amazonaws.com/%s' % (
            config['bucket_name'],
            key
        )
        return url

    def remove(self, key):
        self.s3.delete_object(Bucket=config['bucket_name'], Key=key)

awsS3Saver = AwsS3Saver()
