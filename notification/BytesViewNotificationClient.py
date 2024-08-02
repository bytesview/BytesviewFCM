from notification.utils import notification_queue
from notification.FCMClient import FCMClient
from notification.utils import send_notification



class BytesViewNotificationClient(FCMClient):

    _instance = None
    _queue_instance = None
    _credential = {}

    def __new__(cls, *args, **kwargs):
        
        if not cls._instance:
            cls._instance = super(BytesViewNotificationClient, cls).__new__(cls)

        return cls._instance
    

    def create_connection(self, credentials:list):
        for cred in credentials:
            BytesViewNotificationClient._credential.update(cred)


    def initialize_queue(self, queue_name:str, host:str='localhost', port:int=6379, db:int=1, default_timeout:int=900,
                         result_ttl:int=300, ttl:int=2400, failure_ttl:int=1296000):
        try:
            BytesViewNotificationClient._queue_instance = notification_queue(queue_name=queue_name, host=host, port=port, db=db, default_timeout=default_timeout)
            self.result_ttl = result_ttl
            self.ttl = ttl
            self.failure_ttl = failure_ttl
        except Exception as e:
            return e


    def create_message(self, device_token: str, body: str, image: str, data: dict={}):
        try:
            return FCMClient.create_fcm_message(self, device_token, body, image, data)
        except Exception as e:
            return e
    

    def send_immediate(self, app_name, messages:list):
        try:
            if len(messages) == 1:
                FCMClient.fcm_send(self, credential=BytesViewNotificationClient._credential[app_name], message=messages[0])
            else:
                for batch_of_message in [messages[i:i+500] for i in range(0, len(messages), 500)]:
                    FCMClient.fcm_bulk_send(self, credential=BytesViewNotificationClient._credential[app_name], batch_of_message=batch_of_message)
            return {'status':'success'}
        except Exception as e:
            return e


    def enqueue_messages(self, app_name, messages:list):
        try:
            if BytesViewNotificationClient._queue_instance:
                BytesViewNotificationClient._queue_instance.enqueue(send_notification,args=(BytesViewNotificationClient._credential[app_name],messages,), result_ttl=self.result_ttl, ttl=self.ttl, failure_ttl=self.failure_ttl) 
            else:
                return('queue not configured')
            return {'status':'success'}
        except Exception as e:
            return e
            
