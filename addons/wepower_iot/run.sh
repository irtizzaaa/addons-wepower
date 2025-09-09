#!/usr/bin/with-contenv bashio

echo "[wepower_iot] Starting WePower Sensor Add-on..."

# Load configuration
MQTT_BROKER=$(bashio::config 'mqtt_broker')
MQTT_USERNAME=$(bashio::config 'mqtt_username')
MQTT_PASSWORD=$(bashio::config 'mqtt_password')
SCAN_INTERVAL=$(bashio::config 'scan_interval')
INCLUDE_PATTERNS=$(bashio::config 'include_patterns')
EXCLUDE_PATTERNS=$(bashio::config 'exclude_patterns')
ENABLE_DISCOVERY=$(bashio::config 'enable_discovery')
DISCOVERY_PREFIX=$(bashio::config 'discovery_prefix')
PROBE_COMMAND=$(bashio::config 'probe_command')

# Phase 2 enhanced settings
DEVICE_TIMEOUT=$(bashio::config 'device_timeout')
RETRY_ATTEMPTS=$(bashio::config 'retry_attempts')
RETRY_DELAY=$(bashio::config 'retry_delay')
MESSAGE_QUEUE_SIZE=$(bashio::config 'message_queue_size')
ENABLE_DEVICE_DETECTION=$(bashio::config 'enable_device_detection')
IDENTIFICATION_TIMEOUT=$(bashio::config 'identification_timeout')
BLE_IDENTIFICATION_CMD=$(bashio::config 'ble_identification_cmd')
ZIGBEE_IDENTIFICATION_CMD=$(bashio::config 'zigbee_identification_cmd')
GENERIC_IDENTIFICATION_CMD=$(bashio::config 'generic_identification_cmd')

# Phase 2: Device Management & Pairing
ENABLE_DEVICE_PAIRING=$(bashio::config 'enable_device_pairing')
PAIRING_TIMEOUT=$(bashio::config 'pairing_timeout')
HEARTBEAT_INTERVAL=$(bashio::config 'heartbeat_interval')
CONNECTION_QUALITY_THRESHOLD=$(bashio::config 'connection_quality_threshold')
ENABLE_DEVICE_MANAGEMENT=$(bashio::config 'enable_device_management')
DEVICE_MANAGEMENT_PORT=$(bashio::config 'device_management_port')
MAX_PAIRED_DEVICES=$(bashio::config 'max_paired_devices')

# Set environment variables
export MQTT_BROKER="$MQTT_BROKER"
export MQTT_USERNAME="$MQTT_USERNAME"
export MQTT_PASSWORD="$MQTT_PASSWORD"
export SCAN_INTERVAL="$SCAN_INTERVAL"
export INCLUDE_PATTERNS="${INCLUDE_PATTERNS[*]}"
export EXCLUDE_PATTERNS="${EXCLUDE_PATTERNS[*]}"
export ENABLE_DISCOVERY="$ENABLE_DISCOVERY"
export DISCOVERY_PREFIX="$DISCOVERY_PREFIX"
export PROBE_COMMAND="$PROBE_COMMAND"

# Phase 2 enhanced environment variables
export DEVICE_TIMEOUT="$DEVICE_TIMEOUT"
export RETRY_ATTEMPTS="$RETRY_ATTEMPTS"
export RETRY_DELAY="$RETRY_DELAY"
export MESSAGE_QUEUE_SIZE="$MESSAGE_QUEUE_SIZE"
export ENABLE_DEVICE_DETECTION="$ENABLE_DEVICE_DETECTION"
export IDENTIFICATION_TIMEOUT="$IDENTIFICATION_TIMEOUT"
export BLE_IDENTIFICATION_CMD="$BLE_IDENTIFICATION_CMD"
export ZIGBEE_IDENTIFICATION_CMD="$ZIGBEE_IDENTIFICATION_CMD"
export GENERIC_IDENTIFICATION_CMD="$GENERIC_IDENTIFICATION_CMD"

# Phase 2: Device Management & Pairing environment variables
export ENABLE_DEVICE_PAIRING="$ENABLE_DEVICE_PAIRING"
export PAIRING_TIMEOUT="$PAIRING_TIMEOUT"
export HEARTBEAT_INTERVAL="$HEARTBEAT_INTERVAL"
export CONNECTION_QUALITY_THRESHOLD="$CONNECTION_QUALITY_THRESHOLD"
export ENABLE_DEVICE_MANAGEMENT="$ENABLE_DEVICE_MANAGEMENT"
export DEVICE_MANAGEMENT_PORT="$DEVICE_MANAGEMENT_PORT"
export MAX_PAIRED_DEVICES="$MAX_PAIRED_DEVICES"

echo "[wepower_iot] Configuration loaded:"
echo "[wepower_iot] include_patterns=$INCLUDE_PATTERNS"
echo "[wepower_iot] exclude_patterns=$EXCLUDE_PATTERNS"
echo "[wepower_iot] mqtt_broker=$MQTT_BROKER"
echo "[wepower_iot] enable_device_detection=$ENABLE_DEVICE_DETECTION"
echo "[wepower_iot] enable_device_pairing=$ENABLE_DEVICE_PAIRING"
echo "[wepower_iot] enable_device_management=$ENABLE_DEVICE_MANAGEMENT"
echo "[wepower_iot] scan_interval=${SCAN_INTERVAL}s (${SCAN_INTERVAL}s)"
echo "[wepower_iot] heartbeat_interval=${HEARTBEAT_INTERVAL}s"
echo "[wepower_iot] pairing_timeout=${PAIRING_TIMEOUT}s"

# Check if device management is enabled
if [ "$ENABLE_DEVICE_MANAGEMENT" = "true" ]; then
    echo "[wepower_iot] Device management interface enabled on port $DEVICE_MANAGEMENT_PORT"
fi

# Check if device pairing is enabled
if [ "$ENABLE_DEVICE_PAIRING" = "true" ]; then
    echo "[wepower_iot] Device pairing system enabled (BLE/Zigbee)"
    echo "[wepower_iot] Max paired devices per dongle: $MAX_PAIRED_DEVICES"
fi

# Start the Python application
cd /app
echo "[wepower_iot] Starting Python application..."
exec python3 main.py

