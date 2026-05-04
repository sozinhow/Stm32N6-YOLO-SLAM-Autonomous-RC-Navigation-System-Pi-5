#!/usr/bin/env python3
"""
SLAM Test Launch (No IMU, No Emergency Stop)
"""
from launch import LaunchDescription
from launch_ros.actions import Node
import os


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

        # EKF (will run without IMU input)
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
                'minimum_travel_distance': 0.05,
                'minimum_travel_heading': 0.05,
                'map_update_interval': 0.5,
                'transform_publish_period': 0.02
            }]
        ),

        # STM32 Bridge only (no obstacle detection)
        Node(
            package='rc_car_obstacle_detection',
            executable='stm32_bridge.py',
            name='stm32_bridge',
            output='screen'
        ),
    ])
