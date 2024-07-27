#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include "DHT.h"
#include <HTTPClient.h>

// Konfigurasi pin dan variabel
#define MQ135PIN 32    // Pin analog untuk MQ135
#define LED_PIN_1 15
#define LED_PIN_2 2
#define LED_PIN_3 4
#define BUZZER_PIN 19
#define DHTPIN 5       // Pin digital untuk DHT11
#define DHTTYPE DHT11  // Tipe sensor DHT11

const char* ssid = "LABOR SAMSUNG";
const char* password = "hhpsamsung02";
const char* serverUrl = "http://192.168.1.20:5000/sensor/data/"; // Sesuaikan dengan IP dan port server Anda
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 60000; // 1 menit dalam milidetik

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org");
WiFiClient wifi;
DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C LCD(0x27, 20, 4); // Alamat I2C dan ukuran LCD

// Variabel global untuk suhu, kelembapan, dan ppm
float suhu = 0.0;
float kelembapan = 0.0;
float ppm = 0.0;

unsigned long lastLCDUpdate = 0;
const unsigned long lcdUpdateInterval = 10000; // Interval update LCD (10 detik)
int displayState = 0; // 0: Title, 1: Message, 2: Data

unsigned long lastDataDisplayUpdate = 0;
const unsigned long dataDisplayInterval = 5000; // Interval update tampilan data (5 detik)
int dataDisplayState = 0; // 0: PPM, 1: AQI

void spinner() {
  static int8_t counter = 0;
  const char* glyphs = "\xa1\xa5\xdb";
  LCD.setCursor(15, 1);
  LCD.print(glyphs[counter++]);
  if (counter == strlen(glyphs)) {
    counter = 0;
  }
}

void wifiConnect() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    spinner();
    Serial.print(".");
  }
  Serial.println(" Connected");
}

void LCD_init() {
  LCD.init();
  LCD.backlight();
}

void displayTitle() {
  LCD.clear();
  LCD.setCursor(0, 0);
  LCD.print(" Suhu - Temperature");
  LCD.setCursor(0, 1);
  LCD.print("   Kualitas Udara   ");
  LCD.setCursor(0, 2);
  LCD.print("    SMK Negeri 2   ");
  LCD.setCursor(0, 3);
  LCD.print("     Pekanbaru     ");
}

void displayMessage() {
  LCD.clear();
  LCD.setCursor(0, 0);
  LCD.print(" Jangan Lupa Untuk");
  LCD.setCursor(0, 1);
  LCD.print(" Menjaga Kebersihan");
  LCD.setCursor(0, 2);
  LCD.print("Lingkungan Kita Agar");
  LCD.setCursor(0, 3);
  LCD.print("Udara Menjadi Bersih");
}

void displayData(float temperature, float humidity, float ppm) {
  unsigned long currentMillis = millis();
  if (currentMillis - lastDataDisplayUpdate >= dataDisplayInterval) {
    lastDataDisplayUpdate = currentMillis;
    dataDisplayState = (dataDisplayState + 1) % 2; // Toggle between 0 and 1
  }

  LCD.clear();
  // Menampilkan suhu dan kelembapan
  LCD.setCursor(0, 0);
  LCD.print("Temperature : " + String(temperature, 1) + "C");
  LCD.setCursor(0, 1);
  LCD.print("Humidity : " + String(humidity, 1) + "%");

  // Menampilkan kategori suhu
  String tempCategory = determineTempCategory(temperature);
  LCD.setCursor(0, 2);
  LCD.print("Temp : " + tempCategory);

  // Menampilkan nilai PPM atau kategori PPM berdasarkan state
  if (dataDisplayState == 0) {
    LCD.setCursor(0, 3);
    LCD.print("PPM : " + String(ppm, 1) + "  PPM");
  } else {
    String ppmCategory = determinePPMCategory(ppm);
    LCD.setCursor(0, 3);
    LCD.print("AQI : " + ppmCategory);
  }
}

String determineTempCategory(float temperature) {
  if (temperature < 30) {
    return "Normal";
  } else if (temperature < 40) {
    return "Hangat";
  } else {
    return "Panas";
  }
}

String determinePPMCategory(float ppm) {
  if (ppm < 100) {
    return "Sangat Baik";
  } else if (ppm < 150) {
    return "Baik";
  } else if (ppm < 200) {
    return "Buruk";
  } else {
    return "Sangat Buruk";
  }
}

String padZero(int value) {
  return (value < 10 ? "0" : "") + String(value);
}

void Led_Danger() {
  digitalWrite(LED_PIN_1, HIGH);
  digitalWrite(LED_PIN_2, LOW);
  digitalWrite(LED_PIN_3, LOW);
}

void Led_Warning() {
  digitalWrite(LED_PIN_1, LOW);
  digitalWrite(LED_PIN_2, HIGH);
  digitalWrite(LED_PIN_3, LOW);
}

void Led_Safe() {
  digitalWrite(LED_PIN_1, LOW);
  digitalWrite(LED_PIN_2, LOW);
  digitalWrite(LED_PIN_3, HIGH);
}

void Warning(float temp, float humidity, float ppm) {
  if ((temp > 40 && temp <= 70) || (ppm > 150 && ppm <= 200)) { // Peringatan suhu tinggi
    Led_Warning();
    int buzzerTone = 262;
    int toneDuration = 250;
    int delayBetweenTones = 1000;
    int numBeeps = 60;

    for (int i = 0; i < numBeeps; i++) {
        tone(BUZZER_PIN, buzzerTone, toneDuration);
        delay(toneDuration + delayBetweenTones);
        noTone(BUZZER_PIN);
    }
  } else if (temp > 70 || ppm > 200) { // Suhu sangat tinggi
    Led_Danger();
    tone(BUZZER_PIN, 523);
  } else {
    Led_Safe();
    noTone(BUZZER_PIN);
  }

  Serial.println("Temp: " + String(temp, 2) + "°C");
  Serial.println("Humidity: " + String(humidity, 1) + "%");
  Serial.println("PPM In Air: " + String(ppm, 2) + "ppm");
  Serial.println("--------");
}

float bacaPPM() {
  int adcValue = analogRead(MQ135PIN);
  float ppm = konversiPPM(adcValue);
  return ppm;
}

float konversiPPM(int adcValue) {
  // Karakteristik MQ135 untuk konversi dari nilai ADC ke PPM
  float ppm = 0.2 * adcValue - 50.0;
  return ppm;
}

void sendData() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastSendTime >= sendInterval) {
    lastSendTime = currentMillis;

    // Ambil waktu saat ini dari server NTP
    time_t now = timeClient.getEpochTime();
    struct tm *timeinfo = localtime(&now);

    // Baca nilai sensor
    kelembapan = dht.readHumidity();
    suhu = dht.readTemperature();
    ppm = bacaPPM();

    if (isnan(kelembapan) || isnan(suhu) || isnan(ppm)) {
      Serial.println("Gagal membaca sensor!");
      return;
    }

    // Tentukan kualitas udara berdasarkan nilai PPM
    String kualitasUdara = determinePPMCategory(ppm);

    // Kirim data ke server Flask
    String data = "{";
    data += "\"kelembapan\": " + String(kelembapan, 2) + ",";
    data += "\"suhu\": " + String(suhu, 2) + ",";
    data += "\"ppm\": " + String(ppm, 2) + ",";
    data += "\"kualitas\": \"" + kualitasUdara + "\",";
    data += "\"timestamp\": \"" + String(timeinfo->tm_year + 1900) + "-" 
                          + padZero(timeinfo->tm_mon + 1) + "-" 
                          + padZero(timeinfo->tm_mday) + " " 
                          + padZero(timeinfo->tm_hour) + ":" 
                          + padZero(timeinfo->tm_min) + ":" 
                          + padZero(timeinfo->tm_sec) + "\"";
    data += "}";

    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(data);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Response: " + response);
    } else {
      Serial.println("Error on sending POST: " + String(httpResponseCode));
    }
    http.end();
  }
}

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(MQ135PIN, INPUT);
  pinMode(LED_PIN_1, OUTPUT);
  pinMode(LED_PIN_2, OUTPUT);
  pinMode(LED_PIN_3, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  LCD_init();
  wifiConnect();
  timeClient.begin();
}

void loop() {
  timeClient.update();

  unsigned long currentMillis = millis();
  if (currentMillis - lastLCDUpdate >= lcdUpdateInterval) {
    lastLCDUpdate = currentMillis;

    // Ganti tampilan LCD
    switch (displayState) {
      case 0:
        displayTitle();
        break;
      case 1:
        displayMessage();
        break;
      case 2:
        displayData(suhu, kelembapan, ppm);
        break;
    }
    displayState = (displayState + 1) % 3;
  }

  sendData();

  suhu = dht.readTemperature();
  kelembapan = dht.readHumidity();
  ppm = bacaPPM();

  Warning(suhu, kelembapan, ppm);
}
