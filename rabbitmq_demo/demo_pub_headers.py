import pika
import json
import yaml

def send_headers_message(headers: dict, message: dict) -> None:
    """
    發送一個帶有指定頭部信息的消息到RabbitMQ的headers交換機。

    Args:
        headers (dict): 要附加到消息的頭部信息。
        message (dict): 要發送的消息內容。

    Returns:
        None

    Raises:
        pika.exceptions.AMQPError: 如果與RabbitMQ服務器的連接或通信出現問題。
        yaml.YAMLError: 如果讀取配置文件時出現錯誤。
    """
    # 從YAML配置文件中讀取RabbitMQ連接信息
    with open('rabbitmq_config.yaml', 'r') as f:
        config = yaml.safe_load(f)['rabbitmq']

    # 創建RabbitMQ連接憑證
    credentials = pika.PlainCredentials(config['username'], config['password'])

    # 設置RabbitMQ連接參數
    parameters = pika.ConnectionParameters(
        host=config['host'],
        port=config['port'],
        virtual_host=config['vhost'],
        credentials=credentials
    )

    # 建立到RabbitMQ服務器的連接
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # 聲明一個headers類型的交換機
    channel.exchange_declare(exchange="demo_headers", exchange_type='headers')

    # 發布消息到交換機
    channel.basic_publish(
        exchange="demo_headers",
        routing_key='',  # headers交換機不使用routing_key
        body=json.dumps(message),
        properties=pika.BasicProperties(headers=headers)
    )

    print(f"Sent headers message with headers {headers}: {message}")

    # 關閉連接
    connection.close()

if __name__ == "__main__":
    # 定義示例頭部信息和消息
    headers = {'category': 'electronics', 'priority': 'high'}
    message = {
        'type': 'headers',
        'data': 'This is a headers message about high-priority electronics'
    }

    # 調用函數發送消息
    send_headers_message(headers, message)
