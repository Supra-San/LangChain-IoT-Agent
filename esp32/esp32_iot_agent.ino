#include <WiFi.h>
#include <WiFiClient.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include "DHT.h"

/************************* WiFi Configuration *******************************/
#define WLAN_SSID       "your_ssid"
#define WLAN_PASS       "your_password"

/************************* MQTT Configuration *******************************/
#define MQTT_SERVER     "broker.hivemq.com"
#define MQTT_PORT       1883

#define SENSOR_TOPIC    "home/room1/sensor"
#define CONTROL_TOPIC   "home/room1/control"
#define STATUS_TOPIC    "home/room1/status"

/************************* DHT22 Sensor Setup *******************************/
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

/************************* Relay Configuration ******************************/
#define RELAY_PIN 2   // GPIO2 (D2)
bool relayState = false;

/************************* MQTT Client Setup *******************************/
WiFiClient client;
Adafruit_MQTT_Client mqtt(&client, MQTT_SERVER, MQTT_PORT);
Adafruit_MQTT_Publish dht22_sensor = Adafruit_MQTT_Publish(&mqtt, SENSOR_TOPIC);
Adafruit_MQTT_Subscribe control_topic = Adafruit_MQTT_Subscribe(&mqtt, CONTROL_TOPIC);

/************************* Setup Function ***********************************/
void setup() {
  Serial.begin(115200);
  delay(10);

  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(WLAN_SSID);

  WiFi.begin(WLAN_SSID, WLAN_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi Connected!");
  Serial.print("📡 IP Address: ");
  Serial.println(WiFi.localIP());

  dht.begin();

  // Initialize relay
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Relay OFF (active LOW)

  // Subscribe to AI Agent control topic
  mqtt.subscribe(&control_topic);
  Serial.println("🔌 Waiting for MQTT connection...");
}

/************************* Main Loop *****************************************/
void loop() {
  MQTT_connect();

  // Listen for control messages from AI Agent
  Adafruit_MQTT_Subscribe *subscription;
  while ((subscription = mqtt.readSubscription(100))) {
    if (subscription == &control_topic) {
      String command = (char *)control_topic.lastread;
      command.trim();

      Serial.print("📩 MQTT Message Received: ");
      Serial.println(command);

      if (command == "ON") {
        digitalWrite(RELAY_PIN, LOW);   // Activate relay
        relayState = true;
        Serial.println("⚙️ Relay ON (Fan/AC Activated)");
      } 
      else if (command == "OFF") {
        digitalWrite(RELAY_PIN, HIGH);  // Deactivate relay
        relayState = false;
        Serial.println("⚙️ Relay OFF (Fan/AC Deactivated)");
      }

      // Send relay status back to broker
      String statusMsg = String("{\"relay\": \"") + (relayState ? "ON" : "OFF") + "\"}";
      mqtt.publish(STATUS_TOPIC, statusMsg.c_str());
      Serial.println("📤 Relay status published to broker.");
    }
  }

  // Publish sensor data every 5 seconds
  static unsigned long lastSend = 0;
  if (millis() - lastSend > 5000) {
    lastSend = millis();

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (isnan(h) || isnan(t)) {
      Serial.println(F("⚠️ Failed to read from DHT sensor!"));
      return;
    }

    String jsonData = "{ \"temperature\": " + String(t, 2) +
                      ", \"humidity\": " + String(h, 2) + " }";

    if (dht22_sensor.publish(jsonData.c_str())) {
      Serial.println("📡 Sensor data published:");
      Serial.print("   🌡️ Temperature: ");
      Serial.print(t);
      Serial.print(" °C, 💧 Humidity: ");
      Serial.print(h);
      Serial.println(" %");
    } else {
      Serial.println("❌ Failed to publish sensor data.");
    }
  }
}

/************************* MQTT Connection Helper ***************************/
void MQTT_connect() {
  int8_t ret;

  if (mqtt.connected()) {
    return;
  }

  Serial.print("🔌 Connecting to MQTT... ");

  uint8_t retries = 3;
  while ((ret = mqtt.connect()) != 0) {
    Serial.println(mqtt.connectErrorString(ret));
    Serial.println("⏳ Retrying in 5 seconds...");
    mqtt.disconnect();
    delay(5000);
    retries--;
    if (retries == 0) {
      Serial.println("❌ Unable to connect to MQTT broker.");
      while (1);
    }
  }

  Serial.println("✅ MQTT Connected!");
}