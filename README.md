# powerpy

Pronounced "power-pie". A Python slideshow API using Celery, Tornado, RabbitMQ, and Redis.

## Upload Flow

 1. User uploads file.
 2. File is written to /tmp with a random name. (`/api/v1/slideshow/upload`)
    * File must resolve as a PDF or PPT file.
    * File must be smaller than MAX_UPLOAD_SIZE.
 3. File reference is saved to Redis and status can be queried at `/api/v1/slideshow/$id.json`
    ```
    {
        "_id": "$id",
        "status": "PENDING"
    }
    ```
