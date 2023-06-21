# Create a redis connection
import os
from redis import Redis


redis_conn = Redis.from_url(os.getenv('CELERY_RESULT_BACKEND'))


def get_queue_length() -> int:
    # Get the length of the list 'celery' (default queue)
    length = redis_conn.llen('celery')
    return length
