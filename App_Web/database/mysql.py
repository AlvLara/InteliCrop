import os
from contextlib import contextmanager

from dotenv import load_dotenv
from mysql.connector import pooling
from mysql.connector import Error, IntegrityError

load_dotenv()


connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER_ROOT"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
    autocommit=True,
)


def _get_conn():
    return connection_pool.get_connection()


def _put_conn(conn):
    conn.close()


@contextmanager
def get_cursor(dictionary=False):
    conn = _get_conn()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
    finally:
        if cursor is not None:
            cursor.close()

        _put_conn(conn)


# =====================================================
# USUARIOS
# =====================================================

def obtener_usuario_por_email(email):
    try:
        sql = """
            SELECT user_uuid, nombre, email, password_hash
            FROM usuario
            WHERE email = %s
        """

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (email,))
            usuario = cursor.fetchone()

        return usuario

    except Error as e:
        print(f"Error en obtener_usuario_por_email: {e}")
        return None

    except Exception as e:
        print(f"Error inesperado en obtener_usuario_por_email: {e}")
        return None


def registrar_usuario(nombre, email, password_hash):
    try:
        sql = """
            INSERT INTO usuario (nombre, email, password_hash)
            VALUES (%s, %s, %s)
        """

        with get_cursor() as cursor:
            cursor.execute(sql, (nombre, email, password_hash))

        return True

    except IntegrityError as e:
        print(f"Error: el email ya existe {e}")
        return False

    except Error as e:
        print(f"Error en registrar_usuario: {e}")
        return False

    except Exception as e:
        print(f"Error inesperado en registrar_usuario: {e}")
        return False


def obtener_uuid_usuario_por_email(email):
    try:
        sql = """
            SELECT user_uuid
            FROM usuario
            WHERE email = %s
        """

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (email,))
            result = cursor.fetchone()

        if result is None:
            return None

        return result["user_uuid"]

    except Error as e:
        print(f"Error en obtener_uuid_usuario_por_email: {e}")
        return None

    except Exception as e:
        print(f"Error inesperado en obtener_uuid_usuario_por_email: {e}")
        return None


# =====================================================
# CULTIVOS / PLANTAS
# =====================================================

def obtener_cultivos_por_usuario(user_uuid):
    try:
        sql = """
            SELECT 
                uuid_cultivo,
                nombre,
                estado_del_cultivo,
                fecha_creacion
            FROM cultivo
            WHERE user_uuid = %s
            ORDER BY fecha_creacion DESC
        """

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (user_uuid,))
            cultivos = cursor.fetchall()

        return cultivos

    except Error as e:
        print(f"Error en obtener_cultivos_por_usuario: {e}")
        return []

    except Exception as e:
        print(f"Error inesperado en obtener_cultivos_por_usuario: {e}")
        return []


def registrar_planta(nombre, api_key_hash,secreto_cifrado, user_uuid):
    try:
        sql = """
            INSERT INTO cultivo (
                nombre,
                secreto_cifrado,
                api_key_hash,
                user_uuid
            )
            VALUES (%s, %s, %s, %s)
        """

        with get_cursor() as cursor:
            cursor.execute(sql, (
                nombre,
                secreto_cifrado,
                api_key_hash,
                user_uuid
            ))

        return True

    except IntegrityError as e:
        print(f"Error de integridad en registrar_planta: {e}")
        return False

    except Error as e:
        print(f"Error en registrar_planta: {e}")
        return False

    except Exception as e:
        print(f"Error inesperado en registrar_planta: {e}")
        return False


def obtener_cultivo_por_api_key_hash(api_key_hash):
    try:
        sql = """
            SELECT 
                uuid_cultivo,
                user_uuid,
                nombre,
                secreto_cifrado
            FROM cultivo
            WHERE api_key_hash = %s
              AND estado_del_cultivo = 'activo'
        """

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (api_key_hash,))
            cultivo = cursor.fetchone()

        return cultivo

    except Error as e:
        print(f"Error en obtener_cultivo_por_api_key_hash: {e}")
        return None

    except Exception as e:
        print(f"Error inesperado en obtener_cultivo_por_api_key_hash: {e}")
        return None
def obtener_cultivo_por_uuid_cultivo(uuid_cultivo):
    try:
        sql = """
            SELECT 
                uuid_cultivo,
                user_uuid,
                nombre,
                secreto_cifrado,
                estado_del_cultivo
            FROM cultivo
            WHERE uuid_cultivo = %s
              AND estado_del_cultivo = 'activo'
        """

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (uuid_cultivo,))
            cultivo = cursor.fetchone()

        return cultivo

    except Error as e:
        print(f"Error en obtener_cultivo_por_uuid: {e}")
        return None

    except Exception as e:
        print(f"Error inesperado en obtener_cultivo_por_uuid: {e}")
        return None

def eliminar_cultivo(uuid_cultivo, user_uuid):
    try:
        sql = """
            DELETE FROM cultivo
            WHERE uuid_cultivo = %s
              AND user_uuid = %s
        """

        with get_cursor() as cursor:
            cursor.execute(sql, (uuid_cultivo, user_uuid))

        return True

    except Error as e:
        print(f"Error en eliminar_cultivo: {e}")
        return False

    except Exception as e:
        print(f"Error inesperado en eliminar_cultivo: {e}")
        return False
    
def obtener_cultivo_por_uuid_persona_uuid_cultivo(user_uuid,uuid_cultivo):
    try:
        sql = """
            SELECT 
                uuid_cultivo,
                user_uuid,
                nombre,
                secreto_cifrado,
                estado_del_cultivo
            FROM cultivo
            WHERE uuid_cultivo = %s
              AND estado_del_cultivo = 'activo' and user_uuid = %s
        """

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (uuid_cultivo,user_uuid))
            cultivo = cursor.fetchone()

        return cultivo

    except Error as e:
        print(f"Error en obtener_cultivo_por_uuid: {e}")
        return None

    except Exception as e:
        print(f"Error inesperado en obtener_cultivo_por_uuid: {e}")
        return None
    
def obtener_umbrales_por_cultivo(uuid_cultivo):
    """Obtiene los límites configurados y los devuelve en un diccionario mapeado por tipo de sensor."""
    try:
        sql = """
            SELECT tipo_sensor, min_valor, max_valor
            FROM conf_umbrales
            WHERE uuid_cultivo = %s
        """
        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (uuid_cultivo,))
            filas = cursor.fetchall()
            
        umbrales = {}
        for fila in filas:
            umbrales[fila['tipo_sensor']] = {
                'min': fila['min_valor'],
                'max': fila['max_valor']
            }
        return umbrales
        
    except Error as e:
        print(f"Error en obtener_umbrales_por_cultivo: {e}")
        return {}

def registrar_umbrales(uuid_cultivo, datos_sensores):
    """Inserta o actualiza múltiples tipos de sensores para un cultivo."""
    try:
        with get_cursor(dictionary=True) as cursor:
            for sensor in datos_sensores:
                tipo = sensor['tipo']
                val_min = sensor['min']
                val_max = sensor['max']
                
                cursor.execute("""
                    SELECT uuid_conf FROM conf_umbrales 
                    WHERE uuid_cultivo = %s AND tipo_sensor = %s
                """, (uuid_cultivo, tipo))
                
                existe = cursor.fetchone()
                
                if existe:
                    
                    cursor.execute("""
                        UPDATE conf_umbrales 
                        SET min_valor = %s, max_valor = %s 
                        WHERE uuid_conf = %s
                    """, (val_min, val_max, existe['uuid_conf']))
                else:

                    cursor.execute("""
                        INSERT INTO conf_umbrales (uuid_cultivo, tipo_sensor, min_valor, max_valor)
                        VALUES (%s, %s, %s, %s)
                    """, (uuid_cultivo, tipo, val_min, val_max))
        return True

    except Error as e:
        print(f"Error en registrar_umbrales: {e}")
        return False
    
def verificar_alerta_agua(cultivo_uuid):
    try:
        sql = """
            SELECT uuid_alerta FROM alertas
            WHERE uuid_cultivo = %s and agua=1
            limit 1
        """
        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (cultivo_uuid,))
            alerta = cursor.fetchone()
        return alerta
    except Error as e:
        print(f"Error en verificar_alerta_agua: {e}")
        return None
    
def marcar_alerta_agua_como_enviada(uuid_alerta):
    try:
        sql = """
            UPDATE alertas
            SET agua = 0
            WHERE uuid_alerta = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (uuid_alerta,))
        return True
    except Error as e:
        print(f"Error en marcar_alerta_agua_como_enviada: {e}")
        return False
    
def registrar_activacion_manual_bomba(uuid_cultivo, timenow):
    try:
        sql = """
            INSERT INTO alertas (
                uuid_cultivo,
                tipo_alerta,
                mensaje,
                leida,
                agua,
                momento_alerta
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        valores = (
            uuid_cultivo,
            "BOMBA_MANUAL",
            "La bomba de agua ha sido activada manualmente.",
            0,
            1,
            timenow
        )

        with get_cursor() as cursor:
            cursor.execute(sql, valores)
            print(f"Momento insertado: {timenow}")
            print(f"Filas insertadas en alertas: {cursor.rowcount}")

        return True

    except Error as e:
        print(f"Error en registrar_activacion_manual_bomba: {e}")
        return False

    except Exception as e:
        print(f"Error inesperado en registrar_activacion_manual_bomba: {e}")
        return False

def obtener_alertas_por_cultivo(uuid_cultivo):
    try:
        sql = """
            SELECT uuid_alerta, uuid_cultivo, mensaje, tipo_alerta, agua, momento_alerta
            FROM alertas
            WHERE uuid_cultivo = %s
            ORDER BY momento_alerta DESC
        """
        with get_cursor(dictionary=True) as cursor:
            cursor.execute(sql, (uuid_cultivo,))
            alertas = cursor.fetchall()
        return alertas
    except Error as e:
        print(f"Error en obtener_alertas_por_cultivo: {e}")
        return []

def actualizar_nombre_cultivo(uuid_cultivo, nuevo_nombre, user_uuid):
    try:
        sql = """
            UPDATE cultivo 
            SET nombre = %s 
            WHERE uuid_cultivo = %s AND user_uuid = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (nuevo_nombre, uuid_cultivo, user_uuid))
            
            # Comprobamos si se actualizó alguna fila
            if cursor.rowcount > 0:
                return True
            return False

    except Error as e:
        print(f"Error en actualizar_nombre_cultivo: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado en actualizar_nombre_cultivo: {e}")
        return False