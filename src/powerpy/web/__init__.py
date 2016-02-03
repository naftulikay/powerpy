#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from tornado.options import define, options
from powerpy import config
from powerpy.web.app import SlideshowApplication

import os
import tornado.httpserver
import tornado.ioloop


def start_webserver():
    """
    Start up the Tornado web server.
    """
    define("port", type=int, default=config.http_port, help="The port to listen to for HTTP requests.")
    define("max_upload_size", type=int, default=config.max_upload_size, help="The max upload size in kilobytes.")

    global application
    application = SlideshowApplication(options)

    server = tornado.httpserver.HTTPServer(application)
    server.listen(options.port)

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt as e:
        print "\rShutting down."


if __name__ == "__main__":
    start_webserver()
