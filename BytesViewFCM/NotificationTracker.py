import mysql.connector
from mysql.connector import Error
from BytesViewFCM.notification_exception import TableNotExistError

class NotificationTracker:

    def __init__(self,database_config):
        self.host =database_config ['host']
        self.database =database_config ['database']
        self.user = database_config['user']
        self.port=int(database_config.get('port',"3306"))
        self.password = database_config['password']
        self.notification_log_table=database_config.get('notification_log_table','user_notification_tracking')
        self.device_token_table=database_config.get('device_token_table','user_device_info')
        self.connection=None


    def set_connection(self):
        if not self.connection or not self.connection.is_connected():
            self.connection = mysql.connector.connect(host=self.host,port=self.port,user=self.user,passwd=self.password,database=self.database)
        
    def close_connection(self):
        self.connection.close()
        
    def append_notification(self,notification_data, data_obj, service_name, status,is_success,total_notifications,failed_to_sent,total_clicks):
        """Append notification data to the list."""
        data = data_obj.get('data', {})
        notification_data.append((
            data.get('device',None),
            data.get('u_id'),
            data.get('uuid'),
            data.get('category'),
            service_name,
            status,
            is_success,total_notifications,failed_to_sent,total_clicks
    ))
    def log_notifications(self, service_result):
        cursor = self.connection.cursor()
        notification_data = []
        for data_obj in service_result.get('notif_data', []):
            self.append_notification(notification_data, data_obj, service_result.get('service', 'unknown'), "success",is_success=1,total_notifications=1,failed_to_sent=0,total_clicks=0)
        for data_obj in service_result.get('failed', []):
            self.append_notification(notification_data, data_obj, service_result.get('service', 'unknown'), data_obj.get('error', "unknown"),is_success=0,total_notifications=1,failed_to_sent=1,total_clicks=0)
        try:
            cursor.executemany(f"""INSERT INTO {self.notification_log_table} (device_id, user_id, uuid, category_id, service_name, status,is_success,total_notifications,failed_to_sent,total_clicks)
                                VALUES (%s, %s, %s, %s, %s, %s,%s,%s,%s,%s)""", notification_data)
            self.connection.commit()

        except Error as e:
            if e.errno == mysql.connector.errorcode.ER_NO_SUCH_TABLE:
                raise TableNotExistError(f"Table {self.device_token_table} doesn't exist and required columns are device_id, user_id, uuid, category_id, service_name, status ")
            else:
                raise
        finally:
            cursor.close()

    def update_invalid_device_tokens(self,invalid_tokens=None,device_with_invalid_tokens=None):
        if invalid_tokens:
            device_ids = [token['data']['device'] for sublist in invalid_tokens for token in sublist if 'code' in token and token['code'] == 'NOT_FOUND']
        else:
            device_ids=device_with_invalid_tokens
        if device_ids:
            cursor = self.connection.cursor()
            try:
                for i in range(0, len(device_ids), 100):
                    batch = device_ids[i:i + 100]

                cursor.execute(f"""UPDATE {self.device_token_table} SET invalid_token = 1 WHERE device_id IN ({', '.join(['%s'] * len(batch))})""", batch)
                self.connection.commit()
            except Exception as e:
                raise
            finally:
                cursor.close()
                
    def log_multicast_notifications(self,message_data,service_name,total_notification,failed_to_sent):
        try:
            category_id=message_data.get('category',None)
            uuid=message_data.get('uuid',None)
            cursor=self.connection.cursor()
            cursor.execute(f"""INSERT INTO {self.notification_log_table} (device_id,uuid, category_id, service_name, status,is_success,total_notifications,failed_to_sent,total_clicks)
                                VALUES (%s, %s, %s, %s, %s, %s,%s,%s,%s)""", (None,uuid,category_id,service_name,"success",'1',total_notification,failed_to_sent,'0'))
            self.connection.commit()
            
        except Exception as e:
            raise
        finally:
            cursor.close()