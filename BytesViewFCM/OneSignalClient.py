import onesignal
from onesignal.model.notification import Notification
from onesignal.api import default_api
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from BytesViewFCM.notification_exception import  RateLimitExceeded

class OneSignalClient:
    def _create_notification(self, message:dict, player_ids=None)->Notification:
        notification = Notification(
            app_id=self.credential.get("ONESIGNAL_APP_ID"),
            contents={"en": message.get('body')},
            headings={"en": message.get('title')},
            include_player_ids=player_ids or message.get('player_id').split(','),
            data=message.get('data', None)
        )
        if message.get('image',None):
            notification.large_icon = message.get('image', None)
        if message.get('big_picture',None):
            notification.big_picture = message.get('big_picture', None)
        if message.get("android_channel_id"):
            notification.android_channel_id=message.get("android_channel_id")
        return notification
    
    def send_notification(self, app_name: str, credential, messages: list):
        if not credential.get('ONESIGNAL_REST_API_KEY'):
            raise ValueError("Missing OneSignal API key")
        self.credential=credential
        service_delivery_result = {"service": "onesignal", "notif_data": [], "failed": []}
        with onesignal.ApiClient(onesignal.Configuration(app_key=credential.get('ONESIGNAL_REST_API_KEY'))) as api_client:
            api_instance = default_api.DefaultApi(api_client)
            def send_single_notification(message):
                try:
                    notification=self._create_notification(message)
                    response = api_instance.create_notification(notification)
                    
                    if 'errors' in response and 'invalid_player_ids' in response['errors']:
                        return {"data": message.get('data'), "error": "invalid playerid", "code": 'NOT_FOUND', "status": "failed"}
                    
                    return {"data": message.get('data'), "status": "success"}
                
                except Exception as e:
                    if hasattr(e, 'status') and e.status == 429:
                        raise  RateLimitExceeded
                    elif hasattr(e, 'status') and e.status == 400:
                        return {"data": message.get('data'), "error": json.loads(e.body)["errors"][0], "code": 'NOT_FOUND', "status": "failed"}
                    else:
                        raise

            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_message = {executor.submit(send_single_notification, message): message for message in messages}
                for future in as_completed(future_to_message):
                    result = future.result(timeout=20)
                    if result["status"] == "success":
                        service_delivery_result['notif_data'].append(result)
                    else:
                        service_delivery_result['failed'].append(result)
        return service_delivery_result
    
    def send_multicast(self,credential,message:dict,tokens:list):
        try:
            if not credential.get('ONESIGNAL_REST_API_KEY'):
                raise ValueError("Missing OneSignal API key")
            self.credential=credential
            with onesignal.ApiClient(onesignal.Configuration(app_key=self.credential.get('ONESIGNAL_REST_API_KEY'))) as api_client:
                api_instance = default_api.DefaultApi(api_client)
                notification=self._create_notification(message,player_ids=tokens)
                response = api_instance.create_notification(notification)
                if 'errors' in response and 'invalid_player_ids' in response['errors']:
                    return response['errors']['invalid_player_ids']
                else:
                    return []
        except Exception as e:
            raise
        