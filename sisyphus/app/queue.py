from redis import Redis
from rq import Queue  # type: ignore

from .settings import load_config


settings = load_config()
repos_app = settings.repos_app

redis_conn = Redis()
task_queue = Queue(repos_app.job_queue, connection=redis_conn)
