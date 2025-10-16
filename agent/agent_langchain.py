"""
agent_langchain.py
-------------------
AI IoT Agent using LangChain and OpenAI.

This module listens for sensor data (temperature, humidity) via MQTT,
analyzes it using a language model, and decides whether to turn the
relay (AC) ON or OFF. The decision is sent back through MQTT to the IoT device.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from agent.mqtt_tool import MQTTClient


# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


class AIAgent:
    """
    AI Agent that uses an LLM to determine relay control
    based on environmental sensor data received from MQTT.
    """

    def __init__(self, mqtt_client: MQTTClient):
        """
        Initialize the AI Agent.

        Args:
            mqtt_client (MQTTClient): MQTT client instance for communication.
        """
        self.mqtt_client = mqtt_client
        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=api_key
        )

        self.topic_sensor = "home/room1/sensor"
        self.topic_command = "home/room1/control"
        self.topic_status = "home/room1/status"

    def analyze_environment(self, temperature: float, humidity: float) -> str:
        """
        Use the LLM to reason about the room environment
        and decide whether to turn the relay ON or OFF.

        The model is free to interpret comfort conditions for a 3x3 meter room.
        No explicit rules are enforced.
        """

        prompt = ChatPromptTemplate.from_template("""
        You are an intelligent home assistant managing the air conditioner
        in a small 3x3 meter bedroom.

        Given the following sensor readings:
        - Temperature: {temperature} °C
        - Humidity: {humidity} %

        Think logically about room comfort and air freshness.

        Respond **only** with one of the following:
        - "ON" → if the AC should be turned on.
        - "OFF" → if the AC should be turned off.
        """)

        messages = prompt.format_messages(
            temperature=temperature,
            humidity=humidity
        )

        response = self.model.invoke(messages)
        decision = response.content.strip().upper()

        if decision not in ["ON", "OFF"]:
            decision = "OFF"

        return decision

    def on_message(self, client, userdata, message):
        """MQTT callback: handle sensor data and trigger AI decision."""
        try:
            payload = message.payload.decode()
            data = json.loads(payload)
            temperature = data.get("temperature")
            humidity = data.get("humidity")

            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"\n[📡 {timestamp}] Sensor data received:")
            print(f"   🌡️ Temperature : {temperature} °C")
            print(f"   💧 Humidity    : {humidity} %")

            if temperature is not None and humidity is not None:
                decision = self.analyze_environment(temperature, humidity)
                self.mqtt_client.publish(self.topic_command, decision)

                print(f"   🤖 AI Decision  : {decision}")
                print(f"   ⚙️ Relay Status : {decision}")
                print("-" * 45)

        except Exception as e:
            print(f"[ERROR] Message processing failed: {e}")

    def run(self):
        """Start the agent and listen for incoming MQTT sensor data."""
        print("[INFO] 🔍 AI Agent is active and listening for MQTT data...")
        print(f"[INFO] Subscribed to: {self.topic_sensor}")
        self.mqtt_client.subscribe(self.topic_sensor, self.on_message)
        self.mqtt_client.loop_forever()
