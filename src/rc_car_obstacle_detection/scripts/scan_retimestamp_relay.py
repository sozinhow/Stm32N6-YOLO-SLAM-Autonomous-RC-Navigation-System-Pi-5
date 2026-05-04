#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
激光雷达时间戳修正与转发节点
功能：将 /scan 的时间戳更新为当前 ROS 系统时间，并统一坐标系名称
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import LaserScan

# --- 配置常量 ---
INPUT_TOPIC = '/scan'
OUTPUT_TOPIC = '/scan_fixed'
TARGET_FRAME_ID = 'laser_link'


class ScanRetimestampRelay(Node):
    def __init__(self):
        super().__init__('scan_retimestamp_relay')

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # 订阅用默认 QoS（兼容雷达驱动）
        self.sub = self.create_subscription(
            LaserScan,
            INPUT_TOPIC,
            self.scan_callback,
            10
        )

        # 发布用 sensor QoS（防止数据积压）
        self.pub = self.create_publisher(
            LaserScan,
            OUTPUT_TOPIC,
            sensor_qos
        )

        self.get_logger().info(f'已启动转发节点: {INPUT_TOPIC} -> {OUTPUT_TOPIC}')

    def scan_callback(self, msg: LaserScan):
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = TARGET_FRAME_ID
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ScanRetimestampRelay()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('用户手动停止节点')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()