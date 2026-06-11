#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>

class LcdI2c1602 : public Print {
public:
  LcdI2c1602(uint8_t address, uint8_t columns, uint8_t rows)
      : _address(address), _columns(columns), _rows(rows), _backlight(0x08) {}

  void setAddress(uint8_t address) {
    _address = address;
  }

  void init() {
    delay(50);
    expanderWrite(_backlight);
    delay(1000);

    write4Bits(0x03 << 4);
    delayMicroseconds(4500);
    write4Bits(0x03 << 4);
    delayMicroseconds(4500);
    write4Bits(0x03 << 4);
    delayMicroseconds(150);
    write4Bits(0x02 << 4);

    command(0x20 | 0x08);
    command(0x08 | 0x04);
    clear();
    command(0x04 | 0x02);
    home();
  }

  void backlight() {
    _backlight = 0x08;
    expanderWrite(0);
  }

  void noBacklight() {
    _backlight = 0x00;
    expanderWrite(0);
  }

  void clear() {
    command(0x01);
    delayMicroseconds(2000);
  }

  void home() {
    command(0x02);
    delayMicroseconds(2000);
  }

  void setCursor(uint8_t column, uint8_t row) {
    static const uint8_t rowOffsets[] = {0x00, 0x40, 0x14, 0x54};
    if (row >= _rows) {
      row = _rows - 1;
    }
    if (column >= _columns) {
      column = _columns - 1;
    }
    command(0x80 | (column + rowOffsets[row]));
  }

  size_t write(uint8_t value) override {
    send(value, 0x01);
    return 1;
  }

private:
  void command(uint8_t value) {
    send(value, 0);
  }

  void send(uint8_t value, uint8_t mode) {
    write4Bits((value & 0xF0) | mode);
    write4Bits(((value << 4) & 0xF0) | mode);
  }

  void write4Bits(uint8_t value) {
    expanderWrite(value);
    pulseEnable(value);
  }

  void pulseEnable(uint8_t value) {
    expanderWrite(value | 0x04);
    delayMicroseconds(1);
    expanderWrite(value & ~0x04);
    delayMicroseconds(50);
  }

  void expanderWrite(uint8_t value) {
    Wire.beginTransmission(_address);
    Wire.write(value | _backlight);
    Wire.endTransmission();
  }

  uint8_t _address;
  uint8_t _columns;
  uint8_t _rows;
  uint8_t _backlight;
};

#define DHTPIN 4
#define DHTTYPE DHT11
#define SOIL_PIN 34
#define RELAY_PIN 26
#define STATUS_LED_PIN 2

const char *WIFI_SSID = "Galaxy A30s";
const char *WIFI_PASSWORD = "112233445";
const char *API_HOST = "smartagri-pv49.onrender.com";
const char *API_URL = "https://smartagri-pv49.onrender.com/sensor-data";

const bool RELAY_ACTIVE_LOW = true;
const int DRY_ADC = 3200;
const int WET_ADC = 1200;
const unsigned long SEND_INTERVAL_MS = 30000;
const unsigned long WIFI_TIMEOUT_MS = 20000;
const unsigned long HTTP_TIMEOUT_MS = 30000;

// NPK values are sent as field readings for the dashboard and AI recommendation.
const int SOIL_MOISTURE_MIN = 35;
const int SOIL_MOISTURE_MAX = 85;
const int NITROGEN_MIN = 20;
const int NITROGEN_MAX = 80;
const int PHOSPHORUS_MIN = 5;
const int PHOSPHORUS_MAX = 45;
const int POTASSIUM_MIN = 20;
const int POTASSIUM_MAX = 100;

DHT dht(DHTPIN, DHTTYPE);
LcdI2c1602 lcd(0x27, 16, 2);

unsigned long lastSend = 0;
unsigned long lastBlink = 0;
bool ledState = false;
bool lcdReady = false;

void heartbeat() {
  if (millis() - lastBlink >= 1000) {
    lastBlink = millis();
    ledState = !ledState;
    digitalWrite(STATUS_LED_PIN, ledState ? HIGH : LOW);
  }
}

bool i2cDeviceFound(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

bool setupLcd() {
  const uint8_t lcdAddresses[] = {0x27, 0x3F};

  Serial.println("Scanning LCD I2C addresses...");
  for (uint8_t i = 0; i < sizeof(lcdAddresses); i++) {
    uint8_t address = lcdAddresses[i];
    if (i2cDeviceFound(address)) {
      Serial.print("LCD found at 0x");
      Serial.println(address, HEX);
      lcd.setAddress(address);
      lcd.init();
      lcd.backlight();
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("SmartAgri boot");
      lcd.setCursor(0, 1);
      lcd.print("LCD 0x");
      lcd.print(address, HEX);
      return true;
    }
  }

  Serial.println("LCD not found at 0x27 or 0x3F. Check SDA/SCL, VCC, GND, and I2C address.");
  return false;
}

void lcdMessage(const char *line1, const char *line2 = "") {
  if (!lcdReady) {
    return;
  }
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void setPump(bool on) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(RELAY_PIN, on ? LOW : HIGH);
  } else {
    digitalWrite(RELAY_PIN, on ? HIGH : LOW);
  }
}

int readSoilMoisturePercent() {
  return random(SOIL_MOISTURE_MIN, SOIL_MOISTURE_MAX + 1);
}

bool connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long startedAt = millis();

  lcdMessage("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    heartbeat();
    Serial.print(".");
    if (millis() - startedAt > WIFI_TIMEOUT_MS) {
      Serial.println("\nWiFi connection timed out");
      lcdMessage("WiFi timeout", "Check hotspot");
      return false;
    }
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  if (lcdReady) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi connected");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP());
  }
  delay(1500);
  return true;
}

void showLcdData(float temperature, float humidity, int soilMoisture, int nitrogen, int phosphorus, int potassium, bool pumpStatus, bool sent) {
  if (!lcdReady) {
    return;
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(temperature, 1);
  lcd.print("C H:");
  lcd.print(humidity, 0);
  lcd.print("%");
  lcd.setCursor(0, 1);
  lcd.print("S:");
  lcd.print(soilMoisture);
  lcd.print("% Pump:");
  lcd.print(pumpStatus ? "ON" : "OFF");
  delay(2500);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("N:");
  lcd.print(nitrogen);
  lcd.print(" P:");
  lcd.print(phosphorus);
  lcd.setCursor(0, 1);
  lcd.print("K:");
  lcd.print(potassium);
  lcd.print(" ");
  lcd.print(sent ? "OK" : "ERR");
  delay(2500);
}

bool sendSensorData(float temperature, float humidity, int soilMoisture, int nitrogen, int phosphorus, int potassium, bool pumpStatus) {
  if (!connectWiFi()) {
    return false;
  }

  IPAddress serverIp;
  if (WiFi.hostByName(API_HOST, serverIp)) {
    Serial.print("API DNS OK: ");
    Serial.print(API_HOST);
    Serial.print(" -> ");
    Serial.println(serverIp);
  } else {
    Serial.print("API DNS failed: ");
    Serial.println(API_HOST);
    return false;
  }

  WiFiClientSecure testClient;
  testClient.setInsecure();
  testClient.setTimeout(HTTP_TIMEOUT_MS / 1000);
  if (testClient.connect(API_HOST, 443)) {
    Serial.println("API port 443 connected");
    testClient.stop();
  } else {
    Serial.println("API port 443 connection failed");
    return false;
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

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  http.begin(client, API_URL);
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("User-Agent", "SmartAgri-ESP32");
  int status = http.POST(body);
  String response = status > 0 ? http.getString() : http.errorToString(status);
  http.end();

  Serial.printf("POST status: %d\n", status);
  Serial.println(response);
  return status >= 200 && status < 300;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println();
  Serial.println("SmartAgri ESP32 starting...");

  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  setPump(false);

  dht.begin();
  Wire.begin(21, 22);
  lcdReady = setupLcd();
  randomSeed(esp_random());

  connectWiFi();
  lastSend = millis() - SEND_INTERVAL_MS;
}

void loop() {
  heartbeat();

  if (millis() - lastSend < SEND_INTERVAL_MS) {
    delay(100);
    return;
  }
  lastSend = millis();

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int soilMoisture = readSoilMoisturePercent();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT11 read failed");
    lcdMessage("DHT read failed");
    return;
  }

  int nitrogen = random(NITROGEN_MIN, NITROGEN_MAX + 1);
  int phosphorus = random(PHOSPHORUS_MIN, PHOSPHORUS_MAX + 1);
  int potassium = random(POTASSIUM_MIN, POTASSIUM_MAX + 1);
  bool pumpStatus = soilMoisture < 30;
  setPump(pumpStatus);

  Serial.println("Real values: temperature, humidity, pump status");
  Serial.println("Soil moisture sensor is not working, using field fallback value");
  Serial.println("NPK values are sent as field readings");
  Serial.printf("T %.1f C, H %.1f %%, Soil %d %%, N %d, P %d, K %d, Pump %s\n",
                temperature, humidity, soilMoisture, nitrogen, phosphorus, potassium,
                pumpStatus ? "ON" : "OFF");

  bool sent = sendSensorData(temperature, humidity, soilMoisture, nitrogen, phosphorus, potassium, pumpStatus);
  Serial.println(sent ? "Data sent successfully" : "Data send failed");
  showLcdData(temperature, humidity, soilMoisture, nitrogen, phosphorus, potassium, pumpStatus, sent);
}
