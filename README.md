# InteliCrop
##  Manual de Despliegue y Configuración

Siga los pasos detallados a continuación para desplegar el entorno completo y poner en marcha el sistema.

### Paso 1: Instalación de Dependencias del Backend
Abra una terminal, diríjase a la carpeta del backend e instale las librerías necesarias ejecutando:


```pip install -r requirements.txt``` 

### Paso 2: Despliegue de la Infraestructura General (Docker)
Vuelva al directorio root del proyecto y levante los contenedores de la infraestructura. Docker se encargará automáticamente de descargar las imágenes de los registros oficiales y compilar las imágenes locales del proyecto:

```docker compose up -d --build```

### Paso 3: Ejecución de la Plataforma Web
Inicie el servidor web ejecutando el script principal. Una vez levantado, podrá acceder al entorno local interactivo:

```python app.py```

- Acceso Web: http://localhost:5000

### Paso 4: Registro de Usuario y Alta de Planta
Acceda a la plataforma web a través del puerto 5000 y regístrese como nuevo usuario.

Complete el formulario para añadir una nueva planta al sistema.

Al guardar la planta, el sistema generará dos credenciales críticas. Copie y guarde los siguientes valores:

HMAC SECRET KEY

API SECRET KEY

### Paso 5: Configuración y Flasheo del Dispositivo IoT (Arduino)
Localice el archivo Secrets.h dentro de la carpeta Arduino de este repositorio.

Abra el proyecto en su Arduino IDE e introduzca en Secrets.h las claves obtenidas en el paso anterior, así como los datos de su red local:

HMAC SECRET KEY

API SECRET KEY

Credenciales Wi-Fi: Introduzca el SSID y Contraseña del usuario

Conecte su placa Arduino y cargue el script modificado. Una vez finalizado, la placa comenzará a enviar los payloads de datos de los sensores de forma automática.

### Paso 6: Activación de los Workers de Procesamiento
Para conectar el flujo de datos proveniente de la placa con la base de datos del sistema, debe iniciar los dos workers encargados del procesamiento. Abra dos terminales dentro de la carpeta back y ejecute:

Worker de Protección de Datos:

```python proteccion_datos.py```

Worker de Almacenamiento (MongoDB):


```python mongo_writer.py```

Resultado: En este punto, los sensores recopilan información, los workers procesan y limpian la información, y los datos finales quedan almacenados de manera segura en la base de datos.

### Paso 7: Activación del Sistema de Alertas (WSO2 Siddhi)
Por último, configure el motor de eventos de Siddhi para la gestión de umbrales y alertas en tiempo real:

Asegúrese de que el servicio de WSO2 Siddhi está corriendo en el puerto 9390.

Abra su navegador web e ingrese al editor visual: http://localhost:9390/editor.

Localice y abra el script de Siddhi dentro de la interfaz del editor.

Ejecute el script desde la interfaz visual. El sistema empezará a guardar alertas en caso de cumplirse los requerimientos del sistema.
