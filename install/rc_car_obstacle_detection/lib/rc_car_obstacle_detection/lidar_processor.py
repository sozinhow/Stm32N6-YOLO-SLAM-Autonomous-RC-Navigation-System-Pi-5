#!/usr/bin/env python3
"""
LiDAR Processor Node for ROS 2 Jazzy
Processes LiDAR scan data from cspc_lidar_sdk_ros2 to detect obstacles
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, PointCloud2, PointField
from std_msgs.msg import Bool, Float32, Header
import numpy as np
import math
import struct


class LidarProcessor(Node):
    def __init__(self):
        super().__init__('lidar_processor')

        # Parameters
        self.declare_parameter('detection_distance', 1.5)  # meters
        self.declare_parameter('detection_angle', 60.0)    # degrees (±30°)
        self.declare_parameter('min_points_threshold', 5)
        self.declare_parameter('scan_topic', '/scan')      # Topic from cspc_lidar
        self.declare_parameter('publish_obstacle_cloud', True)  # For costmap

        self.detection_dist = self.get_parameter('detection_distance').value
        self.detection_angle = math.radians(self.get_parameter('detection_angle').value)
        self.min_points = self.get_parameter('min_points_threshold').value
        scan_topic = self.get_parameter('scan_topic').value
        self.publish_cloud = self.get_parameter('publish_obstacle_cloud').value

        # Publishers
        self.obstacle_pub = self.create_publisher(Bool, 'lidar/obstacle_detected', 10)
        self.distance_pub = self.create_publisher(Float32, 'lidar/closest_distance', 10)
        self.cloud_pub = self.create_publisher(PointCloud2, 'lidar/obstacle_points', 10)

        # Subscribers
        self.scan_sub = self.create_subscription(
            LaserScan, scan_topic, self.scan_callback, 10)

        self.get_logger().info(f'LiDAR Processor initialized, subscribing to {scan_topic}')

    def scan_callback(self, scan_msg):
        """Process LiDAR scan data"""
        # Extract points in detection zone (front cone)
        angles = np.arange(
            scan_msg.angle_min,
            scan_msg.angle_max + scan_msg.angle_increment,
            scan_msg.angle_increment
        )
        ranges = np.array(scan_msg.ranges)

        # Ensure arrays are same length
        min_len = min(len(angles), len(ranges))
        angles = angles[:min_len]
        ranges = ranges[:min_len]

        # Filter invalid readings
        valid_mask = (ranges > scan_msg.range_min) & (ranges < scan_msg.range_max)

        # Filter by angle (front cone) - handle wraparound at 0/360
        # Normalize angles to [-pi, pi]
        angles_normalized = np.arctan2(np.sin(angles), np.cos(angles))
        angle_mask = np.abs(angles_normalized) < (self.detection_angle / 2)

        # Filter by distance
        distance_mask = ranges < self.detection_dist

        # Combine filters
        detection_mask = valid_mask & angle_mask & distance_mask

        detected_points = np.sum(detection_mask)

        # Determine if obstacle exists
        obstacle_detected = bool(detected_points >= self.min_points)

        # Find closest point
        if detected_points > 0:
            closest_distance = float(np.min(ranges[detection_mask]))
        else:
            closest_distance = float('inf')

        # Publish results
        obstacle_msg = Bool()
        obstacle_msg.data = bool(obstacle_detected)
        self.obstacle_pub.publish(obstacle_msg)

        distance_msg = Float32()
        distance_msg.data = closest_distance if closest_distance != float('inf') else -1.0
        self.distance_pub.publish(distance_msg)

        # Publish obstacle point cloud for costmap
        if self.publish_cloud and detected_points > 0:
            cloud_msg = self.create_point_cloud(scan_msg, detection_mask, angles, ranges)
            self.cloud_pub.publish(cloud_msg)

        if obstacle_detected:
            self.get_logger().info(
                f'Obstacle detected! Distance: {closest_distance:.2f}m, Points: {detected_points}',
                throttle_duration_sec=1.0)

    def create_point_cloud(self, scan_msg, mask, angles, ranges):
        """Convert detected obstacle points to PointCloud2"""
        # Extract obstacle points
        obstacle_angles = angles[mask]
        obstacle_ranges = ranges[mask]

        # Convert to Cartesian coordinates
        points = []
        for angle, r in zip(obstacle_angles, obstacle_ranges):
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            z = 0.0  # 2D LiDAR
            points.append([x, y, z])

        # Create PointCloud2 message
        header = Header()
        header.stamp = scan_msg.header.stamp
        header.frame_id = scan_msg.header.frame_id

        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]

        cloud_msg = PointCloud2()
        cloud_msg.header = header
        cloud_msg.height = 1
        cloud_msg.width = len(points)
        cloud_msg.fields = fields
        cloud_msg.is_bigendian = False
        cloud_msg.point_step = 12  # 3 floats * 4 bytes
        cloud_msg.row_step = cloud_msg.point_step * len(points)
        cloud_msg.is_dense = True

        # Pack point data
        buffer = []
        for point in points:
            buffer.append(struct.pack('fff', point[0], point[1], point[2]))
        cloud_msg.data = b''.join(buffer)

        return cloud_msg


def main(args=None):
    rclpy.init(args=args)
    node = LidarProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
