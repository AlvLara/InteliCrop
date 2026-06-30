import pika
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hmac
import hashlib
import database.mysql as db

from database.redis_db import RedisClient
from cryptography.fernet import Fernet

load_dotenv()

FERNET_KEY = os.getenv("FERNET_KEY", "").strip()

if not FERNET_KEY:
    raise RuntimeError("Falta FERNET_KEY en .env")

fernet = Fernet(FERNET_KEY.encode())


def descifrar_texto(texto_cifrado):
    return fernet.decrypt(texto_cifrado.encode()).decode()

redis_client = RedisClient()

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER_PROTECTION')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS_PROTECTION')

QUEUE_IN = "cola_sin_verificar"

# EXCHANGE DE SALIDA (en vez de cola)
EXCHANGE_OUT = 'sensores.exchange_proteccion'  # Nombre del exchange para alertas de protección de datos

credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
parametros = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    credentials=credenciales
)

conexion = pika.BlockingConnection(parametros)
channel = conexion.channel()



def callback(ch, method, properties, body):
    try:
        lectura = json.loads(body.decode("utf-8"))
        print(datetime.now(), "Procesando mensaje...")

        uuid_cultivo = lectura.get("uuid_cultivo")
        print("UUID Cultivo:", uuid_cultivo)
        payload = lectura.get("payload")
        hmac_lectura_payload = lectura.get("hmac")

        if not uuid_cultivo:
            print("Mensaje descartado: falta uuid_cultivo.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if payload is None:
            print("Mensaje descartado: falta payload.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if not hmac_lectura_payload:
            print("Mensaje descartado: falta HMAC.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if "time_envio" not in payload:
            print("Mensaje descartado: falta time_envio.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # =========================
        # OBTENER CULTIVO Y SECRETO
        # =========================

        cultivo = db.obtener_cultivo_por_uuid_cultivo(uuid_cultivo)

        if cultivo is None:
            print("Mensaje descartado: cultivo no encontrado o inactivo.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        clave_secreta = descifrar_texto(cultivo["secreto_cifrado"])

        # =========================
        # VALIDAR HMAC
        # =========================

        payload_para_hmac = json.dumps(
            payload,
            separators=(",", ":")
        ).encode("utf-8")

        hmac_calculado = hmac.new(
            clave_secreta.encode("utf-8"),
            payload_para_hmac,
            hashlib.sha256
        ).hexdigest()

        print("Payload para HMAC:", payload_para_hmac)
        print("HMAC recibido:", hmac_lectura_payload)
        print("HMAC calculado:", hmac_calculado)
        print("****************************")

        if not hmac.compare_digest(hmac_calculado, hmac_lectura_payload):
            print("Mensaje descartado por HMAC no coincidente.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # =========================
        # VALIDAR FECHA
        # =========================

        fecha = datetime.fromisoformat(payload["time_envio"])

        if datetime.now() - fecha > timedelta(seconds=20):
            print("Mensaje descartado por ser demasiado antiguo.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # =========================
        # EVITAR DUPLICADOS
        # =========================

        if redis_client.existe_clave(hmac_lectura_payload):
            print("Mensaje descartado por ser un duplicado.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        redis_client.guardar(
            hmac_lectura_payload,
            "1",
            expiracion=20
        )

        # =========================
        # PUBLICAR A EXCHANGE DE SALIDA
        # =========================

        mensaje_salida = json.dumps(
            lectura,
            ensure_ascii=False,
            separators=(",", ":")
        )

        channel.basic_publish(
            exchange=EXCHANGE_OUT,
            routing_key='sensores.validado',
            body=mensaje_salida.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json"
            )
        )

        print("Enviado a colas de salida")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print("Error:", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


if __name__ == "__main__":
    print("Worker iniciado")

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_IN,
        on_message_callback=callback,
        auto_ack=False
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Deteniendo consumidor...")
        channel.stop_consuming()