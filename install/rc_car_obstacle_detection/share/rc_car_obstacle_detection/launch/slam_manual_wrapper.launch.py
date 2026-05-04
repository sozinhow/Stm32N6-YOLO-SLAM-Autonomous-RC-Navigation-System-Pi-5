#!/usr/bin/env python3
"""
SLAM Launch File (run rf2o_wrapper manually)
"""
from launch import LaunchDescription
from launch_ros.actions import Node
def generate_launch_description():
    return LaunchDescription([
        Node(
            package='cspc_lidar',
            executable='cspc_lidar',
            name='cspc_lidar',
            output='screen'
        ),
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            output='screen',
            parameters=[{
                'laser_scan_topic': '/scan_converted',
                'odom_topic': '/odom',
                'publish_tf': True,
                'base_frame_id': 'base_laser',
                'odom_frame_id': 'odom',
                'freq': 10.0
            }]
        ),
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
                'minimum_travel_distance': 0.1,
                'minimum_travel_heading': 0.1,
                'map_update_interval': 1.0,
                'transform_publish_period': 0.02
            }]
        ),
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
