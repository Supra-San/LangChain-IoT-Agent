"""
mqtt_tool.py
-------------
MQTT communication utility for AI IoT Agent.

This module provides a lightweight MQTT client wrapper using the Paho MQTT library.
It handles connections, subscriptions, and message publishing between the AI Agent
and IoT devices such as ESP32. The class is designed for simplicity and easy integration
with LangChain-based intelligent agents.
"""

import paho.mqtt.client as mqtt

class MQTTClient:
    """
    A simple MQTT client wrapper for connecting, subscribing, and publishing
    messages to an MQTT broker (e.g., HiveMQ Public Broker).

    Used by the AI Agent to communicate with the ESP32 device.
    """

    def __init__(self, broker="broker.hivemq.com", port=1883, client_id="AI_Agent_Client"):
        """Initialize MQTT client with connection parameters."""
        self.broker = broker
        self.port = port
        self.client_id = client_id

        # Create MQTT client instance
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)

        # Define callback methods
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.user_callback = None

    def on_connect(self, client, userdata, flags, rc):
        """Handle successful or failed connection to MQTT broker."""
        if rc == 0:
            print(f"[✅] Connected to MQTT Broker: {self.broker}:{self.port}")
            # Subscribe to a topic if already defined
            if hasattr(self, 'topic_to_subscribe'):
                client.subscribe(self.topic_to_subscribe)
                print(f"[🔔] Subscribed to topic: {self.topic_to_subscribe}")
        else:
            print(f"[❌] Failed to connect. Return code={rc}")

    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages and pass them to user-defined callback."""
        print(f"\n[📥] Message received on {msg.topic}")
        print(f"     Payload: {msg.payload.decode()}")
        if self.user_callback:
            self.user_callback(client, userdata, msg)

    def subscribe(self, topic, callback):
        """Subscribe to a given topic and set a callback for incoming messages."""
        self.topic_to_subscribe = topic
        self.user_callback = callback

    def publish(self, topic, payload):
        """Publish a message to a specific topic."""
        print(f"[🚀] Publishing to topic: {topic} → {payload}")
        self.client.publish(topic, payload)

    def loop_forever(self):
        """Start the MQTT client loop and keep the connection alive."""
        print("[🔄] Starting MQTT loop...")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()