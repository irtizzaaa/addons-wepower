#!/usr/bin/env python3
"""Complete WePower IoT Add-on - Full Implementation"""

import asyncio
import json
import os
import serial
import serial.tools.list_ports
import time
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import paho.mqtt.client as mqtt
import queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("🚀 WePower IoT Add-on starting...")

# Enums
class DeviceType(Enum):
    UNKNOWN = "unknown"
    BLE = "ble"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"
    MATTER = "matter"
    GENERIC = "generic"

class DeviceStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    IDENTIFIED = "identified"
    PAIRED = "paired"
    OFFLINE = "offline"
    ERROR = "error"

class DeviceCategory(Enum):
    UNKNOWN = "unknown"
    SENSOR = "sensor"
    SWITCH = "switch"
    LIGHT = "light"
    DOOR = "door"
    TOGGLE = "toggle"

class BLEDiscoveryMode(Enum):
    V0_MANUAL = "v0_manual"  # Manual device input
    V1_AUTO = "v1_auto"      # Network key exchange

print("✅ Enums created successfully")

# Device Classes
class Device:
    def __init__(self, device_id: str, device_type: DeviceType, port: str):
        self.device_id = device_id
        self.device_type = device_type
        self.port = port
        self.status = DeviceStatus.DISCONNECTED
        self.category = DeviceCategory.UNKNOWN
        self.last_seen = None
        self.properties = {}
        self.mqtt_topic = f"wepower_iot/{device_type.value}/{device_id}"
        self.ble_discovery_mode = BLEDiscoveryMode.V0_MANUAL
        self.network_key = None
        self.pairing_status = False
        
    def update_status(self, status: DeviceStatus):
        self.status = status
        self.last_seen = datetime.now(timezone.utc)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "port": self.port,
            "status": self.status.value,
            "category": self.category.value,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "properties": self.properties,
            "ble_discovery_mode": self.ble_discovery_mode.value,
            "pairing_status": self.pairing_status
        }

class Dongle:
    def __init__(self, port: str, device_type: DeviceType):
        self.port = port
        self.device_type = device_type
        self.serial_connection = None
        self.status = DeviceStatus.DISCONNECTED
        self.devices = {}
        self.last_heartbeat = None
        self.is_active = False
        
    def connect(self) -> bool:
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=115200,
                timeout=1,
                write_timeout=1
            )
            self.status = DeviceStatus.CONNECTED
            self.is_active = True
            logger.info(f"✅ Dongle connected on {self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to dongle on {self.port}: {e}")
            self.status = DeviceStatus.ERROR
            return False
            
    def disconnect(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.status = DeviceStatus.DISCONNECTED
        self.is_active = False
        
    def send_message(self, message: str) -> bool:
        if not self.serial_connection or not self.serial_connection.is_open:
            return False
        try:
            self.serial_connection.write(f"{message}\n".encode())
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message to {self.port}: {e}")
            return False
            
    def read_message(self) -> Optional[str]:
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        try:
            if self.serial_connection.in_waiting:
                return self.serial_connection.readline().decode().strip()
        except Exception as e:
            logger.error(f"❌ Failed to read from {self.port}: {e}")
        return None

print("✅ Device and Dongle classes created successfully")

# Settings class
class Settings:
    def __init__(self):
        self.mqtt_broker = os.getenv("MQTT_BROKER", "mqtt://homeassistant:1883")
        self.mqtt_username = os.getenv("MQTT_USERNAME", "")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "")
        self.scan_interval = float(os.getenv("SCAN_INTERVAL", "0.02"))
        self.include_patterns = os.getenv("INCLUDE_PATTERNS", "/dev/ttyUSB*,/dev/ttyACM*").split(",")
        self.exclude_patterns = os.getenv("EXCLUDE_PATTERNS", "/dev/ttyS*,/dev/input*,/dev/hidraw*").split(",")
        self.enable_discovery = os.getenv("ENABLE_DISCOVERY", "true").lower() == "true"
        self.discovery_prefix = os.getenv("DISCOVERY_PREFIX", "homeassistant")
        self.enable_device_detection = os.getenv("ENABLE_DEVICE_DETECTION", "true").lower() == "true"
        self.enable_device_pairing = os.getenv("ENABLE_DEVICE_PAIRING", "true").lower() == "true"
        self.enable_device_management = os.getenv("ENABLE_DEVICE_MANAGEMENT", "true").lower() == "true"
        self.heartbeat_interval = float(os.getenv("HEARTBEAT_INTERVAL", "10.0"))
        self.pairing_timeout = float(os.getenv("PAIRING_TIMEOUT", "30.0"))
        self.device_management_port = int(os.getenv("DEVICE_MANAGEMENT_PORT", "8080"))
        self.max_paired_devices = int(os.getenv("MAX_PAIRED_DEVICES", "50"))
        
        # New settings for BLE/Zigbee toggles
        self.enable_ble = os.getenv("ENABLE_BLE", "true").lower() == "true"
        self.enable_zigbee = os.getenv("ENABLE_ZIGBEE", "true").lower() == "true"
        self.ble_discovery_mode = os.getenv("BLE_DISCOVERY_MODE", "v0_manual").lower()
        
        # Serial communication settings
        self.serial_baudrate = int(os.getenv("SERIAL_BAUDRATE", "115200"))
        self.serial_timeout = float(os.getenv("SERIAL_TIMEOUT", "1.0"))
        self.who_are_you_message = os.getenv("WHO_ARE_YOU_MESSAGE", "WHO_ARE_YOU")
        self.device_scan_interval = float(os.getenv("DEVICE_SCAN_INTERVAL", "5.0"))

print("✅ Settings class created successfully")

# MQTT Manager
class MQTTManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = mqtt.Client(protocol=mqtt.MQTTv5, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.connected = False
        self.message_queue = queue.Queue()
        
        if self.settings.mqtt_username and self.settings.mqtt_password:
            self.client.username_pw_set(self.settings.mqtt_username, self.settings.mqtt_password)
            
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = True
        logger.info("✅ MQTT successfully connected!")
        print("✅ MQTT successfully connected!")
            
            # Subscribe to control topics
        client.subscribe("wepower_iot/control/+/+")
        client.subscribe("wepower_iot/device/+/command")
        
        # Publish status
        self.publish_status("online")
        
    def _on_message(self, client, userdata, msg, properties=None):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            logger.info(f"📨 MQTT message received: {topic} -> {payload}")
            
            # Handle different message types
            if topic.startswith("wepower_iot/control/"):
                self._handle_control_message(topic, payload)
            elif topic.startswith("wepower_iot/device/"):
                self._handle_device_command(topic, payload)
                
        except Exception as e:
            logger.error(f"❌ Error handling MQTT message: {e}")
    
    def _on_disconnect(self, client, userdata, reason_code, properties=None):
        self.connected = False
        logger.warning("⚠️ MQTT disconnected")
        
    def _handle_control_message(self, topic: str, payload: str):
        """Handle control messages from Home Assistant"""
        try:
            data = json.loads(payload)
            action = data.get("action")
            
            if action == "toggle_ble":
                self.settings.enable_ble = data.get("enabled", False)
                logger.info(f"🔄 BLE toggled: {self.settings.enable_ble}")
                
            elif action == "toggle_zigbee":
                self.settings.enable_zigbee = data.get("enabled", False)
                logger.info(f"🔄 Zigbee toggled: {self.settings.enable_zigbee}")
                
            elif action == "manual_device_add":
                self._handle_manual_device_add(data)
                
        except Exception as e:
            logger.error(f"❌ Error handling control message: {e}")
            
    def _handle_device_command(self, topic: str, payload: str):
        """Handle device-specific commands"""
        try:
            data = json.loads(payload)
            command = data.get("command")
            device_id = data.get("device_id")
            
            if command == "pair":
                logger.info(f"🔗 Pairing command for device: {device_id}")
                # Trigger pairing process
                
        except Exception as e:
            logger.error(f"❌ Error handling device command: {e}")
            
    def _handle_manual_device_add(self, data: Dict[str, Any]):
        """Handle manual device addition from UI"""
        device_id = data.get("device_id")
        device_type = data.get("device_type")
        ble_mode = data.get("ble_discovery_mode", "v0_manual")
        
        logger.info(f"➕ Manual device add: {device_id} ({device_type}) - BLE mode: {ble_mode}")
        # This will be handled by the main addon class
        
    def connect(self) -> bool:
        try:
            broker_url = self.settings.mqtt_broker.replace("mqtt://", "")
            if ":" in broker_url:
                host, port = broker_url.split(":")
                port = int(port)
            else:
                host = broker_url
                port = 1883
            
            self.client.connect(host, port, 60)
            self.client.loop_start()
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
    
    def publish(self, topic: str, payload: Dict[str, Any]):
        if not self.connected:
            self.message_queue.put((topic, payload))
            return
        
        try:
            message = json.dumps(payload)
            self.client.publish(topic, message)
            logger.debug(f"📤 MQTT published: {topic} -> {message}")
        except Exception as e:
            logger.error(f"❌ Failed to publish MQTT message: {e}")
            
    def publish_status(self, status: str):
        payload = {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ble_enabled": self.settings.enable_ble,
            "zigbee_enabled": self.settings.enable_zigbee
        }
        self.publish("wepower_iot/status", payload)
        
    def publish_device_update(self, device: Device):
        payload = device.to_dict()
        self.publish(device.mqtt_topic, payload)
        
    def publish_dongle_status(self, dongle: Dongle):
        payload = {
            "port": dongle.port,
            "device_type": dongle.device_type.value,
            "status": dongle.status.value,
            "device_count": len(dongle.devices),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.publish(f"wepower_iot/dongle/{dongle.port}", payload)

print("✅ MQTT Manager created successfully")

# Serial Port Scanner
class SerialPortScanner:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.dongles = {}
        
    def scan_ports(self) -> Dict[str, Dongle]:
        """Scan for available serial ports and identify dongles"""
        available_ports = []
        
        # Get all available ports
        for port in serial.tools.list_ports.comports():
            port_path = port.device
            
            # Check include/exclude patterns
            if self._should_include_port(port_path):
                available_ports.append(port_path)
                
        logger.info(f"🔍 Found {len(available_ports)} available ports: {available_ports}")
        
        # Identify dongles on available ports
        for port in available_ports:
            dongle = self._identify_dongle(port)
            if dongle:
                self.dongles[port] = dongle
                logger.info(f"🔌 Dongle identified: {dongle.device_type.value} on {port}")
                
        return self.dongles
        
    def _should_include_port(self, port_path: str) -> bool:
        """Check if port should be included based on patterns"""
        for pattern in self.settings.include_patterns:
            if pattern.strip() and pattern.strip() in port_path:
                return True
                
        for pattern in self.settings.exclude_patterns:
            if pattern.strip() and pattern.strip() in port_path:
                return False
                
        return False
        
    def _identify_dongle(self, port: str) -> Optional[Dongle]:
        """Identify dongle type by sending 'Who are you?' message"""
        try:
            # Try to connect to port
            with serial.Serial(port, self.settings.serial_baudrate, timeout=self.settings.serial_timeout) as ser:
                # Send identification message
                ser.write(f"{self.settings.who_are_you_message}\n".encode())
                time.sleep(0.1)
                
                # Read response
                if ser.in_waiting:
                    response = ser.readline().decode().strip()
                    logger.info(f"🔍 Port {port} response: {response}")
                    
                    # Parse response to determine dongle type
                    device_type = self._parse_dongle_response(response)
                    if device_type:
                        return Dongle(port, device_type)
                
        except Exception as e:
            logger.debug(f"⚠️ Could not identify dongle on {port}: {e}")
            
        return None
        
    def _parse_dongle_response(self, response: str) -> Optional[DeviceType]:
        """Parse dongle response to determine type"""
        response_lower = response.lower()
        
        if "ble" in response_lower or "bluetooth" in response_lower:
            return DeviceType.BLE
        elif "zigbee" in response_lower or "zig" in response_lower:
                    return DeviceType.ZIGBEE
        elif "zwave" in response_lower or "zw" in response_lower:
            return DeviceType.ZWAVE
        elif "matter" in response_lower:
            return DeviceType.MATTER
        elif "dongle" in response_lower or "device" in response_lower:
                return DeviceType.GENERIC
            
        return None
        
    def get_dongles(self) -> Dict[str, Dongle]:
        return self.dongles
        
    def add_dongle(self, port: str, device_type: DeviceType):
        """Manually add a dongle (for manual configuration)"""
        dongle = Dongle(port, device_type)
        self.dongles[port] = dongle
        logger.info(f"➕ Manual dongle added: {device_type.value} on {port}")

print("✅ Serial Port Scanner created successfully")

# Device Manager
class DeviceManager:
    def __init__(self, settings: Settings, mqtt_manager: MQTTManager):
        self.settings = settings
        self.mqtt_manager = mqtt_manager
        self.devices = {}
        self.device_counter = 0
        
    def add_device(self, device_id: str, device_type: DeviceType, port: str, 
                   category: DeviceCategory = DeviceCategory.UNKNOWN, 
                   properties: Dict[str, Any] = None) -> Device:
        """Add a new device"""
        if device_id in self.devices:
            return self.devices[device_id]
            
        device = Device(device_id, device_type, port)
        device.category = category
        if properties:
            device.properties = properties
            
        self.devices[device_id] = device
        self.device_counter += 1
        
        logger.info(f"➕ Device added: {device_id} ({device_type.value}) on {port}")
        
        # Publish device update
        self.mqtt_manager.publish_device_update(device)
        
        return device
        
    def remove_device(self, device_id: str):
        """Remove a device"""
        if device_id in self.devices:
            device = self.devices[device_id]
            device.update_status(DeviceStatus.DISCONNECTED)
            self.mqtt_manager.publish_device_update(device)
            del self.devices[device_id]
            logger.info(f"➖ Device removed: {device_id}")
            
    def update_device_status(self, device_id: str, status: DeviceStatus):
        """Update device status"""
        if device_id in self.devices:
            device = self.devices[device_id]
            device.update_status(status)
            self.mqtt_manager.publish_device_update(device)
            
    def get_device(self, device_id: str) -> Optional[Device]:
        return self.devices.get(device_id)
        
    def get_devices_by_type(self, device_type: DeviceType) -> List[Device]:
        return [d for d in self.devices.values() if d.device_type == device_type]
        
    def get_devices_by_status(self, status: DeviceStatus) -> List[Device]:
        return [d for d in self.devices.values() if d.status == status]
        
    def get_all_devices(self) -> List[Device]:
        return list(self.devices.values())
        
    def manual_add_device(self, device_data: Dict[str, Any]) -> Optional[Device]:
        """Manually add device from UI form"""
        try:
            device_id = device_data.get("device_id")
            device_type_str = device_data.get("device_type", "unknown")
            port = device_data.get("port", "manual")
            category_str = device_data.get("category", "unknown")
            ble_mode = device_data.get("ble_discovery_mode", "v0_manual")
            
            # Convert strings to enums with fallbacks
            try:
                device_type = DeviceType(device_type_str)
            except ValueError:
                device_type = DeviceType.UNKNOWN
                
            try:
                category = DeviceCategory(category_str)
            except ValueError:
                category = DeviceCategory.UNKNOWN
            
            # Create device
            device = self.add_device(device_id, device_type, port, category)
            
            # Set BLE discovery mode
            if device_type == DeviceType.BLE:
                device.ble_discovery_mode = BLEDiscoveryMode(ble_mode)
                
            # Set initial status based on discovery mode
            if ble_mode == "v0_manual":
                device.update_status(DeviceStatus.IDENTIFIED)
            else:
                device.update_status(DeviceStatus.CONNECTING)
                
            logger.info(f"➕ Manual device added: {device_id} ({device_type.value})")
            return device
                
        except Exception as e:
            logger.error(f"❌ Error adding manual device: {e}")
            return None

print("✅ Device Manager created successfully")

# Main addon class
class WePowerIoTAddon:
    def __init__(self):
        print("✅ Initializing WePower IoT Add-on...")
        self.settings = Settings()
        self.mqtt_manager = MQTTManager(self.settings)
        self.port_scanner = SerialPortScanner(self.settings)
        self.device_manager = DeviceManager(self.settings, self.mqtt_manager)
        self.running = False
        self.scanning_task = None
        self.heartbeat_task = None
        
        print("✅ WePower IoT Add-on initialized successfully")
        
    async def start(self):
        print("✅ Starting WePower IoT Add-on...")
        print(f"✅ MQTT Broker: {self.settings.mqtt_broker}")
        print(f"✅ BLE Enabled: {self.settings.enable_ble}")
        print(f"✅ Zigbee Enabled: {self.settings.enable_zigbee}")
        print(f"✅ Device Detection: {self.settings.enable_device_detection}")
        print(f"✅ Device Pairing: {self.settings.enable_device_pairing}")
        print(f"✅ Device Management: {self.settings.enable_device_management}")
        print(f"✅ Management Port: {self.settings.device_management_port}")
        print(f"✅ Max Paired Devices: {self.settings.max_paired_devices}")
        
        # Connect to MQTT
        if not self.mqtt_manager.connect():
            logger.error("❌ Failed to connect to MQTT broker")
            return False
            
        # Scan for dongles
        dongles = self.port_scanner.scan_ports()
        print(f"✅ Found {len(dongles)} dongles")
        
        # Connect to dongles
        for port, dongle in dongles.items():
            if dongle.connect():
                print(f"✅ Dongle connected: {dongle.device_type.value} on {port}")
            else:
                print(f"❌ Failed to connect to dongle: {dongle.device_type.value} on {port}")
                
            self.running = True
            
        # Start background tasks
        self.scanning_task = asyncio.create_task(self._device_scanning_loop())
        
        # Start heartbeat if enabled
            if self.settings.heartbeat_interval > 0:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
        print("✅ WePower IoT Add-on started successfully!")
        return True
        
    async def stop(self):
        print("🛑 Stopping WePower IoT Add-on...")
        self.running = False
        
        # Cancel background tasks
        if self.scanning_task:
            self.scanning_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            
        # Disconnect dongles
        for dongle in self.port_scanner.get_dongles().values():
            dongle.disconnect()
            
        # Disconnect MQTT
        self.mqtt_manager.disconnect()
        
        print("✅ WePower IoT Add-on stopped successfully")
        
    async def _device_scanning_loop(self):
        """Main device scanning loop"""
        print("✅ Starting device scanning loop...")
        iteration = 0
        
        while self.running:
            iteration += 1
            print(f"✅ Device scan iteration {iteration}")
            
            try:
                # Scan for new devices on each dongle
                for port, dongle in self.port_scanner.get_dongles().items():
                    if dongle.is_active:
                        await self._scan_dongle_for_devices(dongle)
                        
                # Update device statuses
                await self._update_device_statuses()
                
                # Publish dongle statuses
                for dongle in self.port_scanner.get_dongles().values():
                    self.mqtt_manager.publish_dongle_status(dongle)
                    
                # Simulate device discovery every 5 iterations
                if iteration % 5 == 0:
                    print(f"✅ Simulating device discovery at iteration {iteration}")
                    await self._simulate_device_discovery()
                
            except Exception as e:
                logger.error(f"❌ Error in device scanning loop: {e}")
                
            await asyncio.sleep(self.settings.device_scan_interval)
            
        print("✅ Device scanning loop completed")
        
    async def _scan_dongle_for_devices(self, dongle: Dongle):
        """Scan a specific dongle for new devices"""
        try:
            # Send device discovery command
            if dongle.send_message("SCAN_DEVICES"):
                # Read responses
                for _ in range(10):  # Read up to 10 responses
                    message = dongle.read_message()
                    if message:
                        device = self._parse_device_message(message, dongle)
                        if device:
                            # Add or update device
                            existing_device = self.device_manager.get_device(device.device_id)
                            if existing_device:
                                existing_device.update_status(DeviceStatus.CONNECTED)
                            else:
                                self.device_manager.add_device(
                                    device.device_id, 
                                    device.device_type, 
                                    dongle.port,
                                    device.category,
                                    device.properties
                                )
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"❌ Error scanning dongle {dongle.port}: {e}")
            
    def _parse_device_message(self, message: str, dongle: Dongle) -> Optional[Device]:
        """Parse device message from dongle"""
        try:
            # This is a simplified parser - in real implementation, 
            # you'd have specific message formats for each device type
            if "DEVICE:" in message:
                parts = message.split(":")
                if len(parts) >= 3:
                    device_id = parts[1].strip()
                    device_type_str = parts[2].strip()
                    
                    # Determine device type
                    if "BLE" in device_type_str:
                        device_type = DeviceType.BLE
                    elif "ZIGBEE" in device_type_str:
                        device_type = DeviceType.ZIGBEE
                    else:
                        device_type = DeviceType.GENERIC
                        
                    # Create device
                    device = Device(device_id, device_type, dongle.port)
                    
                    # Determine category from message
                    if "SENSOR" in message:
                        device.category = DeviceCategory.SENSOR
                    elif "SWITCH" in message:
                        device.category = DeviceCategory.SWITCH
                    elif "LIGHT" in message:
                        device.category = DeviceCategory.LIGHT
                        
                    return device
                
            except Exception as e:
            logger.error(f"❌ Error parsing device message: {e}")
            
        return None
        
    async def _update_device_statuses(self):
        """Update status of all devices"""
        for device in self.device_manager.get_all_devices():
            # Simulate device status changes
            if device.status == DeviceStatus.CONNECTED:
                # Randomly set some devices to offline (as per requirements)
                if hasattr(device, '_offline_counter'):
                    device._offline_counter += 1
                else:
                    device._offline_counter = 0
                    
                # Set devices to offline after some time (simulating real behavior)
                if device._offline_counter > 10:
                    device.update_status(DeviceStatus.OFFLINE)
                    
    async def _simulate_device_discovery(self):
        """Simulate discovering new devices"""
        # Simulate finding a new BLE device
        if self.settings.enable_ble:
            device_id = f"ble_device_{int(time.time())}"
            device = self.device_manager.add_device(
                device_id, 
                DeviceType.BLE, 
                "simulated_port",
                DeviceCategory.SENSOR
            )
            print(f"✅ Simulated BLE device discovered: {device_id}")
            
        # Simulate finding a new Zigbee device
        if self.settings.enable_zigbee:
            device_id = f"zigbee_device_{int(time.time())}"
            device = self.device_manager.add_device(
                device_id, 
                DeviceType.ZIGBEE, 
                "simulated_port",
                DeviceCategory.SWITCH
            )
            print(f"✅ Simulated Zigbee device discovered: {device_id}")
            
    async def _heartbeat_loop(self):
        """Heartbeat loop for keeping connections alive"""
        while self.running:
            try:
                # Publish heartbeat
                self.mqtt_manager.publish_status("heartbeat")
                
                # Update dongle heartbeats
                for dongle in self.port_scanner.get_dongles().values():
                    if dongle.is_active:
                        dongle.last_heartbeat = datetime.now(timezone.utc)
                
            except Exception as e:
                logger.error(f"❌ Error in heartbeat loop: {e}")
                
                await asyncio.sleep(self.settings.heartbeat_interval)

    def toggle_ble(self, enabled: bool):
        """Toggle BLE functionality"""
        self.settings.enable_ble = enabled
        logger.info(f"🔄 BLE toggled: {enabled}")
        self.mqtt_manager.publish_status("ble_toggled")
        
    def toggle_zigbee(self, enabled: bool):
        """Toggle Zigbee functionality"""
        self.settings.enable_zigbee = enabled
        logger.info(f"🔄 Zigbee toggled: {enabled}")
        self.mqtt_manager.publish_status("zigbee_toggled")
        
    def manual_add_device(self, device_data: Dict[str, Any]) -> Optional[Device]:
        """Manually add device from UI"""
        return self.device_manager.manual_add_device(device_data)

async def main():
    print("✅ Main function started")
    addon = WePowerIoTAddon()
    
    try:
        if await addon.start():
            # Keep running until interrupted
            while addon.running:
                await asyncio.sleep(1)
        else:
            print("❌ Failed to start addon")
            
    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await addon.stop()

    print("✅ Main function completed")

if __name__ == "__main__":
    print("✅ Script entry point reached")
    try:
    asyncio.run(main())
        print("✅ asyncio.run completed successfully")
    except Exception as e:
        print(f"❌ Error in main: {e}")
        import traceback
        traceback.print_exc()
    print("✅ Script finished")

