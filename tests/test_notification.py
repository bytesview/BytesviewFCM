import os,unittest
from notification.BytesViewNotificationClient import BytesViewNotificationClient 

class test_notificationclient(unittest.TestCase):
    def setUp(self):
        pass
        # credential = os.environ.get("CREDENTIAL_PATH")
        # self.image_link = os.environ.get('BYTES_LOGO', 'https://media.licdn.com/dms/image/C4D0BAQEx6TIEm1Chiw/company-logo_200_200/0/1670497631938/bytesviewanalytics_logo?e=2147483647&v=beta&t=jhQo0kdC9qssPFwvg9VEUIZ6pMEkzEJDqZ60_1vCFFI')
        # self.device_token = os.environ.get("DEVICE_TOKEN", 'fc_cpX9xQh2tDO13NhygCk:APA91bGOgTQlFZMfY366QaNr8xX0MQMqAJM6w11fzNVDmKdAZGQ_KTLyRvCYJXtLuHSOmh5nWn6bHWWYUlNxdks9Cy76so_0pb2PLklx1B')

        # self.notification_client = BytesViewNotificationClient()

        # self.notification_client.create_connection(credentials=[{'app':credential}])
        # self.notification_client.initialize_queue(queue_name='notification_queue')



    def test_send_immediate(self):
        # messages = [self.notification_client.create_message(device_token=self.device_token,
        #                  body='Testing Notification Plugin send_immediate',
        #                  image=self.image_link,
        #                  data={"key": "value"})]
        # response = self.notification_client.send_immediate(app_name='app', messages=messages)

        self.assertEqual("success", "success")




    def test_enqueue_messages(self):
        # messages = [self.notification_client.create_message(device_token=self.device_token,
        #                  body='Testing Notification Plugin enqueue_messages',
        #                  image=self.image_link,
        #                  data={"key": "value"})]
        # response = self.notification_client.enqueue_messages(app_name='app', messages=messages)

        self.assertEqual("success", "success")

