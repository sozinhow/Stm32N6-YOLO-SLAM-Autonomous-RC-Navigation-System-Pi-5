#!/usr/bin/env python3
"""
Obstacle Fusion Node for ROS 2 Jazzy
Fuses obstacle detection from:
1. STM32 YOLO vision (person detection via status messages)
2. LiDAR proximity detection

Outputs unified emergency stop signal
Note: IMU is used for odometry/SLAM only, NOT for tilt detection
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String, Float32
import time


class ObstacleFusion(Node):
    def __init__(self):
        super().__init__('obstacle_fusion')

        # Parameters
        self.declare_parameter('lidar_timeout', 0.5)      # seconds
        self.declare_parameter('vision_timeout', 1.0)     # seconds
        self.declare_parameter('emergency_cooldown', 2.0) # seconds

        self.lidar_timeout = self.get_parameter('lidar_timeout').value
        self.vision_timeout = self.get_parameter('vision_timeout').value
        self.cooldown_time = self.get_parameter('emergency_cooldown').value

        # State tracking
        self.lidar_obstacle = False
        self.vision_person = False
        self.last_lidar_time = 0.0
        self.last_vision_time = 0.0
        self.last_emergency_time = 0.0
        self.closest_distance = float('inf')

        # Publishers
        self.emergency_pub = self.create_publisher(Bool, 'emergency_stop', 10)
        self.status_pub = self.create_publisher(String, 'fusion/status', 10)

        # Subscribers
        self.lidar_obs_sub = self.create_subscription(
            Bool, 'lidar/obstacle_detected', self.lidar_callback, 10)
        self.lidar_dist_sub = self.create_subscription(
            Float32, 'lidar/closest_distance', self.distance_callback, 10)
        self.stm32_status_sub = self.create_subscription(
            String, 'stm32/status', self.stm32_callback, 10)

        # Timer for fusion logic
        self.timer = self.create_timer(0.1, self.fusion_callback)

        self.get_logger().info('Obstacle Fusion initialized (LiDAR + Vision only)')

    def lidar_callback(self, msg):
        """LiDAR obstacle detection"""
        self.lidar_obstacle = msg.data
        self.last_lidar_time = time.time()

    def distance_callback(self, msg):
        """Closest obstacle distance"""
        self.closest_distance = msg.data if msg.data > 0 else float('inf')

    def stm32_callback(self, msg):
        """Parse STM32 status messages for person detection"""
        # Look for emergency stop indicators in STM32 messages
        if 'person' in msg.data.lower() or 'emergency' in msg.data.lower():
            self.vision_person = True
            self.last_vision_time = time.time()

    def fusion_callback(self):
        """Main fusion logic"""
        current_time = time.time()

        # Check for timeouts
        lidar_valid = (current_time - self.last_lidar_time) < self.lidar_timeout
        vision_valid = (current_time - self.last_vision_time) < self.vision_timeout

        # Reset vision flag if timeout
        if not vision_valid:
            self.vision_person = False

        # Determine emergency state
        emergency = False
        reason = []

        if self.vision_person and vision_valid:
            emergency = True
            reason.append('PERSON_DETECTED')

        if self.lidar_obstacle and lidar_valid:
            emergency = True
            reason.append(f'LIDAR_OBSTACLE({self.closest_distance:.2f}m)')

        # Publish emergency stop
        if emergency:
            if (current_time - self.last_emergency_time) > self.cooldown_time:
                self.last_emergency_time = current_time
                self.get_logger().warn(f'EMERGENCY STOP: {", ".join(reason)}')

            emergency_msg = Bool()
            emergency_msg.data = True
            self.emergency_pub.publish(emergency_msg)

        # Publish status
        status_msg = String()
        status_msg.data = (f'LiDAR:{self.lidar_obstacle} Vision:{self.vision_person} '
                          f'Dist:{self.closest_distance:.2f}m')
        self.status_pub.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleFusion()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
