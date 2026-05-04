#!/usr/bin/env python3
"""
Full System Launch File for RC Car (ROS 2 Jazzy)
Launches complete SLAM + obstacle detection system:
- Sensors (LiDAR, IMU)
- Odometry (rf2o + EKF fusion)
- Obstacle detection
- Optional SLAM
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import conditions
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # Get package directories
    try:
        imu_pkg_dir = get_package_share_directory('imu_uart_node')
    except:
        imu_pkg_dir = None

    try:
        lidar_pkg_dir = get_package_share_directory('cspc_lidar')
    except:
        lidar_pkg_dir = None

    try:
        rf2o_pkg_dir = get_package_share_directory('rf2o_laser_odometry')
    except:
        rf2o_pkg_dir = None

    try:
        obstacle_pkg_dir = get_package_share_directory('rc_car_obstacle_detection')
    except:
        obstacle_pkg_dir = None

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'enable_slam',
            default_value='false',
            description='Enable SLAM (slam_toolbox)'
        ),
        DeclareLaunchArgument(
            'enable_ekf',
            default_value='true',
            description='Enable EKF sensor fusion'
        ),
        DeclareLaunchArgument(
            'enable_rf2o',
            default_value='true',
            description='Enable RF2O laser odometry'
        ),
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

        # ========== SENSOR LAYER ==========

        # LiDAR Node
        Node(
            package='cspc_lidar',
            executable='cspc_lidar',
            name='cspc_lidar',
            output='screen',
        ),

        # IMU Node (for odometry/SLAM, NOT obstacle detection)
        Node(
            package='imu_uart_node',
            executable='imu_uart_node',
            name='imu_uart_node',
            output='screen',
            condition=conditions.IfCondition(
                LaunchConfiguration('enable_ekf')
                if imu_pkg_dir else 'false'
            )
        ),

        # ========== ODOMETRY LAYER ==========

        # RF2O Laser Odometry
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            output='screen',
            parameters=[{
                'laser_scan_topic': '/scan',
                'odom_topic': '/odom_rf2o',
                'publish_tf': True,
                'base_frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'freq': 10.0
            }],
            condition=conditions.IfCondition(
                LaunchConfiguration('enable_rf2o')
                if rf2o_pkg_dir else 'false'
            )
        ),

        # EKF Sensor Fusion (IMU + Laser Odometry)
        # Note: User should have ekf_launch.py in imu_uart_node package
        # This is a placeholder - user may need to adjust based on their setup
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([imu_pkg_dir, 'launch', 'ekf_launch.py'])
            ),
            condition=conditions.IfCondition(
                LaunchConfiguration('enable_ekf')
                if imu_pkg_dir else 'false'
            )
        ) if imu_pkg_dir else Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[{
                'frequency': 30.0,
                'two_d_mode': True,
                'odom0': '/odom_rf2o',
                'imu0': '/imu/data',
                'odom0_config': [True, True, False,
                                False, False, True,
                                False, False, False,
                                False, False, True,
                                False, False, False],
                'imu0_config': [False, False, False,
                               False, False, True,
                               False, False, False,
                               False, False, True,
                               True, False, False],
            }],
            condition=conditions.IfCondition(
                LaunchConfiguration('enable_ekf')
            )
        ),

        # ========== OBSTACLE DETECTION LAYER ==========

        # Include obstacle detection launch file
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    obstacle_pkg_dir, 'launch', 'obstacle_detection.launch.py'
                ])
            ),
            launch_arguments={
                'serial_port': LaunchConfiguration('serial_port'),
                'detection_distance': LaunchConfiguration('detection_distance'),
                'scan_topic': '/scan',
                'enable_costmap': 'true'
            }.items(),
            condition=conditions.IfCondition('true' if obstacle_pkg_dir else 'false')
        ) if obstacle_pkg_dir else Node(
            package='rc_car_obstacle_detection',
            executable='lidar_processor.py',
            name='placeholder',
            output='screen'
        ),

        # ========== SLAM LAYER (Optional) ==========

        # SLAM Toolbox (online async)
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
                'minimum_travel_distance': 0.2,
                'minimum_travel_heading': 0.2,
                'map_update_interval': 2.0
            }],
            condition=conditions.IfCondition(
                LaunchConfiguration('enable_slam')
            )
        ),
    ])
