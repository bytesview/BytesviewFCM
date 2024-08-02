import firebase_admin
from firebase_admin import credentials, messaging
import json


class FCMClient:

    def create_fcm_message(self, device_token:str, body:str, image:str, data:dict):
        return messaging.Message(
            token=device_token,
            notification=messaging.Notification(
                body=body, image=image
            ),
            data=data
        )

    def fcm_send(self, credential:json, message:messaging.Message):
        app = firebase_admin.initialize_app(credentials.Certificate(credential))
        response = messaging.send(message, app=app)
        return response

    def fcm_bulk_send(self, credential:json, batch_of_message:list):
        app = firebase_admin.initialize_app(credentials.Certificate(credential))
        response = messaging.send_each(batch_of_message, app=app)
        return response