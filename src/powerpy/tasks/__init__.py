#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from datetime import timedelta
from powerpy import redis, config
from powerpy.worker import app

import boto3
import re
import shutil
import subprocess
import os

SLIDE_REGEX = re.compile(r'slide_\d{3}\.jpg$', re.I)

class ProgramException(Exception):

    def __init__(self, message, stdout, stderr, returncode):
        super(Exception, self).__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def execute_process(args):
    """
    """
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    returncode = p.returncode

    if returncode != 0:
        raise ProgramException("Execution failed of %s." %(' '.join(args)), stdout, stderr, returncode)


def upload_to_s3(file_path, upload_path):
    """
    """
    s3 = boto3.resource('s3')
    o = s3.Object(config.s3_bucket, upload_path)
    # do the upload
    o.upload_file(file_path)

    # get the link
    return "https://s3.amazonaws.com/{bucket}/{key}".format(**{
        'bucket': config.s3_bucket,
        'key': upload_path,
    })


@app.task
def process_slideshow_upload(upload_id):
    redis_key = 'powerpy/slideshow/%s' % (upload_id,)
    redis_slides_key = 'powerpy/slideshow/%s/slides' % (upload_id,)
    workdir = redis.hget(redis_key, 'workdir')
    slideshow_filename = redis.hget(redis_key, 'file')
    mimetype = redis.hget(redis_key, 'mimetype')

    try:
        # update redis with processing status
        redis.hset(redis_key, 'status', 'PROCESSING')

        if mimetype.strip() != 'application/pdf':
            # convert from powerpoint format to pdf
            original = slideshow_filename
            slideshow_filename = os.path.join(workdir, 'presentation.pdf')
            execute_process(['/usr/bin/unoconv', '-f', 'pdf', '-o', slideshow_filename, original])

        # convert from pdf to a series of slides
        execute_process(['/usr/bin/convert', slideshow_filename, os.path.join(workdir, 'slide_%03d.jpg')])

        # upload slides to s3
        redis.hset(redis_key, 'status', 'UPLOADING')
        slides = sorted([os.path.join(workdir, i) for i in os.listdir(workdir) if SLIDE_REGEX.search(i)])
        slide_urls = []

        if len(slides) == 0:
            # if no slides, this is wrong
            raise Exception("No slides found in upload, terminating.")

        for slide in slides:
            # find all slides in the work directory in sorted order
            slide_urls.append(upload_to_s3(slide, '%s/%s' % (upload_id, os.path.basename(slide))))

        # save urls to slides in redis
        pipe = redis.pipeline()
        pipe.lpush(redis_slides_key, *reversed(slide_urls)) # redis adds things backwards
        # expire slides in 24 hours
        pipe.expire(redis_slides_key, int(timedelta(hours=24).total_seconds()))
        pipe.execute()

        # cleanup filesystem
        if workdir.startswith('/tmp/powerpy'):
            shutil.rmtree(workdir)

        # update redis
        pipe = redis.pipeline()
        # delete useless keys
        pipe.hdel(redis_key, 'workdir', 'file', 'mimetype')
        # set current slide
        pipe.hset(redis_key, 'current', 0)
        # set status to ready
        pipe.hset(redis_key, 'status', 'READY')
        pipe.execute()
    except Exception as e:
        # clean up redis
        redis.hset(redis_key, 'status', 'ERROR')

        # clean up filesystem (safely)
        if workdir.startswith('/tmp/powerpy'):
            shutil.rmtree(workdir)

        raise e
