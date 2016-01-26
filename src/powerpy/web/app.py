#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from powerpy.web.handlers import SlideshowUploadHandler

import tornado.web


class SlideshowApplication(tornado.web.Application):

    def __init__(self):
        """
        """
        handlers = [
            (r"/api/v1/slideshow/upload", SlideshowUploadHandler),
        ]
        tornado.web.Application.__init__(self, handlers)
