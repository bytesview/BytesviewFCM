from redis import Redis
from rq import Queue

def  get_redis_connection(host, port, db, password=None,):
    if password is None:
        redis_connection = Redis(
            host=host,
            port=port,
            db=db
        )
    else:
        redis_connection = Redis(
            host=host,
            port=port,
            db=db,
            password=password
        )
    return redis_connection

def notification_queue(queue_name, host, port, db, password=None, default_timeout=None):
    redis_connection=get_redis_connection(host, port, db, password)
    notif_queue = Queue(
        queue_name,
        connection=redis_connection,
        default_timeout=default_timeout
    )
    
    return notif_queue
