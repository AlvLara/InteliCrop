from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import database.mysql as db
import database.mongo as mongo
import secrets
import hashlib
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import json
import pika
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo
from datetime import datetime
import re


from uuid import UUID

import auxiliares.auxiliares as auxiliares

load_dotenv()

app = Flask(__name__)

app.secret_key = 'clave_secreta_para_desarrollo_iot'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
csrf = CSRFProtect(app)

FERNET_KEY = os.getenv("FERNET_KEY")
fernet = Fernet(FERNET_KEY)

if not FERNET_KEY:
    raise RuntimeError("Falta FERNET_KEY en el archivo .env")


# =====================================================
# FUNCIONES AUXILIARES DE FLASK
# =====================================================

def email_valido(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not email:
        return False

    email = email.strip()

    if len(email) > 254:
        return False

    if not re.match(patron, email):
        return False

    usuario, dominio = email.split('@')

    if len(usuario) > 64:
        return False

    if '..' in email:
        return False

    if dominio.startswith('.') or dominio.endswith('.'):
        return False

    if dominio.startswith('-') or dominio.endswith('-'):
        return False

    return True

def obtener_campo_form(nombre_campo):
    return request.form.get(nombre_campo, "").strip()


def usuario_no_logueado():
    return 'user_uuid' not in session


@app.after_request
def set_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; " 
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://cdn.jsdelivr.net; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

# =====================================================
# RUTAS
# =====================================================

@app.route('/', methods=['GET'])
def inicio():
    if 'user_uuid' in session:
        return redirect(url_for('plantas'))

    return render_template('index.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'GET':
        return render_template('registro.html')

    nombre = obtener_campo_form('nombre')
    email = obtener_campo_form('email')
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not nombre:
        return render_template(
            'registro.html',
            email=email,
            nombre=nombre,
            error="El nombre es obligatorio."
        )

    if not email:
        return render_template(
            'registro.html',
            email=email,
            nombre=nombre,
            error="El email es obligatorio."
        )

    email = email.strip().lower()

    if not email_valido(email):
        return render_template(
            'registro.html',
            email=email,
            nombre=nombre,
            error="Introduce un correo electrónico válido."
        )

    if not password:
        return render_template(
            'registro.html',
            email=email,
            nombre=nombre,
            error="La contraseña es obligatoria."
        )

    if password != confirm_password:
        return render_template(
            'registro.html',
            email=email,
            nombre=nombre,
            error="Las contraseñas no coinciden."
        )

    password_hash = generate_password_hash(password)

    resultado = db.registrar_usuario(nombre, email, password_hash)

    if resultado is not True:
        return render_template(
            'registro.html',
            email=email,
            nombre=nombre,
            error="Error en el registro. Puede que el email ya exista."
        )

    usuario = db.obtener_usuario_por_email(email)

    if usuario is None:
        return render_template(
            'login.html',
            error="Usuario registrado, pero no se pudo iniciar sesión automáticamente."
        )

    session['user_uuid'] = usuario['user_uuid']
    session['nombre'] = usuario['nombre']

    return redirect(url_for('plantas'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = obtener_campo_form('email')
    password = request.form.get('password', '')

    if not email:
        return render_template(
            'login.html',
            email=email,
            error="El email es obligatorio."
        )

    if not password:
        return render_template(
            'login.html',
            email=email,
            error="La contraseña es obligatoria."
        )

    usuario = db.obtener_usuario_por_email(email)

    if usuario is None:
        return render_template(
            'login.html',
            email=email,
            error="Correo electrónico o contraseña incorrectos."
        )

    if not check_password_hash(usuario["password_hash"], password):
        return render_template(
            'login.html',
            email=email,
            error="Correo electrónico o contraseña incorrectos."
        )

    session['user_uuid'] = usuario['user_uuid']
    session['nombre'] = usuario['nombre']
    session.permanent = True

    return redirect(url_for('plantas'))


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if usuario_no_logueado():
        return redirect(url_for('login'))

    return render_template(
        'dashboard.html',
        nombre_usuario=session['nombre']
    )


@app.route('/plantas', methods=['GET'])
def plantas():
    if usuario_no_logueado():
        return redirect(url_for('login'))

    lista_plantas = db.obtener_cultivos_por_usuario(session['user_uuid'])

    return render_template(
        'plantas.html',
        lista_plantas=lista_plantas,
        nombre_usuario=session['nombre']
    )


@app.route('/registro_planta', methods=['GET', 'POST'])
def registro_planta():
    if usuario_no_logueado():
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template(
            'registro_planta.html'
        )

    nombre = obtener_campo_form('nombre')

    if not nombre:
        return render_template(
            'registro_planta.html',
            error="El nombre de la planta no puede estar vacío."

        )
    secreto_sin_cifrado= obtener_campo_form('secreto_cifrado')
    if not secreto_sin_cifrado:
        return render_template(
            'registro_planta.html',
            error="El secreto cifrado no puede estar vacío."

        )
    if len(secreto_sin_cifrado) < 8 or len(secreto_sin_cifrado) > 25:
        return render_template(
            'registro_planta.html',
            error="El secreto cifrado debe tener al menos 8 caracteres y maximo de 25."

        )
    secreto_cifrado=auxiliares.cifrar_texto(secreto_sin_cifrado,fernet)

    user_uuid = session['user_uuid']

    # API key real. Esta es la que verá el usuario y meterá en el ESP32.
    api_key = secrets.token_hex(16)

    # En BD guardamos solo el hash.
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    resultado = db.registrar_planta(
        nombre=nombre,
        secreto_cifrado=secreto_cifrado,
        api_key_hash=api_key_hash,
        user_uuid=user_uuid
    )

    if resultado is not True:
        return render_template(
            'registro_planta.html',
            error="Error al registrar la planta.",
        )

    return render_template(
        'planta_creada.html',
        nombre_planta=nombre,
        api_key=api_key,
        secreto_sin_cifrado=secreto_sin_cifrado
    )


@app.route('/datos_sensor', methods=['POST'])
@csrf.exempt
def datos_sensor():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "ok": False,
            "error": "No se recibió JSON válido."
        }), 400

    api_key = request.headers.get('x-api-key', '').strip()

    if not api_key:
        return jsonify({
            "ok": False,
            "error": "Falta la API key."
        }), 401

    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    cultivo = db.obtener_cultivo_por_api_key_hash(api_key_hash)

    if cultivo is None:
        return jsonify({
            "ok": False,
            "error": "API key inválida."
        }), 403

    payload = data.get("payload")
    hmac_recibido = data.get("hmac")

    if payload is None:
        return jsonify({
            "ok": False,
            "error": "Falta payload."
        }), 400

    if hmac_recibido is None:
        return jsonify({
            "ok": False,
            "error": "Falta hmac."
        }), 400

    mensaje_rabbitmq = {
        "uuid_cultivo": cultivo["uuid_cultivo"],
        "payload": payload,
        "hmac": hmac_recibido
    }

    try:
        auxiliares.publicar_en_rabbitmq(mensaje_rabbitmq)

    except Exception as e:
        print(f"Error publicando en RabbitMQ: {e}")

        return jsonify({
            "ok": False,
            "error": "API key correcta, pero no se pudo publicar en RabbitMQ."
        }), 500

    print("Cultivo autenticado:")
    print(cultivo)

    print("Mensaje enviado a RabbitMQ:")
    print(mensaje_rabbitmq)

    return jsonify({
        "ok": True,
        "mensaje": "Mensaje recibido y encolado correctamente.",
        "uuid_cultivo": cultivo["uuid_cultivo"]
    }), 202

@app.route('/eliminar_planta/<uuid_cultivo>', methods=['POST'])
def eliminar_planta(uuid_cultivo):
    if 'user_uuid' not in session:
        return redirect(url_for('login'))

    resultado = db.eliminar_cultivo(
        uuid_cultivo=uuid_cultivo,
        user_uuid=session['user_uuid']
    )

    if resultado is True:
        return redirect(url_for('plantas'))

    return redirect(url_for('plantas'))

from bson import ObjectId


@app.route('/cultivo_last_data/<uuid_cultivo>', methods=['GET'])
def cultivo_last_data(uuid_cultivo):
    
    if 'user_uuid' not in session:
        return jsonify({
            "ok": False, 
            "error": "Sesión expirada o usuario no autenticado."
        }), 401

    user_uuid = session['user_uuid']
    print(f"Obteniendo datos para cultivo UUID: {uuid_cultivo} y usuario UUID: {user_uuid}")

    try:
        cultivo = db.obtener_cultivo_por_uuid_persona_uuid_cultivo(user_uuid, uuid_cultivo)
        
        if cultivo is None:
            return jsonify({
                "ok": False, 
                "error": "Cultivo no encontrado o no tienes permisos para verlo."
            }), 404

        last_data = mongo.obtener_ultima_lectura(uuid_cultivo)
        
        if last_data is None:
            return jsonify({
                "ok": False, 
                "error": "No se encontraron lecturas históricas para este cultivo en MongoDB."
            }), 404

        if "_id" in last_data:
            last_data["_id"] = str(last_data["_id"])
        
        if "created_at" in last_data and last_data["created_at"]:
            fecha = last_data["created_at"]

            # Mongo suele devolver datetime sin tzinfo, pero realmente está en UTC
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)

            fecha_espana = fecha.astimezone(ZoneInfo("Europe/Madrid"))

            last_data["created_at"] = fecha_espana.isoformat()

        return jsonify({
            "ok": True,
            "last_data": last_data
        }), 200

    except Exception as e:
        print(f"Error crítico en la ruta /cultivo_last_data: {e}")
        return jsonify({
            "ok": False, 
            "error": "Ocurrió un error interno en el servidor."
        }), 500




@app.route('/cultivo/<uuid_cultivo>', methods=['GET'])
def cultivo(uuid_cultivo):
    if 'user_uuid' not in session:
        return redirect(url_for('login'))

    cultivo = db.obtener_cultivo_por_uuid_persona_uuid_cultivo(session['user_uuid'], uuid_cultivo)

    if cultivo is None or cultivo['user_uuid'] != session['user_uuid']:
        return redirect(url_for('plantas'))

    umbrales = db.obtener_umbrales_por_cultivo(uuid_cultivo)

    return render_template(
        'cultivo.html',
        cultivo=cultivo,
        nombre_usuario=session['nombre'],
        umbrales=umbrales  
    )

@app.route('/cultivo/<uuid_cultivo>/editar_nombre', methods=['POST'])
def editar_nombre_cultivo(uuid_cultivo):
    if 'user_uuid' not in session:
        return redirect(url_for('login'))

    nuevo_nombre = obtener_campo_form('nuevo_nombre')

    if not nuevo_nombre:
        return redirect(url_for('cultivo', uuid_cultivo=uuid_cultivo))

    
    resultado = db.actualizar_nombre_cultivo(
        uuid_cultivo=uuid_cultivo,
        nuevo_nombre=nuevo_nombre,
        user_uuid=session['user_uuid']
    )

    if not resultado:
        print(f"No se pudo actualizar el nombre del cultivo {uuid_cultivo}")

    
    return redirect(url_for('cultivo', uuid_cultivo=uuid_cultivo))

@app.route('/cultivo_historico_data/<uuid_cultivo>', methods=['GET'])
def cultivo_historico_data(uuid_cultivo): 
    if 'user_uuid' not in session:
        return jsonify({"ok": False, "error": "Sesión expirada."}), 401

    user_uuid = session['user_uuid']
    try:
        cultivo = db.obtener_cultivo_por_uuid_persona_uuid_cultivo(user_uuid, uuid_cultivo)
        if cultivo is None:
            return jsonify({"ok": False, "error": "Cultivo no encontrado."}), 404

        historial_crudo = mongo.obtener_historial_semanal(uuid_cultivo)
        
        for registro in historial_crudo:
            if "_id" in registro:
                registro["_id"] = str(registro["_id"])
            if "created_at" in registro and registro["created_at"]:
                registro["created_at"] = registro["created_at"].isoformat()
        
        return jsonify({
            "ok": True,
            "historial": historial_crudo
        }), 200
    except Exception as e:
        print(f"Error crítico en /cultivo_historico_data: {e}")
        return jsonify({"ok": False, "error": "Error interno."}), 500

@app.route('/cultivo/historico/<uuid_cultivo>', methods=['GET'])
def cultivo_historico(uuid_cultivo): 
    if 'user_uuid' not in session:
        return redirect(url_for('login'))

    cultivo = db.obtener_cultivo_por_uuid_persona_uuid_cultivo(
        session['user_uuid'],
        uuid_cultivo
    )

    if cultivo is None or cultivo['user_uuid'] != session['user_uuid']:
        return redirect(url_for('plantas'))

    historial = mongo.obtener_historial_semanal(uuid_cultivo)

    zona_espana = ZoneInfo("Europe/Madrid")

    for lectura in historial:
        if "created_at" in lectura and lectura["created_at"]:
            fecha = lectura["created_at"]
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            fecha_espana = fecha.astimezone(zona_espana)
            lectura["created_at"] = fecha_espana

    return render_template(
        'historico.html',
        cultivo=cultivo,
        nombre_usuario=session['nombre'],
        historial=historial
    )

@app.route('/cultivo/umbrales/<uuid_cultivo>', methods=['GET', 'POST'])
def cultivo_umbrales(uuid_cultivo):
    if 'user_uuid' not in session:
        return redirect(url_for('login'))

    cultivo = db.obtener_cultivo_por_uuid_persona_uuid_cultivo(session['user_uuid'], uuid_cultivo)
    if cultivo is None:
        return redirect(url_for('plantas'))

    if request.method == 'GET':
        umbrales = db.obtener_umbrales_por_cultivo(uuid_cultivo)
        return render_template(
            'umbrales.html',
            cultivo=cultivo,
            nombre_usuario=session['nombre'],
            umbrales=umbrales
        )

    temp_min = request.form.get('temp_min', type=float)
    temp_max = request.form.get('temp_max', type=float)
    hum_min = request.form.get('hum_min', type=float)
    hum_max = request.form.get('hum_max', type=float)
    hum_suelo_min = request.form.get('hum_suelo_min', type=float)
    hum_suelo_max = request.form.get('hum_suelo_max', type=float)

    if None in [temp_min, temp_max, hum_min, hum_max, hum_suelo_min, hum_suelo_max]:
        umbrales_recuperados = db.obtener_umbrales_por_cultivo(uuid_cultivo)
        return render_template(
            'umbrales.html',
            cultivo=cultivo,
            nombre_usuario=session['nombre'],
            umbrales=umbrales_recuperados,
            error="Todos los campos son obligatorios y deben ser valores numéricos."
        )

    if temp_min >= temp_max or hum_min >= hum_max or hum_suelo_min >= hum_suelo_max:
        umbrales_recuperados = db.obtener_umbrales_por_cultivo(uuid_cultivo)
        return render_template(
            'umbrales.html',
            cultivo=cultivo,
            nombre_usuario=session['nombre'],
            umbrales=umbrales_recuperados,
            error="Configuración inválida: Los valores mínimos deben ser menores que los máximos."
        )

    datos_sensores = [
        {'tipo': 'temperatura', 'min': temp_min, 'max': temp_max},
        {'tipo': 'humedad', 'min': hum_min, 'max': hum_max},
        {'tipo': 'humedad_suelo', 'min': hum_suelo_min, 'max': hum_suelo_max}
    ]

    resultado = db.registrar_umbrales(uuid_cultivo, datos_sensores)

    if resultado is True:
        return redirect(url_for('cultivo', uuid_cultivo=uuid_cultivo))
    else:
        umbrales_recuperados = db.obtener_umbrales_por_cultivo(uuid_cultivo)
        return render_template(
            'umbrales.html',
            cultivo=cultivo,
            nombre_usuario=session['nombre'],
            umbrales=umbrales_recuperados,
            error="Ocurrió un error al intentar guardar los cambios en la base de datos."
        )



@app.route('/necesito_agua', methods=['GET'])
def necesito_agua():
    try:
        api_key = request.headers.get('x-api-key', '').strip()

        if not api_key:
            return jsonify({
                "ok": False,
                "necesita_agua": False,
                "accion": "mantener",
                "error": "Falta la API key."
            }), 401

        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        cultivo = db.obtener_cultivo_por_api_key_hash(api_key_hash)

        if cultivo is None:
            return jsonify({
                "ok": False,
                "necesita_agua": False,
                "accion": "mantener",
                "error": "API key inválida."
            }), 403

        cultivo_uuid = cultivo["uuid_cultivo"]
        print(f"API key válida para cultivo UUID: {cultivo_uuid}")

        alerta_agua = db.verificar_alerta_agua(cultivo_uuid)

        if alerta_agua is None:
            return jsonify({
                "ok": True,
                "necesita_agua": False,
                "accion": "mantener",
                "mensaje": "El cultivo no necesita agua."
            }), 200

        uuid_alerta_agua = alerta_agua["uuid_alerta"]

        alerta_marcada = db.marcar_alerta_agua_como_enviada(uuid_alerta_agua)

        return jsonify({
            "ok": True,
            "necesita_agua": True,
            "accion": "regar",
            "mensaje": "El cultivo necesita agua.",
            "alerta": alerta_agua,
            "alerta_marcada_como_enviada": alerta_marcada
        }), 200

    except Exception as e:
        print(f"Error en /necesito_agua: {e}")

        return jsonify({
            "ok": False,
            "necesita_agua": False,
            "accion": "mantener",
            "error": "Error interno del servidor."
        }), 500


@app.route("/activar_bomba_manualmente/<uuid_cultivo>", methods=['POST'])
def activar_bomba_manualmente(uuid_cultivo):
    if 'user_uuid' not in session:
        return redirect(url_for('login'))

    cultivo = db.obtener_cultivo_por_uuid_persona_uuid_cultivo(
        session['user_uuid'],
        uuid_cultivo
    )

    print(f"Intentando activar bomba manualmente para cultivo UUID: {uuid_cultivo}")
    print(f"Usuario en sesión: {session['user_uuid']}")
    print(f"Cultivo encontrado: {cultivo}")

    if cultivo is None or cultivo['user_uuid'] != session['user_uuid']:
        print("No se encontró el cultivo o no pertenece al usuario.")
        return redirect(url_for('plantas'))

    zona_espana = ZoneInfo("Europe/Madrid")
    tiempo_actual = datetime.now(zona_espana).replace(tzinfo=None)

    print(f"Hora española para activación manual: {tiempo_actual}")

    resultado = db.registrar_activacion_manual_bomba(
        uuid_cultivo,
        tiempo_actual
    )

    print(f"Resultado registrar_activacion_manual_bomba: {resultado}")

    return redirect(url_for('cultivo', uuid_cultivo=uuid_cultivo))
    
@app.route('/cultivo/alertas/<uuid_cultivo>', methods=['GET'])
def cultivo_alertas(uuid_cultivo):
    if 'user_uuid' not in session:
        return redirect(url_for('login'))

    cultivo = db.obtener_cultivo_por_uuid_persona_uuid_cultivo(session['user_uuid'], uuid_cultivo)
    if cultivo is None:
        return redirect(url_for('plantas'))

    alertas = db.obtener_alertas_por_cultivo(uuid_cultivo)

    zona_espana = ZoneInfo("Europe/Madrid")

    for alerta in alertas:
        if "momento_alerta" in alerta and alerta["momento_alerta"]:
            fecha = alerta["momento_alerta"]
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            fecha_espana = fecha.astimezone(zona_espana)
            alerta["momento_alerta"] = fecha_espana

    return render_template(
        'alertas.html',
        cultivo=cultivo,
        nombre_usuario=session['nombre'],
        alertas=alertas
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)