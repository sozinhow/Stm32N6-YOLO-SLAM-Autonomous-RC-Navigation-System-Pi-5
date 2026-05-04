#!/usr/bin/env python3
"""
Simple SLAM Launch - No RF2O odometry
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([
        # LiDAR
        Node(
            package='cspc_lidar',
            executable='cspc_lidar',
            name='cspc_lidar',
            output='screen'
        ),

        # SLAM Toolbox (will generate its own odometry)
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
                'do_loop_closing': True,
                'scan_buffer_size': 10
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

