#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from hashlib import sha256
from powerpy import redis, config
from powerpy.tasks import process_slideshow_upload
from powerpy.util import base36
from random import SystemRandom; random = SystemRandom()
from tornado.options import options
from tornado.web import HTTPError

import json
import logging
import magic
import os, os.path
import shutil
import string
import tempfile
import tornado.web
import tornado.websocket
import tornadoredis
import tornadoredis.pubsub
import uuid


class SlideshowUploadHandler(tornado.web.RequestHandler):

    ACCEPTED_TYPES = (
        "application/pdf"
    )

    def post(self):
        """
        Handle a multipart upload of a slideshow file.
        """

        if not self.request.files.has_key('file'):
            # there must be a file
            raise HTTPError(status_code=400, log_message="No multipart file data provided.")

        if not len(self.request.files['file']) == 1:
            # there must be exactly one file
            raise HTTPError(status_code=400, log_message="Only one file may be uploaded.")

        # we have obtained an uploaded file
        uploaded_file = self.request.files['file'][0]

        if len(uploaded_file.body) > (options.max_upload_size * 1024):
            # file is too big, reject
            raise HTTPError(status_code=400, log_message="Upload too large, filesize %dkb, max file size %dkb." %
                (len(uploaded_file.body) / 1024, options.max_upload_size))

        # create a working directory for it
        workdir = tempfile.mkdtemp(prefix="powerpy.")
        slideshow_filename = os.path.join(workdir, 'slideshow')

        # write the file to disk
        with open(slideshow_filename, 'wb') as f:
            f.write(uploaded_file.body)

        try:
            # determine file type
            mimetype = magic.from_file(slideshow_filename, mime=True)

            if mimetype not in SlideshowUploadHandler.ACCEPTED_TYPES:
                # not a known slideshow format
                raise HTTPError(400, log_message="Wrong upload mime type, got %s and expected one of %s" %
                    (mimetype, SlideshowUploadHandler.ACCEPTED_TYPES))

            # if it has made it this far, it just might be a winner
            # generate a random 'unique' id for the upload using base36 and redis
            upload_id = base36.encode(redis.incr('power/slideshow/index'))

            created_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S -0000')
            expires_timestamp = (datetime.utcnow() + timedelta(seconds=config.max_slideshow_age)).strftime('%Y-%m-%d %H:%M:%S -0000')

            # save it to redis
            redis_key = 'powerpy/slideshow/%s' % (upload_id,)
            pipe = redis.pipeline()
            pipe.hmset(redis_key, {
                'id': upload_id,
                'status': 'PENDING',
                'created': created_timestamp,
                'expires': expires_timestamp,
                'workdir': workdir,
                'file': slideshow_filename,
                'mimetype': mimetype
            })
            # this expires according to MAX_SLIDESHOW_AGE
            pipe.expire(redis_key, config.max_slideshow_age)
            pipe.execute()

            # publish to celery
            process_slideshow_upload.delay(upload_id)

            # return JSON result
            result = {
                'id': upload_id,
                'status': 'PENDING',
                'current': 0,
                'created': created_timestamp,
                'expires': expires_timestamp,
                'slides': [],
                '_links': {
                    'self': { 'href': '/api/v1/slideshow/{slideshow_id}.json'.format(slideshow_id=upload_id) }
                }
            }

            self.write(result)
        except Exception as e:
            # always clean up
            shutil.rmtree(workdir)
            raise e


class SlideshowIndexHandler(tornado.web.RequestHandler):

    def get(self, slideshow_id):
        """
        """
        if not slideshow_id:
            raise HTTPError(status_code=404, log_message="Unable to find slideshow with empty id.")

        redis_key = 'powerpy/slideshow/%s' % (slideshow_id,)
        redis_slides_key = 'powerpy/slideshow/%s/slides' % (slideshow_id,)

        if redis.exists(redis_key):
            # great, we have something to return
            slideshow = redis.hgetall(redis_key)
            # slides can be null, that's okay
            slides = redis.lrange(redis_slides_key, 0, 999) if redis.exists(redis_slides_key) else []

            result = {
                'id': slideshow.get('id'),
                'status': slideshow.get('status'),
                'current': slideshow.get('current', 0),
                'created': slideshow.get('created'),
                'expires': slideshow.get('expires'),
                'slides': slides,
                '_links': {
                    'self': { 'href': '/api/v1/slideshow/{slideshow_id}.json'.format(slideshow_id=slideshow_id) },
                    'websocket': { 'href': '/api/v1/slideshow/{slideshow_id}/updates'.format(slideshow_id=slideshow_id) }
                }
            }

            self.write(result)
        else:
            raise HTTPError(status_code=404, log_message="Unable to find slideshow with id of %s" % (slideshow_id,))


class SlideshowControlHandler(tornado.web.RequestHandler):

    def post(self, slideshow_id):
        """
        """
        if not slideshow_id:
            raise HTTPError(status_code=404, log_message="Unable to find slideshow with empty id.")

        redis_key = 'powerpy/slideshow/%s' % (slideshow_id,)
        redis_slides_key = 'powerpy/slideshow/%s/slides' % (slideshow_id,)
        redis_publish_channel = 'powerpy/slideshow/%s/updates' % (slideshow_id,)

        if redis.exists(redis_key):
            # get the slide length
            slides_count = redis.llen(redis_slides_key)

            control_request = json.loads(self.request.body)

            # sanitize and prepare
            result = {
                'id': slideshow_id,
                'current': int(control_request.get('current', 0)),
                'updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S -0000'),
            }

            # validate that current is within the allowed slides count
            if not result.get('current') < slides_count:
                raise HTTPError(status_code=400,
                    log_message="Unable to set current slide to %d, slide count is %d for %s." % (
                        result.get('current'), slides_count, slideshow_id))

            # okay, so set the value in the redis dict and broadcast the event
            pipe = redis.pipeline()
            # update the current value in the dict
            pipe.hset(redis_key, 'current', result.get('current'))
            # publish a json object across the channel with the current index and the current time
            pipe.publish(redis_publish_channel, json.dumps(result))
            pipe.execute()

            # send back the result that we broadcast
            self.write(result)
        else:
            raise HTTPError(status_code=404, log_message="Unable to find slideshow with id of %s" % (slideshow_id,))


class SlideshowListenHandler(tornado.websocket.WebSocketHandler):

    @tornado.gen.engine
    def open(self, slideshow_id):
        """
        Fired when someone connects.
        """
        if not redis.exists('powerpy/slideshow/%s' % (slideshow_id,)):
            raise HTTPError(status_code=404, log_message="Unable to find slideshow with id of %s" % (slideshow_id,))

        logging.info("client connected to slideshow %s", slideshow_id)

        self.client = self.get_redis_client()
        self.redis_channel = 'powerpy/slideshow/%s/updates' % (slideshow_id,)
        yield tornado.gen.Task(self.client.subscribe, self.redis_channel)
        self.client.listen(self.on_redis_message)

    def on_redis_message(self, message):
        """
        Fired whenever a message is published to the Redis channel.
        """
        if message.kind == 'message':
            # we've received a message from redis
            try:
                payload = json.loads(message.body)
                self.write_message(payload)
            except ValueError as e:
                logging.error("failed to convert the message body to JSON: %s", e.message)

    def on_message(self, msg):
        """
        Fired when a message is received from a client. We don't like that.
        """
        self.close()

    def on_close(self):
        """
        Fired when someone closes.
        """
        if self.client.subscribed:
            self.client.unsubscribe(self.redis_channel)
            self.client.disconnect()

    def get_redis_client(self):
        """
        Establish an asynchronous Redis connection.
        """
        client = tornadoredis.Client(host=config.redis_host, port=config.redis_port)
        client.connect()
        return client
