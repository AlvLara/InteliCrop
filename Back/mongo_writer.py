import os
import json

import pika
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv

import database.mongodb as mongo
from database.redis_db import RedisClient


load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
RABBITMQ_USER = os.getenv("RABBITMQ_USER_PYTHON_MONGO")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS_PYTHON_MONGO")
RABBITMQ_QUEUE_MONGO = os.getenv("RABBITMQ_QUEUE_MONGO", "cola_mongo_raw")


redis_client = RedisClient()



def procesar_mensaje(channel, method, properties, body):
    try:
        lectura = json.loads(body.decode("utf-8"))
        print(datetime.now(), "Procesando mensaje...")

        mongo.guardar_lectura_raw(lectura)

        print("Lectura guardada en MongoDB:")
        print(lectura)

        channel.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        print("Error: el mensaje recibido no es JSON válido")
        print(body)

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )

    except Exception as error:
        print("Error procesando mensaje:")
        print(error)

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )




if __name__ == "__main__":
    if not mongo.health_check():
        print("Error al conectar a MongoDB.")
        exit()

    print("Conexión a MongoDB exitosa.")

    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASS
    )

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=30
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.basic_qos(prefetch_count=10)

    channel.basic_consume(
        queue=RABBITMQ_QUEUE_MONGO,
        on_message_callback=procesar_mensaje,
        auto_ack=False
    )

    print(f"Esperando mensajes en la cola: {RABBITMQ_QUEUE_MONGO}")
    print("Pulsa CTRL + C para detener.")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Deteniendo consumidor...")
        channel.stop_consuming()
    finally:
        connection.close()