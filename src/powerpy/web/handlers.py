#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from hashlib import sha256
from powerpy import redis
from powerpy.tasks import process_slideshow_upload
from random import SystemRandom; random = SystemRandom()
from tornado.options import options
from tornado.web import HTTPError

import magic
import os, os.path
import shutil
import string
import tempfile
import tornado.web
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
            # generate a random 'unique' id for the upload
            upload_id = sha256(
                # a random uuid plus 256 bits of randomness from system random
                str(uuid.uuid4()) + ''.join([random.choice(string.letters + string.digits) for i in range(32)])
            ).hexdigest()

            created_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

            # save it to redis
            redis_key = 'powerpy/slideshow/%s' % (upload_id,)
            pipe = redis.pipeline()
            pipe.hmset(redis_key, {
                'id': upload_id,
                'status': 'PENDING',
                'created': created_timestamp,
                'workdir': workdir,
                'file': slideshow_filename,
                'mimetype': mimetype
            })
            # this expires in 24 hours
            pipe.expire(redis_key, int(timedelta(hours=24).total_seconds()))
            pipe.execute()

            # publish to celery
            process_slideshow_upload.delay(upload_id)

            # TODO return JSON result
        except Exception as e:
            # always clean up
            shutil.rmtree(workdir)
            raise e


class SlideshowIndexHandler(tornado.web.RequestHandler):
    pass
