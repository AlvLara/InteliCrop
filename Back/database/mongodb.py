from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")


# =====================================================
# CONEXIÓN GLOBAL
# =====================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=3000
)

db = client[MONGO_DB]

lecturas = db["lecturas_raw"]


# =====================================================
# HEALTH
# =====================================================

def health_check() -> bool:
    try:
        client.admin.command("ping")
        return True

    except PyMongoError as e:
        print(f"Error en health_check: {e}")
        return False

    except Exception as e:
        print(f"Error inesperado en health_check: {e}")
        return False


# =====================================================
# LECTURAS
# =====================================================

def guardar_lectura_raw(lectura: dict):

    try:
        entrada = {
            "created_at": datetime.now(timezone.utc),

            "metadata": {
                "uuid_cultivo": lectura.get(
                    "uuid_cultivo",
                    "desconocido"
                )
            },

            "data": {
                "temperatura": lectura.get("payload", {}).get("temperatura"),
                "humedad": lectura.get("payload", {}).get("humedad"),
                "lluvia": lectura.get("payload", {}).get("lluvia"),
                "humedad_suelo": lectura.get("payload", {}).get("humedad_suelo"),
                "esta_lloviendo": lectura.get("payload", {}).get("esta_lloviendo"),
                "ts": lectura.get("payload", {}).get("ts")
            }
        }

        lecturas.insert_one(entrada)

        return True

    except PyMongoError as e:
        print(f"Error en guardar_lectura_raw: {e}")
        return False

    except Exception as e:
        print(f"Error inesperado en guardar_lectura_raw: {e}")
        return False


def obtener_ultima_lectura(uuid_cultivo: str):

    try:

        lectura = lecturas.find_one(
            {"metadata.uuid_cultivo": uuid_cultivo},
            sort=[("created_at", -1)]
        )

        return lectura

    except PyMongoError as e:
        print(f"Error en obtener_ultima_lectura: {e}")
        return None

    except Exception as e:
        print(f"Error inesperado en obtener_ultima_lectura: {e}")
        return None
    
def obtener_historial_cultivo(uuid_cultivo: str, limite: int = 100):
    try:
        
        cursor = lecturas.find(
            {"metadata.uuid_cultivo": uuid_cultivo}
        ).sort("created_at", -1).limit(limite) 
        
       
        historial = list(cursor)
        return historial

    except PyMongoError as e:
        print(f"Error en obtener_historial_cultivo: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado en obtener_historial_cultivo: {e}")
        return None
    
