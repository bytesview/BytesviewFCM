import onesignal
from onesignal.model.notification import Notification
from onesignal.api import default_api
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from BytesViewFCM.notification_exception import  RateLimitExceeded
from BytesViewFCM.logger import logger

class OneSignalClient:

    def send_notification(self, app_name: str, credential, messages: list):
        if credential.get('ONESIGNAL_REST_API_KEY') is None:
            raise ValueError("Missing OneSignal API key")
        service_delivery_result = {"service": "onesignal", "notif_data": [], "failed": []}
        with onesignal.ApiClient(onesignal.Configuration(app_key=credential.get('ONESIGNAL_REST_API_KEY'))) as api_client:
            api_instance = default_api.DefaultApi(api_client)
            def send_single_notification(message):
                try:
                    notification = Notification(
                        app_id=credential.get("ONESIGNAL_APP_ID"),
                        contents={"en": message.get('body')},
                        headings={"en": message.get('title')},
                        include_player_ids=[message.get('player_id')],
                        data=message.get('data', None)
                    )
                    notification.large_icon = message.get('image', None)
                    notification.big_picture = message.get('big_picture', None)
                    if message.get("android_channel_id"):
                        notification.android_channel_id=message.get("android_channel_id")
                    response = api_instance.create_notification(notification)
                    
                    if 'errors' in response and 'invalid_player_ids' in response['errors']:
                        return {"data": message.get('data'), "error": "invalid playerid", "code": 'NOT_FOUND', "status": "failed"}
                    
                    return {"data": message.get('data'), "status": "success"}
                
                except Exception as e:
                    logger.error(f"failed to send notfication to {message.get('player_id')}")
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