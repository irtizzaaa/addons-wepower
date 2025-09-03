# WePower Sensor Add-on

Enhanced multi-serial scanner with device type detection, MQTT queuing, two-way communication, and comprehensive device management for Home Assistant.

## Features

### 🔍 **Device Type Detection**
- **"Who are you?" Protocol**: Automatically identifies connected dongles
- **Multi-Protocol Support**: Detects BLE, Zigbee, Z-Wave, and Matter devices
- **Device Fingerprinting**: Creates unique identifiers for each device
- **Capability Detection**: Identifies device capabilities automatically

### 📡 **Enhanced MQTT Communication**
- **Two-Way Communication**: Send commands to devices via MQTT
- **Message Queuing**: Reliable message delivery with retry logic
- **Structured Data Format**: JSON-based message structure
- **Authentication Support**: Secure MQTT connections

### 🔄 **Reliability Features**
- **Automatic Reconnection**: Handles device disconnections gracefully
- **Message Retry Logic**: Configurable retry attempts with exponential backoff
- **Device Timeout Handling**: Detects and reports inactive devices
- **Queue Management**: Prevents message loss during network issues

### 🆕 **Phase 2: Advanced Device Management**
- **Device Pairing System**: Automatic pairing with BLE and Zigbee devices
- **Heartbeat Monitoring**: Continuous device health monitoring
- **Connection Quality Tracking**: Real-time connection quality metrics
- **Device Registry**: Comprehensive device tracking and management
- **Pairing Status Management**: Track pairing progress and results
- **Capability-Based Operations**: Device-specific functionality based on capabilities

## Installation

1. Add this repository to your Home Assistant add-ons
2. Install the "WePower Sensor" add-on
3. Configure the settings (see Configuration section)
4. Start the add-on

## Configuration

### Basic Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `mqtt_broker` | `mqtt://homeassistant:1883` | MQTT broker URL |
| `mqtt_username` | `""` | MQTT username (optional) |
| `mqtt_password` | `""` | MQTT password (optional) |
| `scan_interval` | `0.02` | Port scanning interval in seconds (minimum: 20ms, maximum: 60s) |
| `enable_discovery` | `true` | Enable MQTT device discovery |

**Note**: The scan interval controls how frequently the add-on checks each serial port for new data. This value is used in the main scanning loop and affects data freshness, system resource usage, and network traffic. For high-frequency applications like industrial monitoring, you can set this to 20ms (0.02 seconds). For general monitoring, 1-5 seconds is usually sufficient.

### Port Filtering

| Setting | Default | Description |
|---------|---------|-------------|
| `include_patterns` | `["/dev/ttyUSB*", "/dev/ttyACM*"]` | Port patterns to include |
| `exclude_patterns` | `["/dev/ttyS*", "/dev/input*", "/dev/hidraw*"]` | Port patterns to exclude |

### Enhanced Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_device_detection` | `true` | Enable automatic device type detection |
| `device_timeout` | `30.0` | Device timeout in seconds |
| `retry_attempts` | `3` | Number of message retry attempts |
| `retry_delay` | `1.0` | Base delay between retries in seconds |
| `message_queue_size` | `100` | Maximum messages in queue |
| `identification_timeout` | `5.0` | Device identification timeout |

### Phase 2: Device Management Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_device_pairing` | `true` | Enable device pairing functionality |
| `pairing_timeout` | `30.0` | Device pairing timeout in seconds |
| `heartbeat_interval` | `10.0` | Device heartbeat interval in seconds |
| `connection_quality_threshold` | `0.8` | Minimum connection quality threshold (0.0-1.0) |
| `enable_device_management` | `true` | Enable device management features |
| `device_management_port` | `8080` | Port for device management interface |
| `max_paired_devices` | `50` | Maximum number of paired devices per dongle |

## MQTT Topics

### Device Discovery
```
wepower_iot/discovery/{fingerprint}
```
Publishes device discovery information when a new device is identified.

### Device Data
```
wepower_iot/{device_id}/data
```
Publishes data received from serial devices.

### Device Status
```
wepower_iot/{device_id}/status
```
Publishes device connection status and health information.

### Device Heartbeat
```
wepower_iot/{device_id}/heartbeat
```
Publishes device heartbeat and connection quality information.

### Device Identification
```
wepower_iot/{device_id}/identification
```
Publishes device identification and type detection results.

### Commands (Incoming)
```
wepower_iot/{device_id}/command
```
Receives commands to send to specific devices.

### Configuration (Incoming)
```
wepower_iot/{device_id}/config
```
Receives configuration updates for devices.

### Device Registry
```
wepower_iot/registry/summary
wepower_iot/registry/devices/{device_slug}/status
```
Publishes comprehensive device registry information and individual device statuses.

## Message Formats

### Device Discovery Message
```json
{
  "device_path": "/dev/ttyUSB0",
  "device_type": "ble",
  "fingerprint": "a1b2c3d4",
  "capabilities": ["serial_communication", "bluetooth_low_energy", "device_discovery"],
  "discovered_at": "2024-01-01T12:00:00Z",
  "metadata": {
    "response_sample": "424c455f444f4e474c45",
    "identification_time": "2024-01-01T12:00:00Z"
  }
}
```

### Device Data Message
```json
{
  "device": "/dev/ttyUSB0",
  "data": "BLE_DEVICE_DATA",
  "ts": "2024-01-01T12:00:00Z",
  "device_type": "ble",
  "fingerprint": "a1b2c3d4"
}
```

### Device Status Message
```json
{
  "device": "/dev/ttyUSB0",
  "state": "connected",
  "error": null,
  "ts": "2024-01-01T12:00:00Z",
  "device_info": {
    "device_path": "/dev/ttyUSB0",
    "device_type": "ble",
    "fingerprint": "a1b2c3d4",
    "capabilities": ["serial_communication", "bluetooth_low_energy"],
    "last_seen": "2024-01-01T12:00:00Z",
    "is_connected": true,
    "pairing_status": "paired",
    "connection_quality": 0.95
  }
}
```

### Device Heartbeat Message
```json
{
  "device": "/dev/ttyUSB0",
  "heartbeat": true,
  "connection_quality": 0.95,
  "ts": "2024-01-01T12:00:00Z"
}
```

### Device Registry Summary
```json
{
  "total_devices": 3,
  "device_types": {
    "ble": 2,
    "zigbee": 1
  },
  "status_counts": {
    "connected": 2,
    "identifying": 1
  },
  "pairing_status_counts": {
    "paired": 1,
    "not_paired": 2
  },
  "ts": "2024-01-01T12:00:00Z"
}
```

### Command Message (Send to device)
```json
{
  "command": "identify",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Device Types

### BLE (Bluetooth Low Energy)
- **Identification Commands**: `WHO_ARE_YOU`, `BLE_ID`, `IDENTIFY`
- **Response Patterns**: `BLE`, `BLUETOOTH`, `BT_`, `BLE_`
- **Capabilities**: `bluetooth_low_energy`, `device_discovery`, `data_transmission`, `beacon_scanning`
- **Pairing Support**: ✅ Full pairing support with automatic device discovery

### Zigbee
- **Identification Commands**: `ZIGBEE_ID`, `COORDINATOR_ID`, `IDENTIFY`
- **Response Patterns**: `ZIGBEE`, `ZIG`, `COORDINATOR`, `ZHA_`
- **Capabilities**: `zigbee_coordinator`, `device_pairing`, `network_management`
- **Pairing Support**: ✅ Full pairing support with network management

### Z-Wave
- **Identification Commands**: `ZWAVE_ID`, `CONTROLLER_ID`, `IDENTIFY`
- **Response Patterns**: `ZWAVE`, `ZW_`, `CONTROLLER`, `ZW_`
- **Capabilities**: `zwave_controller`, `device_inclusion`, `network_management`
- **Pairing Support**: ❌ Not supported (use native Z-Wave integration)

### Matter
- **Identification Commands**: `MATTER_ID`, `FABRIC_ID`, `IDENTIFY`
- **Response Patterns**: `MATTER`, `FABRIC`, `MT_`, `MATTER_`
- **Capabilities**: `matter_fabric`, `device_commissioning`, `network_management`
- **Pairing Support**: ❌ Not supported (use native Matter integration)

### Generic
- **Identification Commands**: `AT+INFO`, `IDENTIFY`
- **Response Patterns**: `AT+`, `OK`, `ERROR`, `READY`
- **Capabilities**: `serial_communication`, `basic_at_commands`
- **Pairing Support**: ❌ Basic serial communication only

## Usage Examples

### Sending Commands to Devices

To send a command to a specific device:

```bash
mosquitto_pub -h localhost -t "wepower_iot/dev_ttyUSB0/command" -m '{"command": "identify"}'
```

### Monitoring Device Discovery

To monitor for new devices:

```bash
mosquitto_sub -h localhost -t "wepower_iot/discovery/#" -v
```

### Monitoring Device Data

To monitor data from all devices:

```bash
mosquitto_sub -h localhost -t "wepower_iot/+/data" -v
```

### Monitoring Device Heartbeats

To monitor device health and connection quality:

```bash
mosquitto_sub -h localhost -t "wepower_iot/+/heartbeat" -v
```

### Monitoring Device Registry

To monitor comprehensive device status:

```bash
mosquitto_sub -h localhost -t "wepower_iot/registry/#" -v
```

## Troubleshooting

### Device Not Detected
1. Check if the device is in the include patterns
2. Verify the device is not in the exclude patterns
3. Check device permissions and USB access
4. Enable debug logging to see identification attempts

### MQTT Connection Issues
1. Verify MQTT broker URL and credentials
2. Check network connectivity
3. Review MQTT broker logs
4. Verify topic permissions

### Message Delivery Issues
1. Check message queue size settings
2. Review retry configuration
3. Monitor MQTT broker performance
4. Check for network connectivity issues

### Device Pairing Issues
1. Verify device supports pairing (BLE/Zigbee only)
2. Check pairing timeout settings
3. Monitor pairing status in device registry
4. Review device capabilities and pairing requirements

## Development

### Adding New Device Types

To add support for a new device type:

1. Add the device type to the `DeviceType` enum
2. Add identification commands to `IDENTIFICATION_COMMANDS`
3. Add response patterns to `RESPONSE_PATTERNS`
4. Update capability detection in `_determine_capabilities`
5. Add pairing support if applicable

### Custom Message Formats

The add-on supports custom message formats through the MQTT command interface. Send configuration messages to customize device behavior.

### Device Management API

The add-on provides a comprehensive device management API through MQTT topics, allowing external systems to:
- Monitor device status and health
- Control device pairing processes
- Configure device parameters
- Retrieve device capabilities and information

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
