#!/bin/bash
# generate_certs.sh
# Script to generate TLS Certificates for MQTT Broker (Mosquitto), Python Client, and ESP32.
# Certificates include SAN extensions for proper hostname verification.

set -e

# Target directory
CERT_DIR="./certs"
mkdir -p "$CERT_DIR"

# Configurations
IP_ADDRESS="127.0.0.1"
DOMAIN="localhost"
DAYS=3650

# [R-02 FIX] Read client key password from environment variable.
# Never hardcode passwords in shell scripts.
if [ -z "$CLIENT_PASS" ]; then
    echo "ERROR: CLIENT_PASS environment variable is not set."
    echo "Usage: CLIENT_PASS='your_strong_password' ./generate_certs.sh"
    exit 1
fi

echo "=========================================="
echo "Generating SSL/TLS Certificates for Secure MQTT"
echo "=========================================="

# 1. Generate CA (Certificate Authority)
echo "Generating CA..."
openssl req -new -x509 -days $DAYS -extensions v3_ca \\
    -keyout "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" \\
    -nodes -subj "/C=ID/ST=Jakarta/L=Jakarta/O=IoT-Secure/CN=IoT-RootCA"

# [R-01 FIX] Create SAN (Subject Alternative Name) config for the server certificate.
# This is required for hostname verification (tls_insecure_set(False)) to work.
cat > "$CERT_DIR/server_san.ext" << EOF
[SAN]
subjectAltName=DNS:${DOMAIN},IP:${IP_ADDRESS}
EOF

# 2. Generate Server (MQTT Broker) Key & CSR
echo "Generating Broker (Server) Certificates with SAN..."
openssl req -new -nodes -newkey rsa:2048 \\
    -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \\
    -subj "/C=ID/ST=Jakarta/L=Jakarta/O=IoT-Secure/CN=$DOMAIN"

# Sign Server Certificate with CA, including SAN extension
openssl x509 -req -in "$CERT_DIR/server.csr" \\
    -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial \\
    -out "$CERT_DIR/server.crt" -days $DAYS \\
    -extfile "$CERT_DIR/server_san.ext" -extensions SAN

# 3. Generate Client (Python Agent / ESP32) Key & CSR
echo "Generating Client Certificates..."
# We encrypt the client key with a password for the Python agent
openssl req -new -newkey rsa:2048 \\
    -passout "pass:$CLIENT_PASS" \\
    -keyout "$CERT_DIR/client.key" -out "$CERT_DIR/client.csr" \\
    -subj "/C=ID/ST=Jakarta/L=Jakarta/O=IoT-Secure/CN=MQTT-Client"

# Sign Client Certificate with CA
openssl x509 -req -in "$CERT_DIR/client.csr" \\
    -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" \\
    -out "$CERT_DIR/client.crt" -days $DAYS

# [R-03 FIX] Generate decrypted key ONLY for temporary ESP32 flashing use.
# It will be automatically deleted after 60 seconds as a safety measure.
echo ""
echo "WARNING: Generating decrypted client key for ESP32 flashing..."
echo "  This file will be automatically deleted in 60 seconds."
openssl rsa \\
    -in "$CERT_DIR/client.key" \\
    -passin "pass:$CLIENT_PASS" \\
    -out "$CERT_DIR/client.decrypted.key"

# Schedule auto-deletion of the decrypted key after 60 seconds
(sleep 60 && rm -f "$CERT_DIR/client.decrypted.key" && echo "[AUTO-CLEANUP] client.decrypted.key deleted.") &

# Clean up CSR files, serial, and SAN ext
rm -f "$CERT_DIR/server.csr" "$CERT_DIR/client.csr" "$CERT_DIR/ca.srl" "$CERT_DIR/server_san.ext"

echo "=========================================="
echo "Done! Certificates generated in $CERT_DIR:"
echo "  - ca.crt                (CA Root Certificate - for Broker, Python, ESP32)"
echo "  - ca.key                (CA Root Private Key - Keep Secret)"
echo "  - server.crt            (Broker Certificate with SAN for hostname verification)"
echo "  - server.key            (Broker Private Key)"
echo "  - client.crt            (Client Certificate - for Python Agent/ESP32)"
echo "  - client.key            (Client Private Key - Encrypted with password)"
echo "  - client.decrypted.key  (Temporary - flash to ESP32 NOW, auto-deleted in 60s)"
echo "=========================================="
echo "REMINDER: Store MQTT_KEY_PASSWORD securely in your .env file."
