#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch import LaunchDescription


def generate_launch_description():
    cspc_lidar_dir = get_package_share_directory("cspc_lidar")
    slam_toolbox_dir = get_package_share_directory("slam_toolbox")

    nodes = [
        Node(
            package="cspc_lidar",
            executable="cspc_lidar",
            name="lidar",
            output="screen",
            parameters=[os.path.join(cspc_lidar_dir, "params", "cspc_lidar.yaml")],
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="tf_pub",
            arguments=["0", "0", "0", "0", "0", "0", "base_link", "laser_link"],
            output="screen",
        ),
        Node(
            package="slam_toolbox",
            executable="async_slam_toolbox_node",
            name="slam",
            output="screen",
            parameters=[
                os.path.join(slam_toolbox_dir, "config", "mapper_params_online_async.yaml"),
                {
                    "tf_buffer_duration": 100.0,
                    "transform_timeout": 5.0,
                    "scan_buffer_size": 100,
                    "throttle_scans": 1,
                },
            ],
        ),
    ]

    return LaunchDescription(nodes)
