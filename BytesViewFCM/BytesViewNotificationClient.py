from BytesViewFCM.utils import notification_queue
from BytesViewFCM.FCMClient import FCMClient
from BytesViewFCM.OneSignalClient import OneSignalClient
from BytesViewFCM.NotificationTracker import NotificationTracker
from firebase_admin import  messaging
from typing import List
from BytesViewFCM.notification_exception import RateLimitExceeded
from uuid import uuid4
from time import time

class BytesViewNotificationClient:

    _instance = None
    _queue_instance = None
    _fcm_credential = {}
    _onesignal_credential={}
    _database_config=None
    REQUIRED_KEYS = {'device_token','title','body','image'}

    def __new__(cls, *args, **kwargs):
        
        if not cls._instance:
            cls._instance = super(BytesViewNotificationClient, cls).__new__(cls)

        return cls._instance
    
    def __init__(self,fcm_credentials:List[dict],onesignal_credentials:List[dict]=None,database_config:dict=None):
        """
        Parameters:
        onesignal_credentials : List[dict], optional
            A list of dictionaries containing the OneSignal credentials. Each dictionary should 
            include the following keys:
            
            - 'ONESIGNAL_REST_API_KEY': The REST API key for OneSignal, required for sending notifications.
            - 'ONESIGNAL_APP_ID': The application ID for OneSignal, required to identify the target app.

            This parameter is optional and can be set to None if OneSignal is not used.

        database_config : dict, optional
            Following keys required
                - 'host','database', 'user','password'
        
            Optional keys:
        - 'notification_log_table' (default: 'user_notification_tracking'): table used for tracking notifications.
        - 'device_token_table' (default: 'user_device_info'):table that stores device tokens 
          for notifications.
        """
        self.fcm_client=FCMClient()
        self.onesignal_client=OneSignalClient()

        for cred in fcm_credentials:
            BytesViewNotificationClient._fcm_credential.update(cred)

        if onesignal_credentials:
            for onesignal_cred in onesignal_credentials:
                BytesViewNotificationClient._onesignal_credential.update(onesignal_cred)

        if database_config:
            BytesViewNotificationClient._database_config=database_config
    def set_notification_queue(self, queue_name:str, redis_host:str='localhost',password:str=None, port:int=6379, db:int=1, default_timeout:int=900,
                         result_ttl:int=300, ttl:int=2400, failure_ttl:int=1296000):
        try:
            BytesViewNotificationClient._queue_instance = notification_queue(queue_name=queue_name, host=redis_host, port=port, db=db,password=password, default_timeout=default_timeout)
            self.result_ttl = result_ttl
            self.ttl = ttl
            self.failure_ttl = failure_ttl
        except Exception as e:
            return e
    
    def _prepare_messages(self,messages:List[dict])->List:
        processed_messages = []
        for index, message in enumerate(messages):
            missing_keys = [key for key in self.REQUIRED_KEYS if key not in message]
            if missing_keys:
                raise ValueError(f"Message at index {index} is missing keys: {missing_keys}")
            
            if 'data' not in message:
                message['data']={}
            message['data']['uuid']=''.join(str(uuid4()).split('-'))

            if 'onesignal_playerid' not  in message:
                try:
                    fcm_message=self.fcm_client.create_fcm_message(device_token=message['device_token'],
                                                                    title=message['title'], 
                                                                    body=message['body'], 
                                                                    image=message['image'] if message['image'] else message['big_picture'], 
                                                                    data=message['data'])
                    processed_messages.append(fcm_message)
                except Exception as e:
                    continue
            else:
                processed_messages.append({'player_id': message.get('onesignal_playerid'),
                                           'device_token': message['device_token'], 
                                           'title': message['title'],
                                           'body': message['body'],
                                           'image': message['image'],
                                           'data': message.get('data'), 
                                           'big_picture': message.get('big_picture'),
                                           'android_channel_id':message.get('notification_channel')
                                        })
        return processed_messages

    def _send_notifications(self, app_name, messages:List[dict], fcm_credential, onesignal_credential, database_config:dict,update_invalid_tokens:bool=False):
        try:
            start=time()
            if len(messages) > 500:
                raise ValueError('messages list must not contain more than 500 elements.')
            
            processed_messages=self._prepare_messages(messages=messages)
           
            self.notif_tracker=NotificationTracker(database_config=database_config)
            self.notif_tracker.set_connection()
            onesignal_list,fcm_list,invalid_token_list = [],[],[]
            for message in processed_messages:
                if isinstance(message, messaging.Message):
                    fcm_list.append(message)
                else:
                    onesignal_list.append(message)
            if onesignal_list :
                try:
                    service_result=self.onesignal_client.send_notification(app_name=app_name,credential=onesignal_credential,messages=onesignal_list)
                    self.notif_tracker.log_notifications(service_result)
                    if service_result and  service_result['failed']:
                        invalid_token_list.append(service_result['failed'])
                except RateLimitExceeded:
                    self._fallback_to_fcm(onesignal_list, fcm_list)
                except Exception as e:
                    raise
            if fcm_list:
                service_result=self.fcm_client.fcm_bulk_send(
                    app_name=app_name,
                    credential=fcm_credential,
                    batch_of_message=fcm_list
                ) 
                self.notif_tracker.log_notifications(service_result)
                if service_result and service_result['failed']:
                    invalid_token_list.append(service_result['failed'])
            if invalid_token_list and update_invalid_tokens:
                self.notif_tracker.update_invalid_device_tokens(invalid_tokens=invalid_token_list)
            return {'status': 'success'}
        except Exception as e:
            raise
        finally:
            self.notif_tracker.close_connection()
        
    def send_immediate_notification(self, app_name, messages: list,update_invalid_tokens=False):
        return self._send_notifications(app_name=app_name,
                                        messages=messages,
                                        fcm_credential=BytesViewNotificationClient._fcm_credential[app_name],
                                        onesignal_credential=BytesViewNotificationClient._onesignal_credential[app_name],
                                        database_config=self._database_config,
                                        update_invalid_tokens=update_invalid_tokens,
                                        )
       
    def send_notification_by_queue(self,app_name,messages,fcm_credential,onesignal_credential,database_config,update_invalid_tokens=False):
        return self._send_notifications(app_name=app_name,
                                        messages=messages,
                                        fcm_credential=fcm_credential,
                                        onesignal_credential=onesignal_credential,
                                        database_config=database_config,
                                        update_invalid_tokens=update_invalid_tokens,
                                        )

    def _fallback_to_fcm(self, onesignal_list, fcm_list):
        """
        Method to convert Onesignal Message To Fcm Message
        """

        for onesignal_message in onesignal_list:
            fcm_message = self.fcm_client.create_fcm_message(
                device_token=onesignal_message['device_token'],
                title=onesignal_message['title'],
                body=onesignal_message['body'],
                image=onesignal_message['image'],
                data=onesignal_message['data']
            )
            fcm_list.append(fcm_message)
    
    def enqueue_messages(self,app_name,messages,update_invalid_tokens=False):
        """
         Parameters:
            - app_name (str): application sending notification.
            - messages (list of dict): for tracking notification data object required follwing keys:
                        -'u_id': User ID of the notification recipient.
                        -'device': Device Id
                        -'category': Category ID for tracking purposes. Must be digit
            Any missing keys will result in null values for those columns in tracking.
            - update_invalid_tokens (bool, optional): Whether to update invalid tokens if found. 
            Defaults to False.
        """
        try:
            if BytesViewNotificationClient._queue_instance:
                BytesViewNotificationClient._queue_instance.enqueue(self.send_notification_by_queue,args=(app_name,messages,BytesViewNotificationClient._fcm_credential[app_name],BytesViewNotificationClient._onesignal_credential[app_name],BytesViewNotificationClient._database_config,update_invalid_tokens), result_ttl=self.result_ttl, ttl=self.ttl, failure_ttl=self.failure_ttl) 
            else:
                raise ValueError("queue not configured")
            return {'status':'success'}
        except Exception as e:
            raise
        
    def _multicast_notification(self, app_name,tokens:list, message:dict, fcm_credential, onesignal_credential, database_config:dict,update_invalid_tokens:bool=False):
        """method is useful when we want send same message to large audience"""
        try:
            if len(tokens)>2000:
                raise ValueError('messages list must not contain more than 2000 elements.')
            if 'data' not in message:
                message['data']={}
            onesignal_playerids,fcm_device_tokens=[],[]
            self.notif_tracker=NotificationTracker(database_config=database_config)
            self.notif_tracker.set_connection()

            for token in tokens:
                if token.get("onesignal_playerid",None):
                    onesignal_playerids.append(token['onesignal_playerid'])
                elif token.get('device_token',None):
                    fcm_device_tokens.append(token['device_token'])
                else:
                    raise ValueError("Each element of token must have either onesignal_playerid or device_token")
            invalid_onesignal_tokens=[]
            if onesignal_playerids:
                try:
                    message['data']['uuid']=''.join(str(uuid4()).split('-'))
                    invalid_onesignal_tokens=self.onesignal_client.send_multicast(credential=onesignal_credential,message=message,tokens=onesignal_playerids)
                    self.notif_tracker.log_multicast_notifications(message_data=message.get('data'),service_name='onesignal',
                                                                total_notification=len(onesignal_playerids),
                                                                failed_to_sent=len(invalid_onesignal_tokens)            
                                                                )
                except RateLimitExceeded:
                    fcm_device_tokens.extend([token['device_token'] for token in tokens if token['onesignal_playerid'] is not None])
                except Exception as e:
                    raise
            invalid_fcm_tokens=[]
            if fcm_device_tokens:
                message['data']['uuid']=''.join(str(uuid4()).split('-'))
                for i in range(0, len(fcm_device_tokens), 500):
                    fcm_message = self.fcm_client.create_multicast_message(
                        device_tokens= fcm_device_tokens[i:i + 500],
                        title=message.get('title', None),
                        body=message.get('body', None),
                        image=message.get('image', None),
                        data=message.get('data', None)
                    )
                
                    invalid_fcm_tokens.extend(self.fcm_client.send_multicast(app_name=app_name,credential=fcm_credential,message=fcm_message))
                self.notif_tracker.log_multicast_notifications(message_data=message.get('data'),service_name='fcm',
                                                               total_notification=len(fcm_device_tokens),
                                                               failed_to_sent=len(invalid_fcm_tokens)            
                                                                )
            device_with_invalid_token = [token['device_id'] for token in tokens
                                  if (token.get('onesignal_playerid') in invalid_onesignal_tokens) or
                                  (token.get('device_token') in invalid_fcm_tokens)
                                ]   
            if device_with_invalid_token and update_invalid_tokens:
                self.notif_tracker.update_invalid_device_tokens(device_with_invalid_tokens=device_with_invalid_token)
                    
        except Exception as e:
            raise
        finally:
            self.notif_tracker.close_connection()
            
    def send_immediate_multicast_notification(self, app_name,tokens:list, message: dict,update_invalid_tokens=False):
        return self._multicast_notification(app_name=app_name,
                                            tokens=tokens,
                                        message=message,
                                        fcm_credential=BytesViewNotificationClient._fcm_credential[app_name],
                                        onesignal_credential=BytesViewNotificationClient._onesignal_credential[app_name],
                                        database_config=self._database_config,
                                        update_invalid_tokens=update_invalid_tokens,
                                        )
       
    def send_multicast_notification_by_queue(self,app_name,tokens,message,fcm_credential,onesignal_credential,database_config,update_invalid_tokens=False):
        return self._multicast_notification(app_name=app_name,
                                            tokens=tokens,
                                        message=message,
                                        fcm_credential=fcm_credential,
                                        onesignal_credential=onesignal_credential,
                                        database_config=database_config,
                                        update_invalid_tokens=update_invalid_tokens,
                                        )
    
    def enqueue_multicast_message(self,app_name,tokens,message,update_invalid_tokens=False):
        try:
            if BytesViewNotificationClient._queue_instance:
                BytesViewNotificationClient._queue_instance.enqueue(self.send_multicast_notification_by_queue,
                                                                    args=(app_name,tokens,message,BytesViewNotificationClient._fcm_credential[app_name],
                                                                          BytesViewNotificationClient._onesignal_credential[app_name],
                                                                          BytesViewNotificationClient._database_config,update_invalid_tokens,
                                                                          ), 
                                                                    result_ttl=self.result_ttl, ttl=self.ttl, failure_ttl=self.failure_ttl
                                                                    ) 
            else:
                raise ValueError("queue not configured")
            return {'status':'success'}
        except Exception as e:
            raise 