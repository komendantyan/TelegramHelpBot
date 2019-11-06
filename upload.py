#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from boto3.session import Session


AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
AWS_ENDPOINT = 'https://storage.yandexcloud.net'

FILENAME = 'function.zip'


def main():
    session = Session(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    client = session.client(service_name='s3', endpoint_url=AWS_ENDPOINT)

    with open(FILENAME, 'rb') as file:
        client.put_object(Bucket=AWS_BUCKET_NAME,
                          Key=FILENAME,
                          Body=file.read())


if __name__ == "__main__":
    main()
