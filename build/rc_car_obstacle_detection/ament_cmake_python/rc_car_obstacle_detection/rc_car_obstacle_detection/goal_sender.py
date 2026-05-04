#!/usr/bin/env python3
"""
Simple Goal Sender for RC Car
Sends navigation goals based on map coordinates
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import sys
import math


class GoalSender(Node):

    def __init__(self):
        super().__init__('goal_sender')

        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.status_sub = self.create_subscription(
            String,
            '/navigation_status',
            self.status_callback,
            10
        )

        self.get_logger().info('Goal Sender initialized')
        self.get_logger().info(
            'Usage: ros2 run rc_car_obstacle_detection goal_sender.py X Y YAW'
        )

    def status_callback(self, msg):
        self.get_logger().info(f'Navigation status: {msg.data}')

    def send_goal(self, x, y, yaw):
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.position.z = 0.0

        # Convert yaw to quaternion
        goal.pose.orientation.z = math.sin(float(yaw) / 2.0)
        goal.pose.orientation.w = math.cos(float(yaw) / 2.0)

        self.goal_pub.publish(goal)
        self.get_logger().info(f'Sent goal: x={x}, y={y}, yaw={yaw}')


def main():
    rclpy.init()
    node = GoalSender()

    if len(sys.argv) >= 4:
        x = sys.argv[1]
        y = sys.argv[2]
        yaw = sys.argv[3]

        node.send_goal(x, y, yaw)
        rclpy.spin_once(node, timeout_sec=1.0)
    else:
        node.get_logger().error('Usage: goal_sender.py X Y YAW')
        node.get_logger().info('Example: goal_sender.py 2.0 1.0 0.0')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
