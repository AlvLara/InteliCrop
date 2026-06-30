#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include "secrets.h"
#include <mbedtls/md.h>
#include <time.h>

// =====================================================
// 1. Configuración de Hardware
// =====================================================

LiquidCrystal_I2C lcd(0x27, 16, 2);

// Sensor humedad suelo
const int sensorPin = A0;
const int valorSeco = 1500;
const int valorHumedo = 3500;

// Sensor lluvia
const int pinLluviaDigital = 2;
const int pinLluviaAnalogico = A1;

// Sensor DHT
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Relé / bomba
const int PIN_RELE = 12;

// =====================================================
// 2. Credenciales WiFi
// =====================================================

const char* WIFI_SSID = WIFI_SSID_SECRET;
const char* WIFI_PASSWORD = WIFI_PASSWORD_SECRET;

// =====================================================
// 3. Configuración API HTTP y Seguridad
// =====================================================

const char* API_URL = API_URL_SECRET;
const char* API_URL_AGUA = API_URL_AGUA_SECRET;

const char* API_KEY = API_KEY_SECRET;
const char* HMAC_SECRET = HMAC_SECRET_KEY;

// NTP España
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 3600;
const int daylightOffset_sec = 3600;

// =====================================================
// 4. Clientes WiFi / HTTP
// =====================================================

WiFiClient wifiClient;
WiFiClientSecure secureClient;

// =====================================================
// 5. Variables de sensores
// =====================================================

int porcentajeHumedadSuelo = 0;
bool estaLloviendo = false;
int intensidadLluvia = 0;

float temperaturaAire = 0.0;
float humedadAire = 0.0;

// Guarda si alguna vez el DHT ha leído bien
bool dhtTieneLecturaValida = false;

// =====================================================
// 6. Temporizadores
// =====================================================

// LCD cada 5 segundos
unsigned long tiempoAnteriorLCD = 0;
const unsigned long intervaloLCD = 5000UL;

// Envío HTTP cada 10 segundos
unsigned long tiempoAnteriorPublicacion = 0;
const unsigned long intervaloPublicacion = 10000UL;

// Consulta al servidor cada 30 segundos
unsigned long tiempoAnteriorConsultaAgua = 0;
const unsigned long intervaloConsultaAgua = 30000UL;

// Duración de la bomba encendida
const unsigned long duracionRiegoMs = 5000UL;

// Estado bomba
bool bombaActiva = false;
unsigned long tiempoInicioBomba = 0;

// =====================================================
// 7. Control de bomba / relé
// =====================================================

void apagarBomba() {
  pinMode(PIN_RELE, INPUT);
  bombaActiva = false;

  Serial.println("Bomba apagada");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("BOMBA APAGADA");
}

void encenderBomba() {
  pinMode(PIN_RELE, OUTPUT);
  digitalWrite(PIN_RELE, LOW);

  bombaActiva = true;
  tiempoInicioBomba = millis();

  Serial.println("Bomba encendida");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("BOMBA ACTIVA");
  lcd.setCursor(0, 1);
  lcd.print("Regando cultivo");
}

void activarBombaDuranteRiego() {
  if (bombaActiva) {
    Serial.println("La bomba ya esta activa");
    return;
  }

  encenderBomba();
}

void gestionarBomba() {
  if (!bombaActiva) {
    return;
  }

  unsigned long ahora = millis();

  if (ahora - tiempoInicioBomba >= duracionRiegoMs) {
    apagarBomba();
  }
}

// =====================================================
// 8. Conectar WiFi
// =====================================================

void conectarWiFi() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Conectando WiFi");

  Serial.print("Conectando a WiFi");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi conectado");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi conectado");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP());

  delay(1500);
}

// =====================================================
// 9. Leer DHT sin mostrar errores puntuales
// =====================================================

void leerDHTSilencioso() {
  float t = NAN;
  float h = NAN;

  for (int intento = 0; intento < 3; intento++) {
    t = dht.readTemperature();
    h = dht.readHumidity();

    if (!isnan(t) && !isnan(h)) {
      temperaturaAire = t;
      humedadAire = h;
      dhtTieneLecturaValida = true;
      return;
    }

    delay(700);
  }

  // Si falla, no mostramos error.
  // Se mantiene el último valor válido de temperaturaAire y humedadAire.
}

// =====================================================
// 10. Leer sensores
// =====================================================

void leerSensores() {
  // Humedad suelo
  int lecturaCruda = analogRead(sensorPin);

  porcentajeHumedadSuelo = map(
    lecturaCruda,
    valorSeco,
    valorHumedo,
    0,
    100
  );

  porcentajeHumedadSuelo = constrain(porcentajeHumedadSuelo, 0, 100);

  // Lluvia
  estaLloviendo = digitalRead(pinLluviaDigital) == LOW;

  int lecturaLluviaCruda = analogRead(pinLluviaAnalogico);

  intensidadLluvia = map(
    lecturaLluviaCruda,
    4095,
    0,
    0,
    100
  );

  intensidadLluvia = constrain(intensidadLluvia, 0, 100);

  // DHT con reintentos silenciosos
  leerDHTSilencioso();
}

// =====================================================
// 11. Obtener fecha y hora formateada
// =====================================================

String obtenerTimeNow() {
  struct tm timeinfo;

  if (!getLocalTime(&timeinfo)) {
    Serial.println("Error al obtener la hora");
    return "N/A";
  }

  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo);

  return String(buffer);
}

// =====================================================
// 12. Generar HMAC SHA-256
// =====================================================

String generarHMAC(const char* payload, const char* secret) {
  byte hmacResult[32];

  mbedtls_md_context_t ctx;
  mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;

  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 1);
  mbedtls_md_hmac_starts(&ctx, (const unsigned char*)secret, strlen(secret));
  mbedtls_md_hmac_update(&ctx, (const unsigned char*)payload, strlen(payload));
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  String hashHex = "";

  for (int i = 0; i < 32; i++) {
    char str[3];
    sprintf(str, "%02x", (int)hmacResult[i]);
    hashHex += str;
  }

  return hashHex;
}

// =====================================================
// 13. Enviar datos por HTTP POST
// =====================================================

void enviarLecturaHTTP() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("No se envia: WiFi no conectado");
    return;
  }

  // Si todavía no tenemos ninguna lectura válida del DHT,
  // intentamos una vez más antes de enviar.
  if (!dhtTieneLecturaValida) {
    leerDHTSilencioso();
  }

  StaticJsonDocument<512> docDatos;
  docDatos["temperatura"] = temperaturaAire;
  docDatos["humedad"] = humedadAire;
  docDatos["lluvia"] = intensidadLluvia;
  docDatos["humedad_suelo"] = porcentajeHumedadSuelo;
  docDatos["esta_lloviendo"] = estaLloviendo;
  docDatos["ts"] = millis();
  docDatos["time_envio"] = obtenerTimeNow();

  char datosString[512];
  size_t datosSize = serializeJson(docDatos, datosString, sizeof(datosString));

  if (datosSize == 0) {
    Serial.println("Error serializando datos");
    return;
  }

  Serial.print("Datos sin firmar: ");
  Serial.println(datosString);

  String firma = generarHMAC(datosString, HMAC_SECRET);

  StaticJsonDocument<768> docFinal;
  docFinal["payload"] = docDatos;
  docFinal["hmac"] = firma;

  char paqueteFinal[768];
  size_t payloadSize = serializeJson(docFinal, paqueteFinal, sizeof(paqueteFinal));

  if (payloadSize == 0) {
    Serial.println("Error serializando paquete final");
    return;
  }

  Serial.print("JSON final a enviar: ");
  Serial.println(paqueteFinal);

  HTTPClient http;

  String url = String(API_URL);
  bool iniciado = false;

  if (url.startsWith("https://")) {
    secureClient.setInsecure();
    iniciado = http.begin(secureClient, API_URL);
  } else {
    iniciado = http.begin(wifiClient, API_URL);
  }

  if (!iniciado) {
    Serial.println("Error iniciando HTTPClient");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  http.addHeader("x-api-key", API_KEY);

  int httpCode = http.POST((uint8_t*)paqueteFinal, payloadSize);

  if (httpCode > 0) {
    Serial.print("POST enviado. HTTP code=");
    Serial.println(httpCode);

    String respuesta = http.getString();
    Serial.print("Respuesta servidor: ");
    Serial.println(respuesta);
  } else {
    Serial.print("Error en POST: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
}

// =====================================================
// 14. Consultar si necesita agua
// =====================================================

bool consultarNecesitaAguaHTTP(bool &necesitaAgua) {
  necesitaAgua = false;

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("No se consulta agua: WiFi no conectado");
    return false;
  }

  HTTPClient http;

  String url = String(API_URL_AGUA);
  bool iniciado = false;

  if (url.startsWith("https://")) {
    secureClient.setInsecure();
    iniciado = http.begin(secureClient, API_URL_AGUA);
  } else {
    iniciado = http.begin(wifiClient, API_URL_AGUA);
  }

  if (!iniciado) {
    Serial.println("Error iniciando HTTPClient para /necesito_agua");
    return false;
  }

  http.addHeader("Accept", "application/json");
  http.addHeader("x-api-key", API_KEY);

  int httpCode = http.GET();

  if (httpCode <= 0) {
    Serial.print("Error en GET /necesito_agua: ");
    Serial.println(http.errorToString(httpCode));
    http.end();
    return false;
  }

  Serial.print("GET /necesito_agua HTTP code=");
  Serial.println(httpCode);

  String respuesta = http.getString();

  Serial.print("Respuesta agua: ");
  Serial.println(respuesta);

  http.end();

  if (httpCode != 200) {
    Serial.println("El servidor no devolvio 200");
    return false;
  }

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, respuesta);

  if (error) {
    Serial.print("Error parseando JSON de agua: ");
    Serial.println(error.c_str());
    return false;
  }

  bool ok = doc["ok"] | false;

  if (!ok) {
    Serial.println("Respuesta ok=false en /necesito_agua");
    return false;
  }

  necesitaAgua = doc["necesita_agua"] | false;

  return true;
}

void comprobarAguaYRegarSiHaceFalta() {
  if (bombaActiva) {
    Serial.println("No se consulta agua porque la bomba ya esta activa");
    return;
  }

  bool necesitaAgua = false;
  bool consultaCorrecta = consultarNecesitaAguaHTTP(necesitaAgua);

  if (!consultaCorrecta) {
    Serial.println("No se pudo comprobar si necesita agua");

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Error consulta");
    lcd.setCursor(0, 1);
    lcd.print("agua servidor");

    return;
  }

  if (necesitaAgua) {
    Serial.println("El servidor indica que el cultivo necesita agua");

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Necesita agua");
    lcd.setCursor(0, 1);
    lcd.print("Activando bomba");

    delay(700);

    activarBombaDuranteRiego();
  } else {
    Serial.println("El cultivo no necesita agua");

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Agua OK");
    lcd.setCursor(0, 1);
    lcd.print("No regar");
  }
}

// =====================================================
// 15. Actualizar LCD
// =====================================================

void actualizarLCD() {
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("T:");
  // Evitar imprimir NAN en el LCD
  if (isnan(temperaturaAire)) {
    lcd.print("--");
  } else {
    lcd.print(temperaturaAire, 1);
  }
  lcd.print("C H:");
  
  if (isnan(humedadAire)) {
    lcd.print("--");
  } else {
    lcd.print(humedadAire, 0);
  }
  lcd.print("%");

  lcd.setCursor(0, 1);
  lcd.print("S:");
  lcd.print(porcentajeHumedadSuelo);
  lcd.print("% L:");
  lcd.print(intensidadLluvia);
  lcd.print("%");
}

// =====================================================
// 16. Setup
// =====================================================

void setup() {
  Serial.begin(115200);

  pinMode(pinLluviaDigital, INPUT);

  // Relé apagado desde el inicio.
  // Usamos INPUT para simular desconexión total del relé.
  pinMode(PIN_RELE, INPUT);

  dht.begin();

  // Pequeña espera para que el DHT se estabilice al arrancar.
  delay(2500);

  lcd.init();
  lcd.backlight();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sistema listo");
  lcd.setCursor(0, 1);
  lcd.print("Iniciando...");
  delay(1200);

  // Primera lectura silenciosa del DHT.
  leerDHTSilencioso();

  conectarWiFi();

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.println("Sincronizando hora con servidor NTP...");

  unsigned long ahora = millis();

  tiempoAnteriorLCD = ahora;
  tiempoAnteriorPublicacion = ahora;

  // Consulta nada más arrancar.
  // Luego seguirá consultando cada 30 segundos.
  tiempoAnteriorConsultaAgua = ahora - intervaloConsultaAgua;

  lcd.clear();

  Serial.println("Sistema iniciado");
  Serial.println("LCD cada 5 segundos");
  Serial.println("POST HTTP cada 10 segundos");
  Serial.println("GET /necesito_agua cada 30 segundos");
}

// =====================================================
// 17. Loop principal
// =====================================================

void loop() {
  unsigned long ahora = millis();

  // 1. Gestionar apagado automatico de la bomba
  gestionarBomba();

  // 2. Revisar WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado. Reconectando...");

    apagarBomba();
    conectarWiFi();

    ahora = millis();

    tiempoAnteriorLCD = ahora;
    tiempoAnteriorPublicacion = ahora;
    tiempoAnteriorConsultaAgua = ahora;

    return;
  }

  // 3. Temporizadores independientes
  bool tocaLCD = ahora - tiempoAnteriorLCD >= intervaloLCD;
  bool tocaPublicar = ahora - tiempoAnteriorPublicacion >= intervaloPublicacion;
  bool tocaConsultarAgua = ahora - tiempoAnteriorConsultaAgua >= intervaloConsultaAgua;

  // 4. Leer sensores cuando haga falta
  if (tocaLCD || tocaPublicar) {
    leerSensores();
  }

  // 5. LCD cada 5 segundos
  // Si la bomba esta activa, no pisamos el mensaje "BOMBA ACTIVA"
  if (tocaLCD && !bombaActiva) {
    tiempoAnteriorLCD = ahora;
    actualizarLCD();

    Serial.println("LCD actualizada");
  }

  // 6. POST HTTP cada 10 segundos
  if (tocaPublicar) {
    tiempoAnteriorPublicacion = ahora;
    enviarLecturaHTTP();

    Serial.println("Payload enviado por HTTP");
  }

  // 7. GET cada 30 segundos para saber si necesita agua
  if (tocaConsultarAgua) {
    tiempoAnteriorConsultaAgua = ahora;
    comprobarAguaYRegarSiHaceFalta();
  }

  delay(10);
}