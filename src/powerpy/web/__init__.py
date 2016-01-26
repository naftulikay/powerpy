#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from tornado.options import define, options
from powerpy.web.app import SlideshowApplication

import os
import tornado.httpserver
import tornado.ioloop


def start_webserver():
    """
    Start up the Tornado web server.
    """
    define("port", type=int, default=os.environ.get('HTTP_PORT', "8080"),
        help="The port to listen to for HTTP requests.")
    define("redis_host", type=str, default=os.environ.get('REDIS_HOST', 'localhost'),
        help="The host on which Redis is running.")
    define("redis_port", type=int, default=int(os.environ.get('REDIS_PORT', "5769")),
        help="The port to use when connecting to Redis.")
    define("max_upload_size", type=int, default=os.environ.get('MAX_UPLOAD_SIZE', 10 * 1024),
        help="The max upload size in kilobytes.")

    server = tornado.httpserver.HTTPServer(SlideshowApplication())
    server.listen(options.port)

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt as e:
        print "\rShutting down."


if __name__ == "__main__":
    start_webserver()
