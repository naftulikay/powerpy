# powerpy

Pronounced "power-pie". A Python slideshow API using Celery, Tornado, RabbitMQ, Redis, and Amazon S3.

## Running the Application

You'll need a Redis server, a RabbitMQ server, and an S3 bucket at minimum to run the application. There is a Docker
Compose configuration file in the project root for quickly getting Redis and RabbitMQ running.

There are two processes to run, one is the Tornado web server for HTTP requests and the other is the Celery asynchronous
task worker for converting files and background uploading.

### Environment Variables

Before starting the worker, it is important to setup the environment variables pointing to your Redis instance,
your RabbitMQ instance, and your AWS account credentials and S3 bucket information.

<table>
    <thead>
        <tr>
            <th>Name</th>
            <th>Required By</th>
            <th>Description</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>AWS_ACCESS_KEY_ID</td>
            <td>Celery Worker</td>
            <td>Your AWS access key ID for Amazon authentication.
        </tr>
        <tr>
            <td>AWS_SECRET_ACCESS_KEY</td>
            <td>Celery Worker</td>
            <td>Your AWS secret access key for Amazon authentication.</td>
        </tr>
        <tr>
            <td>S3_BUCKET</td>
            <td>Celery Worker</td>
            <td>The S3 bucket name to upload files into.</td>
        </tr>
        <tr>
            <td>MAX_UPLOAD_SIZE</td>
            <td>Web Server</td>
            <td>The maximum upload size in kilobytes. Defaults to 10240 (10MiB).</td>
        </tr>
        <tr>
            <td>HTTP_PORT</td>
            <td>Web Server</td>
            <td>The HTTP port to listen on for traffic. Defaults to 8080.</td>
        </td>
        <tr>
            <td>REDIS_HOST</td>
            <td>Both</td>
            <td>The hostname of the Redis server. Defaults to localhost.</td>
        </tr>
        <tr>
            <td>REDIS_PORT</td>
            <td>Both</td>
            <td>The port number of the Redis server. Defaults to 6379.</td>
        </tr>
        <tr>
            <td>RABBITMQ_HOST</td>
            <td>Both</td>
            <td>The hostname of the RabbitMQ server. Defaults to localhost.</td>
        </tr>
        <tr>
            <td>RABBITMQ_PORT</td>
            <td>Both</td>
            <td>The port number of the RabbitMQ server. Defaults to 5672.</td>
        </tr>
    </tbody>
</table>

### Starting the Web Server

After building the project, the web worker can be started like so:

```
bin/powerpy-web
```

### Starting the Celery Worker

The Celery worker can be started like so:

```
bin/powerpy-worker worker
```

## Upload Flow

Upload a slideshow file:

```
$ curl -X POST -F 'file=@Downloads/presentation.pdf' http://localhost:8080/api/v1/slideshow/upload
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
$ curl -X GET http://localhost:8080/api/v1/slideshow/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba.json
{
    "id": "4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba",
    "status": "READY",
    "current": "0",
    "slides": [
        "https://s3.amazonaws.com/{{ bucket_name }}/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba/slide_000.jpg",
        "https://s3.amazonaws.com/{{ bucket_name }}/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba/slide_001.jpg",
        "https://s3.amazonaws.com/{{ bucket_name }}/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba/slide_002.jpg"
    ],
    "created": "2016-02-02 21:44:42 -0000"
}
```

Now that it's ready, the host can make changes to it, changing the current slide selected:

```
$ curl -X POST -d '{ "current": 1 }' http://localhost:8080/api/v1/slideshow/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba/control
{
    "current": 1,
    "updated": "2016-02-02 21:50:22 -0000"
}
```

All listeners on the subscribe endpoint will receive the same JSON as above. Connect a WebSocket to the following URL
to watch changes:

```
http://localhost:8080/api/v1/slideshow/4044fe7b9cd73cccc82bdd1a2255c68e5d58afdcd40d3c66386f6c3afee5b9ba/listen
```

## Bucket Setup

Setup your AWS S3 bucket with the following bucket permissions:

```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "AddPerm",
			"Effect": "Allow",
			"Principal": "*",
			"Action": "s3:GetObject",
			"Resource": "arn:aws:s3:::{{ bucket_name }}/*"
		}
	]
}
```

You'll also need an IAM user account and credentials which have the following permissions to act on your bucket:

```
{
   "Version":"2012-10-17",
   "Statement":[
      {
         "Effect":"Allow",
         "Action":[
            "s3:ListBucket",
            "s3:GetBucketLocation"
         ],
         "Resource":"arn:aws:s3:::{{ bucket_name }}"
      },
      {
         "Effect":"Allow",
         "Action":[
            "s3:PutObject",
            "s3:GetObject",
            "s3:DeleteObject"
         ],
         "Resource":"arn:aws:s3:::{{ bucket_name }}/*"
      }
   ]
}
```

It should be possible to remove the following permissions from above if desired:

 * `s3:ListBucket`
 * `s3:GetBucketLocation`
 * `s3:GetObject`
 * `s3:DeleteObject`

As of the time of writing, these permissions aren't used.
