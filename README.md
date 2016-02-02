# powerpy

Pronounced "power-pie". A Python slideshow API using Celery, Tornado, RabbitMQ, and Redis.

## Upload Flow

Upload a slideshow file:

```
$ curl -X POST -F 'file=@Downloads/Rental Application.pdf' http://localhost:2200/api/v1/slideshow/upload
{
    "id": "4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba",
    "status": "PENDING",
    "current": 0,
    "slides": [],
    "created": "2016-02-02 21:40:43 -0000"
}
```

Wait for the upload to finish by curling the details for the slideshow:

```
$ curl -X GET http://localhost:2200/api/v1/slideshow/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba.json
{
    "id": "c2d641ffa35b105427c6bc47fba73dc73de0ce73f17730e36c038ea1441acebf",
    "status": "READY",
    "current": "0",
    "slides": [
        "https://nope.com/s3/c2d641ffa35b105427c6bc47fba73dc73de0ce73f17730e36c038ea1441acebf/slide_000.jpg",
        "https://nope.com/s3/c2d641ffa35b105427c6bc47fba73dc73de0ce73f17730e36c038ea1441acebf/slide_001.jpg",
        "https://nope.com/s3/c2d641ffa35b105427c6bc47fba73dc73de0ce73f17730e36c038ea1441acebf/slide_002.jpg"
    ],
    "created": "2016-02-02 21:44:42 -0000"
}
```

Now that it's ready, the host can make changes to it, changing the current slide selected:

```
$ curl -X POST -d '{ "current": 1 }' http://localhost:2200/api/v1/slideshow/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba/control
{
    "current": 1,
    "updated": "2016-02-02 21:50:22 -0000"
}
```

All listeners on the subscribe endpoint will receive the same JSON as above. Connect a WebSocket to the following URL
to watch changes:

```
http://localhost:2200/api/v1/slideshow/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba/listen
```
