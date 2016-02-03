#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from celery import Celery
from powerpy import config

import os
import sys


app = Celery('powerpy',
    broker='amqp://%s:%d' % (config.rabbitmq_host, config.rabbitmq_port),
    include=['powerpy.tasks']
)

app.conf.update(
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TASK_SERIALIZER='json',
)

def start_worker():
    if not config.aws_access_key_id:
        raise Exception("AWS_ACCESS_KEY_ID must be defined for S3 access!")

    if not config.aws_secret_access_key:
        raise Exception("AWS_SECRET_ACCESS_KEY must be defined for S3 access!")

    if not config.s3_bucket:
        raise Exception("S3_BUCKET must be defined for S3 access!")

    argv = sys.argv

    if len(argv) == 1:
        argv.append('worker')

    app.start(argv=argv)


if __name__ == '__main__':
    startup_worker()
