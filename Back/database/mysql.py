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