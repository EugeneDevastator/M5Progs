import socket
import asyncio
from hbmqtt.broker import Broker

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1

class LoggingBroker(Broker):
    async def on_broker_post_publish(self, *args, **kwargs):
        message = args[0]
        print(f'Topic: {message.topic}, Payload: {message.data.decode("utf-8")}')
        await super().on_broker_post_publish(*args, **kwargs)

config = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'bind': '0.0.0.0:1883'
        },
    },
    'sys_interval': 10,
    'topic-check': {
        'enabled': False  # Disable topic_check plugin
    }
}

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

async def broker_coro():
    broker = Broker(config)
    await broker.start()
    ip_address = get_ip_address()
    port = config['listeners']['default']['bind'].split(':')[-1]
    print(f'MQTT Server is running on: tcp://{ip_address}:{port}')
    while True:
        # Keep the broker running indefinitely
        await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(broker_coro())
