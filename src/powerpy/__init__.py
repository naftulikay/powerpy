#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from redis import StrictRedis

import isodate
import os

class Configuration(object):

    def __init__(self):
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.s3_bucket = os.environ.get('S3_BUCKET')
        self.http_port = int(os.environ.get('HTTP_PORT', 8080))
        self.redis_host = os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = int(os.environ.get('REDIS_PORT', 6379))
        self.rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'localhost')
        self.rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', 5672))
        self.max_upload_size = int(os.environ.get('MAX_UPLOAD_SIZE', 1024 * 10)) # 10MiB
        # slideshows live in redis for 24 hours by default
        self.max_slideshow_age = int(isodate.parse_duration(os.environ.get('MAX_SLIDESHOW_AGE', 'PT24H')).total_seconds())

config = Configuration()

redis = StrictRedis(host=config.redis_host, port=config.redis_port)
