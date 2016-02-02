#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from powerpy.web.handlers import (
    SlideshowUploadHandler,
    SlideshowIndexHandler,
)

import tornado.web


class SlideshowApplication(tornado.web.Application):

    def __init__(self, options):
        """
        """
        handlers = (
            (r"/api/v1/slideshow/upload", SlideshowUploadHandler),
            (r'/api/v1/slideshow/(?<slideshow_id)[a-f0-9]{40})\.json', SlideshowIndexHandler),
        )

        tornado.web.Application.__init__(self, handlers)
