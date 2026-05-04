#!/usr/bin/env python3
"""
STM32N6 Bridge Node for ROS 2 Jazzy
Handles UART communication with STM32N6 for manual control commands
Subscribes to existing imu_uart_node for IMU data
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import serial
import threading


class STM32Bridge(Node):
    def __init__(self):
        super().__init__('stm32_bridge')

        # Parameters
        self.declare_parameter('serial_port', '/dev/ttyAMA0')
        self.declare_parameter('baud_rate', 115200)

        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value

        # Publishers
        self.stm32_status_pub = self.create_publisher(String, 'stm32/status', 10)

        # Subscribers
        self.cmd_sub = self.create_subscription(
            String, 'stm32/command', self.command_callback, 10)
        self.emergency_sub = self.create_subscription(
            Bool, 'emergency_stop', self.emergency_callback, 10)

        # Serial connection
        try:
            self.serial = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f'Connected to STM32 on {port}')
        except Exception as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            raise

        # Start serial reader thread
        self.running = True
        self.reader_thread = threading.Thread(target=self.serial_reader, daemon=True)
        self.reader_thread.start()

        self.get_logger().info('STM32 Bridge initialized')

    def serial_reader(self):
        """Background thread to read serial data from STM32"""
        buffer = ""
        while self.running:
            try:
                if self.serial.in_waiting:
                    data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data

                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        self.process_line(line.strip())
            except Exception as e:
                self.get_logger().error(f'Serial read error: {e}')

    def process_line(self, line):
        """Parse incoming serial data from STM32"""
        if line.startswith('['):
            # Status messages from STM32
            msg = String()
            msg.data = line
            self.stm32_status_pub.publish(msg)
            self.get_logger().info(f'STM32: {line}')

    def command_callback(self, msg):
        """Send command to STM32"""
        try:
            cmd = msg.data.strip()
            if len(cmd) == 1:
                self.serial.write(cmd.encode())
                self.get_logger().debug(f'Sent command: {cmd}')
        except Exception as e:
            self.get_logger().error(f'Failed to send command: {e}')

    def emergency_callback(self, msg):
        """Handle emergency stop"""
        if msg.data:
            self.serial.write(b'p')  # Stop motor
            self.get_logger().warn('EMERGENCY STOP ACTIVATED')

    def destroy_node(self):
        self.running = False
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = STM32Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
