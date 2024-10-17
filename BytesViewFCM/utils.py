from redis import Redis
from rq import Queue

def notification_queue(queue_name, host, port, db, password=None, default_timeout=None):
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
    notif_queue = Queue(
        queue_name,
        connection=redis_connection,
        default_timeout=default_timeout
    )
    
    return notif_queue
