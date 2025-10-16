# 🧠 LangChain-IoT-Agent
A fully AI-driven IoT system that integrates LangChain and ESP32 to automatically control room comfort using temperature and humidity data.
The system works without explicit logic, relying entirely on LLM reasoning.<br />


# 🌍 Overview
This project demonstrates an autonomous AI agent that controls a relay (representing an air conditioner or fan) through ESP32, based on environmental data from a DHT22 sensor.
All control logic is decided by a Large Language Model (LLM) using LangChain — making the decision process fully AI-driven.<br />

# 🧩 Components

| Component           | Description                                                |
| ------------------- | ---------------------------------------------------------- |
| **ESP32**           | IoT microcontroller handling sensor input and relay output |
| **DHT22**           | Sensor for temperature and humidity                        |
| **Relay Module**    | Controls electrical device (active LOW)                    |
| **LangChain Agent** | Python-based AI agent using OpenAI LLM                     |
| **MQTT Broker**     | Communication hub (HiveMQ public broker)                   |
| **OpenAI API**      | Provides LLM reasoning for environment comfort             |

# 📁 Folder Structure
        Langchain-IoT-Agent
        |
        ├── agent/
        │   ├── __init__.py
        │   └── agent_langchain.py
        │   └── mqtt_tool.py
        │   └── .env
        ├── esp32/
        │   └── esp32_iot_agent.ino
        ├── main.py
        ├── requirements.txt
        └── README.md

# ⚙️ Installation and Setup
#### 🧩 1. Prerequisites
* Python ≥ 3.9
* ESP32 board configured in Arduino IDE
* DHT22 temperature/humidity sensor
* Relay module (active low)
* MQTT broker (e.g., HiveMQ)

#### 💻 2. Setup Python Environment
### Clone the repository:
```bash
git clone https://github.com/<your-username>/AI-IoT-SmartRoom.git
cd AI-IoT-SmartRoom
```

### Create virtual environment
```bash
python -m venv venv
source venv/bin/activate   # (or venv\Scripts\activate on Windows)
```

### Install dependencies
```bash
pip install -r requirements.txt
```

#### 🔑 3. Configure API Key
Create a .env file inside the agent/ directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

#### 🚀 4. Run the AI Agent
```bash
python main.py
```

Expected terminal output:
```bash
[INFO] 🔍 AI Agent is active and listening for MQTT data...
[✅] Connected to MQTT Broker: broker.hivemq.com:1883
```

#### 🔌 5. Upload ESP32 Firmware

Open esp32_iot_agent.ino using Arduino IDE:
* Update WiFi credentials (WLAN_SSID, WLAN_PASS)
* Compile and upload to your ESP32 board

The ESP32 will:
* Connect to WiFi and MQTT
* Publish DHT22 sensor data to topic home/room1/sensor
* Listen for AI decisions on topic home/room1/control
* Control relay (LOW = ON, HIGH = OFF)

# 🧠 How It Works (AI Logic)

Unlike traditional control systems, no if/else or threshold rules exist in this project.
Instead, the LangChain agent asks the LLM to reason about comfort in a small 3x3m room using natural language.

Example reasoning:
> [!NOTE]
> “Temperature is 33°C and humidity 83%. The room feels hot and humid — AC should be ON.”

or
> [!NOTE]
> “Temperature is 25°C and humidity 50%. The room is comfortable — AC should be OFF.”

# 📊 MQTT Topics
| Topic                | Direction     | Description                 |
| -------------------- | ------------- | --------------------------- |
| `home/room1/sensor`  | ESP32 → Agent | Temperature & humidity data |
| `home/room1/control` | Agent → ESP32 | AI decision (ON/OFF)        |
| `home/room1/status`  | ESP32 → Agent | Relay status confirmation   |

# 🧪 Example Console Logs
* ESP32<br />
  📡 Data sent: { "temperature": 32.5, "humidity": 80.2 }<br />
  📩 Received command: ON<br />
  ⚙️  Relay ON (AC active)<br />
  📤 Status relay sent: { "relay": "ON" }

* AI Agent<br />
 [📡 21:24:28] Sensor data received:<br />
   🌡️ Temperature : 32.5 °C<br />
   💧 Humidity    : 80.2 %<br />
 🤖 AI Decision: ON<br />
 ⚙️ Relay Status: ON

# 📜 License
This project is licensed under the MIT License — feel free to use, modify, and distribute.

# 🧑‍💻 Author
Suprapto Santoso<br />
AI & IoT Developer<br />
🚀 Focused on Generative AI, Embedded Systems, and Smart Automation<br />
supraptosantoso.san@gmail.com






