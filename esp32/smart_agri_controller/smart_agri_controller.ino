#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define DHTPIN 4
#define DHTTYPE DHT22
#define SOIL_PIN 34
#define RELAY_PIN 26

const char *WIFI_SSID = "Moto g57";
const char *WIFI_PASSWORD = "12345678";
const char *API_URL = "https://your-render-service.onrender.com/sensor-data";

const bool RELAY_ACTIVE_LOW = true;
const int DRY_ADC = 3200;
const int WET_ADC = 1200;
const unsigned long SEND_INTERVAL_MS = 30000;

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);

unsigned long lastSend = 0;

void setPump(bool on) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(RELAY_PIN, on ? LOW : HIGH);
  } else {
    digitalWrite(RELAY_PIN, on ? HIGH : LOW);
  }
}

int readSoilMoisturePercent() {
  int raw = analogRead(SOIL_PIN);
  int percent = map(raw, DRY_ADC, WET_ADC, 0, 100);
  return constrain(percent, 0, 100);
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi connected");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP());
  delay(1500);
}

bool sendSensorData(float temperature, float humidity, int soilMoisture, int nitrogen, int phosphorus, int potassium, bool pumpStatus) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  StaticJsonDocument<256> doc;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["soil_moisture"] = soilMoisture;
  doc["nitrogen"] = nitrogen;
  doc["phosphorus"] = phosphorus;
  doc["potassium"] = potassium;
  doc["pump_status"] = pumpStatus;

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");
  int status = http.POST(body);
  String response = http.getString();
  http.end();

  Serial.printf("POST status: %d\n", status);
  Serial.println(response);
  return status >= 200 && status < 300;
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  setPump(false);

  dht.begin();
  Wire.begin();
  lcd.init();
  lcd.backlight();
  randomSeed(esp_random());

  connectWiFi();
}

void loop() {
  if (millis() - lastSend < SEND_INTERVAL_MS) {
    delay(100);
    return;
  }
  lastSend = millis();

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int soilMoisture = readSoilMoisturePercent();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT22 read failed");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("DHT read failed");
    return;
  }

  int nitrogen = random(20, 81);
  int phosphorus = random(5, 46);
  int potassium = random(20, 101);
  bool pumpStatus = soilMoisture < 30;
  setPump(pumpStatus);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(temperature, 1);
  lcd.print(" H:");
  lcd.print(humidity, 0);
  lcd.print("%");
  lcd.setCursor(0, 1);
  lcd.print("S:");
  lcd.print(soilMoisture);
  lcd.print("% P:");
  lcd.print(pumpStatus ? "ON " : "OFF");

  Serial.println("Real values: temperature, humidity, soil moisture, pump status");
  Serial.println("Simulated NPK because NPK sensor is defective");
  Serial.printf("T %.1f C, H %.1f %%, Soil %d %%, N %d, P %d, K %d, Pump %s\n",
                temperature, humidity, soilMoisture, nitrogen, phosphorus, potassium,
                pumpStatus ? "ON" : "OFF");

  bool sent = sendSensorData(temperature, humidity, soilMoisture, nitrogen, phosphorus, potassium, pumpStatus);
  Serial.println(sent ? "Data sent successfully" : "Data send failed");
}
