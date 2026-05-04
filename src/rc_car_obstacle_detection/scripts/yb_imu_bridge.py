#!/usr/bin/env python3
"""
YB-MRA02 九轴 IMU -> ROS2 /imu 话题桥接节点
直接输出四元数姿态 + 角速度 + 线加速度
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import Imu
from YbImuLib import YbImuSerial

SERIAL_PORT = "/dev/ttyUSB1"
PUBLISH_RATE = 100.0  # Hz


class YbImuBridge(Node):
    def __init__(self):
        super().__init__("yb_imu_bridge")

        # 初始化 IMU 串口
        self.imu_dev = YbImuSerial(SERIAL_PORT, debug=False)
        self.imu_dev.create_receive_threading()
        self.get_logger().info(f"Connected to YB-MRA02 on {SERIAL_PORT}")

        # Sensor QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # 发布者
        self.pub = self.create_publisher(Imu, "/imu", sensor_qos)

        # 定时器
        self.timer = self.create_timer(1.0 / PUBLISH_RATE, self.publish_imu)

        # 重力常量
        self.G = 9.80665

    def publish_imu(self):
        try:
            ax, ay, az = self.imu_dev.get_accelerometer_data()
            gx, gy, gz = self.imu_dev.get_gyroscope_data()
            qw, qx, qy, qz = self.imu_dev.get_imu_quaternion_data()

            msg = Imu()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "imu_link"

            msg.orientation.w = float(qw)
            msg.orientation.x = float(qx)
            msg.orientation.y = float(qy)
            msg.orientation.z = float(qz)
            msg.orientation_covariance[0] = 0.01
            msg.orientation_covariance[4] = 0.01
            msg.orientation_covariance[8] = 0.01

            msg.angular_velocity.x = float(gx)
            msg.angular_velocity.y = float(gy)
            msg.angular_velocity.z = float(gz)
            msg.angular_velocity_covariance[0] = 0.001
            msg.angular_velocity_covariance[4] = 0.001
            msg.angular_velocity_covariance[8] = 0.001

            msg.linear_acceleration.x = float(ax) * self.G
            msg.linear_acceleration.y = float(ay) * self.G
            msg.linear_acceleration.z = float(az) * self.G
            msg.linear_acceleration_covariance[0] = 0.01
            msg.linear_acceleration_covariance[4] = 0.01
            msg.linear_acceleration_covariance[8] = 0.01

            self.pub.publish(msg)

        except Exception as e:
            self.get_logger().warn(f"IMU read error: {e}", throttle_duration_sec=2.0)


def main(args=None):
    rclpy.init(args=args)
    node = YbImuBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()