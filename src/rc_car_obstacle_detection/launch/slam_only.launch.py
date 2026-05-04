#!/usr/bin/env python3
"""
SLAM Only Launch File for RC Car (No Nav2 required)
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false'
        ),

        # LiDAR
        Node(
            package='cspc_lidar',
            executable='cspc_lidar',
            name='cspc_lidar',
            output='screen'
        ),

        # RF2O Laser Odometry
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            output='screen',
            parameters=[{
                'laser_scan_topic': '/scan',
                'odom_topic': '/odom',
                'publish_tf': True,
                'base_frame_id': 'base_laser',
                'odom_frame_id': 'odom',
                'freq': 10.0
            }]
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
                'base_frame': 'base_laser',
                'scan_topic': '/scan',
                'mode': 'mapping',
                'resolution': 0.05,
                'max_laser_range': 12.0,
                'minimum_travel_distance': 0.2,
                'minimum_travel_heading': 0.2,
                'map_update_interval': 2.0
            }]
        ),

        # Obstacle detection nodes
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
