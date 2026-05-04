#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import LaserScan


class RF2OWrapper(Node):
    def __init__(self):
        super().__init__('rf2o_wrapper')

        # QoS 配置 - 使用 RELIABLE 和较大的 history
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos
        )

        self.scan_pub = self.create_publisher(
            LaserScan,
            '/scan_converted',
            qos
        )

        self.get_logger().info('RF2O Wrapper started')

    def scan_callback(self, msg):
        self.scan_pub.publish(msg)


def main():
    rclpy.init()
    node = RF2OWrapper()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
