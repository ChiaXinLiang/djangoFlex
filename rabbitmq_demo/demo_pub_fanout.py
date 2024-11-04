import pika
import json
import yaml

def send_fanout_message(message):
    """
    向 RabbitMQ 發送扇出（fanout）消息。

    這個函數從配置文件讀取 RabbitMQ 連接信息，建立連接，
    然後向指定的交換機發送消息。

    參數:
    message (dict): 要發送的消息，將被轉換為 JSON 格式。

    返回:
    None
    """
    # 從 YAML 配置文件讀取 RabbitMQ 配置
    with open('rabbitmq_config.yaml', 'r') as f:
        config = yaml.safe_load(f)['rabbitmq']

    # 創建 RabbitMQ 連接憑證
    credentials = pika.PlainCredentials(config['username'], config['password'])

    # 設置 RabbitMQ 連接參數
    parameters = pika.ConnectionParameters(
        host=config['host'],
        port=config['port'],
        virtual_host=config['vhost'],
        credentials=credentials
    )

    # 建立到 RabbitMQ 服務器的連接
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # 聲明一個 fanout 類型的交換機
    channel.exchange_declare(exchange="demo_fanout", exchange_type='fanout')

    # 發布消息到交換機
    channel.basic_publish(exchange='demo_fanout',
                          routing_key='',
                          body=json.dumps(message))
    print(f"Sent fanout message: {message}")

    # 關閉連接
    connection.close()

if __name__ == "__main__":
    # 定義要發送的消息
    message = {
        'type': 'fanout',
        'data': 'This is a fanout message'
    }
    # 調用函數發送消息
    send_fanout_message(message)
