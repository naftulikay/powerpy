#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from powerpy.web.handlers import (
    SlideshowUploadHandler,
    SlideshowIndexHandler,
    SlideshowControlHandler,
    SlideshowListenHandler,
)

import tornado.web


class SlideshowApplication(tornado.web.Application):

    def __init__(self, options):
        """
        """
        handlers = (
            # upload
            (r'/api/v1/slideshow/upload', SlideshowUploadHandler),
            # static get
            (r'/api/v1/slideshow/(?P<slideshow_id>[a-f0-9]{64})\.json', SlideshowIndexHandler),
            # control
            (r'/api/v1/slideshow/(?P<slideshow_id>[a-f0-9]{64})/control', SlideshowControlHandler),
            # websocket watch
            (r'/api/v1/slideshow/(?P<slideshow_id>[a-f0-9]{64})/(?:listen|updates)', SlideshowListenHandler),
        )

        tornado.web.Application.__init__(self, handlers)
