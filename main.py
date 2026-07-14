"""
===========================================================
AI-IoT Smart Room — Main Entry Script
===========================================================

This script serves as the main entry point for the AI-driven IoT system.
It initializes both the MQTT communication client and the AI reasoning agent
that processes environmental data (temperature and humidity) received from ESP32.

The agent uses a Large Language Model (LLM) through LangChain to reason
about room comfort (for a 3x3 meter space) and determine whether the relay
should be ON or OFF — **without any explicit threshold-based rules**.

-----------------------------------------------------------
Author  : Suprapto Santoso
Project : AI-IoT Smart Room
Version : 1.0.0
License : MIT
-----------------------------------------------------------

Workflow:
----------
1. The MQTTClient connects to the broker (e.g., HiveMQ) and subscribes
   to the topic where the ESP32 publishes sensor data (`home/room1/sensor`).

2. The AIAgent listens to incoming messages and uses an LLM prompt
   to interpret the environment conditions and generate a control decision
   (`ON` or `OFF`).

3. The decision is then published to the control topic (`home/room1/control`)
   where the ESP32 reads it and switches the relay accordingly.

Example:
---------
Run this script to start the AI agent listener:

    $ python main.py

Expected output:
-----------------
[INFO] 🔍 AI Agent is active and listening for MQTT data...
[✅] Connected to MQTT Broker: broker.hivemq.com:1883
[📡] Sensor data received: { "temperature": 32.7, "humidity": 82.4 }
🤖 AI Decision: ON
⚙️ Relay Status: ON

Dependencies:
-------------
- Python >= 3.9
- LangChain
- OpenAI API
- Paho MQTT

Environment Variables:
----------------------
The OpenAI API key must be stored in `.env` under the agent directory:

    OPENAI_API_KEY=your_openai_api_key_here
"""

import os
import uuid
from dotenv import load_dotenv
from agent.mqtt_tool import MQTTClient
from agent.agent_langchain import AIAgent


def main():
    """
    Main execution function.

    Initializes the MQTT client and the AI Agent, then starts the agent's
    main loop to continuously listen for sensor data and make AI-based
    control decisions.

    Loads TLS configuration from environment variables.
    """
    load_dotenv()

    broker = os.getenv("MQTT_BROKER", "localhost")
    port = int(os.getenv("MQTT_PORT", "8883"))
    ca_certs = os.getenv("MQTT_CA_FILE", "certs/ca.crt")
    certfile = os.getenv("MQTT_CERT_FILE", "certs/client.crt")
    keyfile = os.getenv("MQTT_KEY_FILE", "certs/client.key")

    # [R-02 FIX] No default password — must be set explicitly in .env.
    # Raises EnvironmentError to prevent silent use of hardcoded fallback.
    keyfile_password = os.getenv("MQTT_KEY_PASSWORD")
    if not keyfile_password:
        raise EnvironmentError(
            "MQTT_KEY_PASSWORD is not set. "
            "Please add it to your .env file. "
            "Refusing to start without a key password."
        )

    # [R-07 FIX] Use randomized client ID to avoid topology fingerprinting
    # and prevent session conflicts when multiple instances run concurrently.
    client_id = f"AI_Agent_{uuid.uuid4().hex[:8]}"

    # If CA certificate exists, connect securely using TLS/SSL
    if os.path.exists(ca_certs):
        print(f"[🛡️] TLS Certificates detected. Initiating SECURE MQTT connection on port {port}...")
        print(f"[🔑] Client ID: {client_id}")
        mqtt = MQTTClient(
            broker=broker,
            port=port,
            client_id=client_id,
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
            keyfile_password=keyfile_password
        )
    else:
        # [R-04 FIX] Refuse to start without TLS — no insecure fallback.
        # An unencrypted connection would expose sensor data and relay
        # commands in plaintext on the network.
        raise FileNotFoundError(
            f"CA Certificate '{ca_certs}' not found. "
            "Secure (TLS) connection is required. "
            "Run generate_certs.sh to create certificates, "
            "then verify paths in your .env file."
        )

    agent = AIAgent(mqtt)
    agent.run()


if __name__ == "__main__":
    main()

