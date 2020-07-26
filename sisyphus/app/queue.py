from redis import Redis
from rq import Queue  # type: ignore


redis_conn = Redis()
task_queue = Queue(connection=redis_conn)
