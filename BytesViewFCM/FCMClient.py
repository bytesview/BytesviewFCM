import firebase_admin
from firebase_admin import credentials, messaging
import json


class FCMClient:

    _initialized_apps = {}

    def create_fcm_message(self, device_token:str, title:str, body:str, image:str, data:dict):
        return messaging.Message(
            token=device_token,
            notification=messaging.Notification(
                title=title, body=body, image=image
            ),
            data=data
        )

    def fcm_send(self, app_name:str, credential:json, message:messaging.Message):
        if app_name not in FCMClient._initialized_apps:
            FCMClient._initialized_apps[app_name] = firebase_admin.initialize_app(credentials.Certificate(credential))
        response = messaging.send(message, app=FCMClient._initialized_apps[app_name])
        return response

    def fcm_bulk_send(self, app_name:str, credential:json, batch_of_message:list):
        if app_name not in FCMClient._initialized_apps:
            FCMClient._initialized_apps[app_name] = firebase_admin.initialize_app(credentials.Certificate(credential))
        response = messaging.send_each(batch_of_message, app=FCMClient._initialized_apps[app_name])
        return response