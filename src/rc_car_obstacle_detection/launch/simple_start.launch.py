#!/usr/bin/env python3
"""
Simple launch file for RC Car - LiDAR + Obstacle Detection only
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyAMA0',
            description='Serial port for STM32 communication'
        ),
        DeclareLaunchArgument(
            'detection_distance',
            default_value='1.5',
            description='LiDAR detection distance in meters'
        ),

        # LiDAR Node
        Node(
            package='cspc_lidar',
            executable='cspc_lidar',
            name='cspc_lidar',
            output='screen'
        ),

        # STM32 Bridge Node
        Node(
            package='rc_car_obstacle_detection',
            executable='stm32_bridge.py',
            name='stm32_bridge',
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'baud_rate': 115200
            }]
        ),

        # LiDAR Processor Node
        Node(
            package='rc_car_obstacle_detection',
            executable='lidar_processor.py',
            name='lidar_processor',
            output='screen',
            parameters=[{
                'detection_distance': LaunchConfiguration('detection_distance'),
                'detection_angle': 60.0,
                'min_points_threshold': 5,
                'scan_topic': '/scan',
                'publish_obstacle_cloud': True
            }]
        ),

        # Obstacle Fusion Node
        Node(
            package='rc_car_obstacle_detection',
            executable='obstacle_fusion.py',
            name='obstacle_fusion',
            output='screen',
            parameters=[{
                'lidar_timeout': 0.5,
                'vision_timeout': 1.0,
                'emergency_cooldown': 2.0
            }]
        ),
    ])
