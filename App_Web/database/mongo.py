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
    
def obtener_historial_semanal(uuid_cultivo: str):
    try:
        
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)

        pipeline = [
           
            {
                "$match": {
                    "metadata.uuid_cultivo": uuid_cultivo,
                    "created_at": {"$gte": fecha_limite}
                }
            },
            
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "day": {"$dayOfMonth": "$created_at"},
                        "hour": {"$hour": "$created_at"}
                    },
                    "temperatura_avg": {"$avg": "$data.temperatura"},
                    "humedad_avg": {"$avg": "$data.humedad"},
                    "humedad_suelo_avg": {"$avg": "$data.humedad_suelo"},
                    "lluvia_avg": {"$avg": "$data.lluvia"},
                    "esta_lloviendo": {"$max": "$data.esta_lloviendo"}, 
                    "fecha_referencia": {"$first": "$created_at"} 
                }
            },
            
            {
                "$sort": {"fecha_referencia": -1}
            }
        ]

        cursor = lecturas.aggregate(pipeline)
        
        
        historial_formateado = []
        for doc in cursor:
            fecha_hora = datetime(
                doc["_id"]["year"], 
                doc["_id"]["month"], 
                doc["_id"]["day"], 
                doc["_id"]["hour"],
                tzinfo=timezone.utc
            )
            
            historial_formateado.append({
                "created_at": fecha_hora,
                "data": {
                    "temperatura": round(doc.get("temperatura_avg") or 0, 1),
                    "humedad": round(doc.get("humedad_avg") or 0, 1),
                    "humedad_suelo": round(doc.get("humedad_suelo_avg") or 0, 1),
                    "lluvia": round(doc.get("lluvia_avg") or 0, 1),
                    "esta_lloviendo": bool(doc.get("esta_lloviendo"))
                }
            })

        return historial_formateado

    except PyMongoError as e:
        print(f"Error en obtener_historial_semanal: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado en obtener_historial_semanal: {e}")
        return []