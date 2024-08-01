from rq import Queue
from redis import Redis
from FCMClient import FCMClient


def notification_queue(queue_name:str, host:str='localhost', port:int=6379, db:int=1, default_timeout:int=900):
    notif_queue = Queue(
        queue_name, 
        connection=Redis(
            host=host, 
            port=port, 
            db=db),
        default_timeout=default_timeout,
        db=db)
    return notif_queue



def send_notification(credential, messages):
    
    if len(messages) == 1:
        FCMClient().fcm_send(credential=credential, message=messages[0])
    else:
        for batch_of_message in [messages[i:i+500] for i in range(0, len(messages), 500)]:
            FCMClient().fcm_bulk_send(credential=credential, batch_of_message=batch_of_message)

