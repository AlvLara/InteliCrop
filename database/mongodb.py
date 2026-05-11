from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import PyMongoError


import os

from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

class MongoRepository:
    def __init__(self):
        uri = MONGO_URI

        self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.db = self.client[MONGO_DB]
        self.lecturas = self.db["lecturas_raw"]

    def health_check(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def guardar_lectura_raw(self, lectura: dict):
        entrada={
            "created_at": datetime.now(timezone.utc),
            "metadata": {
                "sensor_id": lectura.get("sensor_id","desconocido")
            },
            "data": {
                "temperatura": lectura.get("temperatura"),
                "humedad": lectura.get("humedad"),
                "lluvia": lectura.get("lluvia"),
                "humedad_suelo": lectura.get("humedad_suelo"),
                "esta_lloviendo": lectura.get("esta_lloviendo"),
                "ts": lectura.get("ts")
            }
        }
        self.lecturas.insert_one(entrada)

        
