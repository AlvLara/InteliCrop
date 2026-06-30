import os
import redis
from dotenv import load_dotenv

class RedisClient:
    def __init__(self):
        """Inicializa la clase cargando el entorno y estableciendo la conexión."""
        load_dotenv()
        
        # Atributos privados (encapsulados) para aislar los datos de conexión
        self.__host = os.getenv("REDIS_HOST", "localhost")
        self.__port = int(os.getenv("REDIS_PORT", 6379))
        self.__user = os.getenv("REDIS_USER", "tu_usuario_iot")
        self.__password = os.getenv("REDIS_PASS", "tu_contraseña")
        
        # El cliente interno de Redis
        self.client = None
        
        # Intentar conectar automáticamente al instanciar el objeto
        self._conectar()

    def _conectar(self):
        """Método interno para gestionar la conexión y autenticación."""
        try:
            self.client = redis.Redis(
                host=self.__host,
                port=self.__port,
                username=self.__user,
                password=self.__password,
                db=0, 
                decode_responses=True
            )
            # Hacemos un ping para asegurar que la conexión realmente funciona
            self.client.ping()
            print("[Redis] Conectado y autenticado correctamente.")
            
        except redis.AuthenticationError:
            print("[Redis] Error: El usuario o la contraseña son incorrectos.")
            self.client = None
        except redis.ConnectionError:
            print("[Redis] Error: No se pudo conectar al servidor.")
            self.client = None

    # --- ACCIONES (Métodos públicos para interactuar con Redis) ---

    def guardar(self, clave, valor, expiracion=20):
        """Guarda un par clave-valor. Opcionalmente acepta tiempo de expiración en segundos."""
        if not self.client:
            print("No hay conexión con Redis.")
            return False
        try:
            if expiracion:
                return self.client.setex(clave, expiracion, valor)
            return self.client.set(clave, valor)
        except Exception as e:
            print(f"Error al guardar datos: {e}")
            return False

    def obtener(self, clave):
        """Obtiene el valor de una clave."""
        if not self.client:
            print("No hay conexión con Redis.")
            return None
        try:
            return self.client.get(clave)
        except Exception as e:
            print(f"Error al obtener datos: {e}")
            return None

    def encolar_dato(self, nombre_cola, dato):
        """Añade un dato al final de una lista (útil para telemetría IoT)."""
        if not self.client:
            print("No hay conexión con Redis.")
            return False
        try:
            return self.client.rpush(nombre_cola, dato)
        except Exception as e:
            print(f"Error al encolar: {e}")
            return False
        
    def existe_clave(self, clave):
        """Verifica si una clave existe en Redis."""
        if not self.client:
            print("No hay conexión con Redis.")
            return False
        try:
            return self.client.exists(clave) == 1
        except Exception as e:
            print(f"Error al verificar clave: {e}")
            return False
if __name__ == "__main__":
    redis_client = RedisClient()
    if redis_client.client:
        print("Prueba de conexión exitosa.")
    else:
        print("No se pudo establecer conexión con Redis.")