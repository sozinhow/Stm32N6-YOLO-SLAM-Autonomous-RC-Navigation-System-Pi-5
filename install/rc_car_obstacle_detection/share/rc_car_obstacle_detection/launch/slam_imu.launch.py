#!/usr/bin/env python3
"""
SLAM Launch File with IMU Odometry
"""
from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    config_dir = os.path.join(
        os.path.expanduser('~'),
        'ros2_ws/src/rc_car_obstacle_detection/config'
    )
    ekf_config = os.path.join(config_dir, 'ekf_imu.yaml')

    return LaunchDescription([
        # LiDAR
        Node(
            package='cspc_lidar',
            executable='cspc_lidar',
            name='cspc_lidar',
            output='screen'
        ),

        # IMU
        Node(
            package='imu_uart_node',
            executable='imu_uart_node',
            name='imu_uart_node',
            output='screen'
        ),

        # EKF for IMU odometry
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config]
        ),

        # SLAM Toolbox
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_link',
                'scan_topic': '/scan',
                'mode': 'mapping',
                'resolution': 0.05,
                'max_laser_range': 12.0,
                'minimum_travel_distance': 0.1,
                'minimum_travel_heading': 0.1,
                'map_update_interval': 1.0,
                'transform_publish_period': 0.02
            }]
        ),

        # Obstacle detection
        Node(
            package='rc_car_obstacle_detection',
            executable='stm32_bridge.py',
            name='stm32_bridge',
            output='screen'
        ),

        Node(
            package='rc_car_obstacle_detection',
            executable='lidar_processor.py',
            name='lidar_processor',
            output='screen'
        ),

        Node(
            package='rc_car_obstacle_detection',
            executable='obstacle_fusion.py',
            name='obstacle_fusion',
            output='screen'
        ),
    ])
