#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from redis import StrictRedis

import os


redis = StrictRedis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', '6379')),
)
