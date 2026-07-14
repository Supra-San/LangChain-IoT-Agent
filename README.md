# LangChain IoT Agent

An AI-driven IoT system that integrates LangChain with an ESP32 microcontroller to autonomously control room comfort based on real-time temperature and humidity data. All control decisions are produced by a Large Language Model (LLM) — no hardcoded threshold rules.

---

## Overview

This project demonstrates an autonomous AI agent that controls a relay (representing an air conditioner or fan) via MQTT. Environmental data is read from a DHT22 sensor on an ESP32, published to a local Mosquitto broker over TLS, and consumed by a Python agent powered by LangChain and OpenAI GPT-4o-mini. The agent's decision (`ON` or `OFF`) is sent back to the ESP32, which actuates the relay accordingly.

The system uses mutual TLS (mTLS) throughout: both the broker and every client (Python agent and ESP32) authenticate with certificates signed by a self-managed Certificate Authority.

---

## System Architecture

![Architecture Overview](https://github.com/user-attachments/assets/e1b3d515-23c2-4b3e-82f2-d390bfeece76)
![Wiring Diagram](https://github.com/user-attachments/assets/bd1e2ca4-6e23-493e-b74c-b73bde69886d)

---

## Components

| Component | Description |
|-----------|-------------|
| ESP32 | Microcontroller handling DHT22 sensor input and relay output |
| DHT22 | Temperature and humidity sensor |
| Relay Module | Controls electrical device (active LOW logic) |
| Python AI Agent | LangChain-based agent using OpenAI GPT-4o-mini for reasoning |
| Mosquitto Broker | Local MQTT broker with mTLS and ACL enforcement |
| OpenAI API | Provides LLM inference for comfort analysis |

---

## Repository Structure

```
LangChain-IoT-Agent/
├── agent/
│   ├── __init__.py
│   ├── agent_langchain.py   # AI agent: payload validation, LLM call, rate limiting
│   └── mqtt_tool.py         # MQTT client wrapper with TLS support
├── certs/                   # TLS certificates and Mosquitto config (excluded from Git)
│   ├── mosquitto.conf
│   ├── mosquitto.acl
│   ├── ca.crt / ca.key
│   ├── server.crt / server.key
│   └── client.crt / client.key
├── esp32/
│   ├── esp32_iot_agent.ino  # Arduino firmware
│   └── secrets.h            # WiFi credentials and TLS certs for ESP32 (excluded from Git)
├── .env                     # Environment variables (excluded from Git)
├── generate_certs.sh        # Script to generate all TLS certificates
├── main.py                  # Application entry point
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.9 or later
- Arduino IDE with ESP32 board support
- [Mosquitto MQTT broker](https://mosquitto.org/) installed locally
- DHT22 sensor and relay module wired to the ESP32
- OpenAI API key

**Required Arduino libraries** (install via Library Manager):
- `Adafruit MQTT Library`
- `DHT sensor library` by Adafruit
- `WiFiClientSecure` (bundled with ESP32 board package)

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Supra-San/LangChain-IoT-Agent.git
cd LangChain-IoT-Agent
```

### 2. Generate TLS Certificates

All MQTT communication is secured with mutual TLS. Run the certificate generation script with a strong password of your choice:

```bash
CLIENT_PASS='your_strong_password_here' ./generate_certs.sh
```

This generates all required certificates in `./certs/`:
- A self-signed Root CA (`ca.crt`, `ca.key`)
- A server certificate with SAN extension for Mosquitto (`server.crt`, `server.key`)
- A client certificate for the Python agent and ESP32 (`client.crt`, `client.key`)
- A temporary decrypted key for ESP32 flashing (`client.decrypted.key`) — auto-deleted after 60 seconds

### 3. Start the MQTT Broker

```bash
mosquitto -c certs/mosquitto.conf
```

The broker listens on port `8883` (TLS only), requires client certificates, and enforces ACL rules restricting access to `home/room1/#` topics.

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# MQTT TLS
MQTT_BROKER=localhost
MQTT_PORT=8883
MQTT_CA_FILE=certs/ca.crt
MQTT_CERT_FILE=certs/client.crt
MQTT_KEY_FILE=certs/client.key
MQTT_KEY_PASSWORD=your_strong_password_here
```

> `MQTT_KEY_PASSWORD` must match the `CLIENT_PASS` used when generating certificates.

### 5. Create a Python Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 6. Run the AI Agent

```bash
python main.py
```

Expected output:

```
[*] TLS Certificates detected. Initiating SECURE MQTT connection on port 8883...
[*] Client ID: AI_Agent_4f9a12bc
[*] Configuring SSL/TLS for AI_Agent_4f9a12bc...
[OK] Connected to MQTT Broker: localhost:8883
[*] Subscribed to topic: home/room1/sensor
[INFO] AI Agent is active and listening for MQTT data...
```

### 7. Flash the ESP32 Firmware

1. Open `esp32/esp32_iot_agent.ino` in Arduino IDE.
2. Edit `esp32/secrets.h`:
   - Set `WLAN_SSID` and `WLAN_PASS` to your WiFi credentials.
   - Paste the contents of `certs/ca.crt`, `certs/client.crt`, and `certs/client.decrypted.key` into the corresponding string variables.
3. In `esp32_iot_agent.ino`, set `MQTT_SERVER` to your broker's local IP address.
4. Compile and upload to the ESP32 board.

The ESP32 will:
- Connect to WiFi and the MQTT broker over TLS (port 8883)
- Publish DHT22 readings every 5 minutes to `home/room1/sensor`
- Subscribe to `home/room1/control` for relay commands
- Actuate the relay (LOW = ON, HIGH = OFF) based on commands received

---

## MQTT Topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| `home/room1/sensor` | ESP32 → Agent | `{"temperature": 32.5, "humidity": 80.2}` |
| `home/room1/control` | Agent → ESP32 | `ON` or `OFF` |
| `home/room1/status` | ESP32 → Agent | `{"relay": "ON"}` |

---

## How the AI Logic Works

There are no threshold rules or if/else conditions governing the relay. The Python agent passes the raw sensor readings directly to GPT-4o-mini with the following prompt context:

> "You are an intelligent home assistant managing the air conditioner in a small 3x3 meter bedroom. Given temperature and humidity readings, respond only with ON or OFF."

The model reasons about thermal comfort and responds with a binary decision. Any response outside `ON` or `OFF` is defaulted to `OFF` as a safety measure.

The agent enforces a 30-second rate limit between LLM calls and validates all incoming sensor payloads for correct type and physical range before forwarding them to the model.

---

## Security

This project implements a layered security approach. For a full analysis, see [`security_review.md`](security_review.md).

| Control | Implementation |
|---------|---------------|
| Transport encryption | TLS 1.2 on all MQTT connections (port 8883) |
| Mutual authentication | Both broker and clients present certificates signed by the project CA |
| Authorization | Mosquitto ACL restricts each client to `home/room1/#` only |
| Anonymous access | Disabled (`allow_anonymous false`) |
| Hostname verification | Enabled; server certificate includes SAN for `localhost`/`127.0.0.1` |
| Secrets management | All credentials stored in `.env` and `certs/` (both excluded from Git) |
| Input validation | Sensor payload validated for type and physical range before LLM use |
| Rate limiting | 30-second minimum interval between OpenAI API calls |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `langchain` | Agent orchestration framework |
| `langchain-openai` | OpenAI LLM integration |
| `paho-mqtt` | MQTT client |
| `python-dotenv` | Environment variable loading |

Install all dependencies:

```bash
pip install -r requirements.txt
```

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Suprapto Santoso**  
AI & IoT Developer  
supraptosantoso.san@gmail.com
