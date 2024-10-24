import pika
import json
import yaml

def send_test_message(routing_key, message):
    """
    向 RabbitMQ 發送測試消息。

    參數:
    routing_key (str): 用於路由消息的鍵。
    message (dict): 要發送的消息內容。

    功能:
    1. 從 YAML 文件加載 RabbitMQ 配置。
    2. 建立與 RabbitMQ 的連接。
    3. 聲明交換機並發布消息。
    4. 關閉連接。
    """
    # 從 YAML 文件加載 RabbitMQ 配置
    with open('rabbitmq_config.yaml', 'r') as f:
        config = yaml.safe_load(f)['rabbitmq']

    # 創建到 RabbitMQ 的連接
    credentials = pika.PlainCredentials(config['username'], config['password'])
    parameters = pika.ConnectionParameters(
        host=config['host'],
        port=config['port'],
        virtual_host=config['vhost'],
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # 向 RabbitMQ 發送消息
    channel.exchange_declare(exchange=config['exchange'],
                             exchange_type="direct")
    channel.basic_publish(exchange=config['exchange'],
                          routing_key=routing_key,
                          body=json.dumps(message))
    print(f"已發送消息到 {routing_key}: {message}")

    # 關閉連接
    connection.close()

if __name__ == "__main__":
    # 主程序入口點
    # 定義路由鍵和測試消息
    routing_key = "camera-live-1"
    message = {
        'camera_id': 1,
        'frame_data': 'Test frame data'
    }
    # 調用函數發送測試消息
    send_test_message(routing_key, message)
