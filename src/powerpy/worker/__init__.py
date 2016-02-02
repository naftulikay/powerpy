#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from celery import Celery

import os


app = Celery('powerpy',
    broker='amqp://%s:%s' % (os.environ.get('RABBITMQ_HOST', 'localhost'), os.environ.get('RABBITMQ_PORT', '5672')),
    include=['powerpy.tasks']
)

app.conf.update(
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TASK_SERIALIZER='json',
)

def start_worker():
    app.start()


if __name__ == '__main__':
    startup_worker()
