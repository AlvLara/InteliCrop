import os
import json
import pika
def cifrar_texto(texto,fernet):
    return fernet.encrypt(texto.encode()).decode()


def descifrar_texto(texto_cifrado,fernet):
    return fernet.decrypt(texto_cifrado.encode()).decode()


def publicar_en_rabbitmq(mensaje):
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbitmq_user = os.getenv("RABBITMQ_USER")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")

    rabbitmq_exchange = os.getenv("RABBITMQ_EXCHANGE", "amq.topic")
    rabbitmq_routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "sensores.raw")

    credentials = pika.PlainCredentials(
        rabbitmq_user,
        rabbitmq_password
    )

    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=10
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    mensaje_json = json.dumps(
        mensaje,
        ensure_ascii=False,
        separators=(",", ":")
    )

    channel.basic_publish(
        exchange=rabbitmq_exchange,
        routing_key=rabbitmq_routing_key,
        body=mensaje_json.encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json"
        )
    )

    connection.close()