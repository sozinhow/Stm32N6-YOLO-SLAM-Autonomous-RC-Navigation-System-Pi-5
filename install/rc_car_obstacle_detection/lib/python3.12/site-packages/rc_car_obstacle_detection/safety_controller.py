#!/usr/bin/env python3
"""
Safety Controller Node for ROS 2 Jazzy
Monitors system health and provides manual override capabilities
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
import sys
import select
import termios
import tty


class SafetyController(Node):
    def __init__(self):
        super().__init__('safety_controller')

        # Publishers
        self.emergency_pub = self.create_publisher(Bool, 'emergency_stop', 10)
        self.cmd_pub = self.create_publisher(String, 'stm32/command', 10)

        # Subscribers
        self.status_sub = self.create_subscription(
            String, 'fusion/status', self.status_callback, 10)

        # Terminal settings for keyboard input
        self.settings = termios.tcgetattr(sys.stdin)

        # Timer for keyboard check
        self.timer = self.create_timer(0.05, self.keyboard_callback)

        self.emergency_active = False

        self.print_help()
        self.get_logger().info('Safety Controller initialized')

    def print_help(self):
        """Print control instructions"""
        print("\n" + "="*60)
        print("RC CAR SAFETY CONTROLLER")
        print("="*60)
        print("STEERING:")
        print("  a - Turn left")
        print("  d - Turn right")
        print("  s - Center steering")
        print("\nMOTOR:")
        print("  1 - Low speed")
        print("  2 - Medium speed")
        print("  3 - High speed")
        print("  p - Stop")
        print("  b - Reverse")
        print("  f - Full forward (test)")
        print("\nSAFETY:")
        print("  SPACE - Emergency stop")
        print("  r - Reset emergency stop")
        print("  q - Quit")
        print("="*60 + "\n")

    def get_key(self):
        """Non-blocking keyboard input"""
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def keyboard_callback(self):
        """Check for keyboard input"""
        if select.select([sys.stdin], [], [], 0)[0]:
            key = self.get_key()

            if key == 'q':
                self.get_logger().info('Quitting...')
                raise KeyboardInterrupt

            elif key == ' ':
                # Emergency stop
                self.emergency_active = True
                emergency_msg = Bool()
                emergency_msg.data = True
                self.emergency_pub.publish(emergency_msg)
                self.get_logger().warn('MANUAL EMERGENCY STOP')

            elif key == 'r':
                # Reset emergency
                self.emergency_active = False
                emergency_msg = Bool()
                emergency_msg.data = False
                self.emergency_pub.publish(emergency_msg)
                self.get_logger().info('Emergency stop reset')

            elif key in ['a', 'd', 's', '1', '2', '3', 'p', 'b', 'f']:
                # Send command to STM32
                if not self.emergency_active:
                    cmd_msg = String()
                    cmd_msg.data = key
                    self.cmd_pub.publish(cmd_msg)
                    self.get_logger().info(f'Command sent: {key}')
                else:
                    self.get_logger().warn('Commands blocked - emergency stop active')

    def status_callback(self, msg):
        """Display system status"""
        self.get_logger().info(f'Status: {msg.data}', throttle_duration_sec=2.0)

    def destroy_node(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SafetyController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
