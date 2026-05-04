#!/usr/bin/env python3
"""
Costmap Publisher Node for ROS 2 Jazzy
Publishes detected obstacles to costmap for navigation integration
Combines LiDAR obstacle points and vision-detected persons
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import String, Header
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
import struct
import numpy as np


class CostmapPublisher(Node):
    def __init__(self):
        super().__init__('costmap_publisher')

        # Parameters
        self.declare_parameter('obstacle_height', 0.5)     # meters (for 2D costmap)
        self.declare_parameter('person_radius', 0.5)       # meters (safety margin)
        self.declare_parameter('map_frame', 'odom')        # or 'map' if using SLAM
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('publish_rate', 10.0)       # Hz

        self.obstacle_height = self.get_parameter('obstacle_height').value
        self.person_radius = self.get_parameter('person_radius').value
        self.map_frame = self.get_parameter('map_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.publish_rate = self.get_parameter('publish_rate').value

        # State tracking
        self.lidar_obstacles = None
        self.person_detected = False
        self.person_location = None  # Future: could estimate from vision

        # Publishers
        self.obstacle_cloud_pub = self.create_publisher(
            PointCloud2, 'obstacle_cloud', 10)
        self.marker_pub = self.create_publisher(
            MarkerArray, 'obstacle_markers', 10)

        # Subscribers
        self.lidar_cloud_sub = self.create_subscription(
            PointCloud2, 'lidar/obstacle_points', self.lidar_cloud_callback, 10)
        self.stm32_status_sub = self.create_subscription(
            String, 'stm32/status', self.stm32_callback, 10)

        # Timer for publishing
        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_callback)

        self.get_logger().info(
            f'Costmap Publisher initialized, frame: {self.map_frame}')

    def lidar_cloud_callback(self, msg):
        """Receive obstacle points from LiDAR processor"""
        self.lidar_obstacles = msg

    def stm32_callback(self, msg):
        """Parse STM32 status for person detection"""
        if 'person' in msg.data.lower():
            self.person_detected = True
            # Future: could parse person location from message
        else:
            self.person_detected = False

    def publish_callback(self):
        """Publish combined obstacle cloud and markers"""
        current_time = self.get_clock().now().to_msg()

        # Publish LiDAR obstacles
        if self.lidar_obstacles is not None:
            # Update timestamp and frame
            obstacle_cloud = self.lidar_obstacles
            obstacle_cloud.header.stamp = current_time
            obstacle_cloud.header.frame_id = self.base_frame
            self.obstacle_cloud_pub.publish(obstacle_cloud)

        # Publish visualization markers
        markers = self.create_markers(current_time)
        self.marker_pub.publish(markers)

    def create_markers(self, timestamp):
        """Create visualization markers for RViz"""
        marker_array = MarkerArray()

        # Marker for LiDAR obstacles
        if self.lidar_obstacles is not None and self.lidar_obstacles.width > 0:
            lidar_marker = Marker()
            lidar_marker.header.stamp = timestamp
            lidar_marker.header.frame_id = self.base_frame
            lidar_marker.ns = "lidar_obstacles"
            lidar_marker.id = 0
            lidar_marker.type = Marker.POINTS
            lidar_marker.action = Marker.ADD
            lidar_marker.scale.x = 0.1
            lidar_marker.scale.y = 0.1
            lidar_marker.color.r = 1.0
            lidar_marker.color.g = 0.0
            lidar_marker.color.b = 0.0
            lidar_marker.color.a = 1.0

            # Extract points from PointCloud2
            points = self.extract_points_from_cloud(self.lidar_obstacles)
            for point in points:
                p = Point()
                p.x = point[0]
                p.y = point[1]
                p.z = self.obstacle_height / 2
                lidar_marker.points.append(p)

            marker_array.markers.append(lidar_marker)

        # Marker for detected person
        if self.person_detected:
            person_marker = Marker()
            person_marker.header.stamp = timestamp
            person_marker.header.frame_id = self.base_frame
            person_marker.ns = "person_detection"
            person_marker.id = 1
            person_marker.type = Marker.CYLINDER
            person_marker.action = Marker.ADD
            person_marker.pose.position.x = 1.0  # Assume person is 1m ahead
            person_marker.pose.position.y = 0.0
            person_marker.pose.position.z = self.obstacle_height / 2
            person_marker.pose.orientation.w = 1.0
            person_marker.scale.x = self.person_radius * 2
            person_marker.scale.y = self.person_radius * 2
            person_marker.scale.z = self.obstacle_height
            person_marker.color.r = 1.0
            person_marker.color.g = 0.5
            person_marker.color.b = 0.0
            person_marker.color.a = 0.7

            marker_array.markers.append(person_marker)

        return marker_array

    def extract_points_from_cloud(self, cloud_msg):
        """Extract XYZ points from PointCloud2 message"""
        points = []
        point_step = cloud_msg.point_step
        row_step = cloud_msg.row_step

        for i in range(cloud_msg.width):
            offset = i * point_step
            x = struct.unpack_from('f', cloud_msg.data, offset)[0]
            y = struct.unpack_from('f', cloud_msg.data, offset + 4)[0]
            z = struct.unpack_from('f', cloud_msg.data, offset + 8)[0]
            points.append([x, y, z])

        return points


def main(args=None):
    rclpy.init(args=args)
    node = CostmapPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
