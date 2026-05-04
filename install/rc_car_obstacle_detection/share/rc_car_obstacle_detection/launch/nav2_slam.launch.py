import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    rc_car_dir = get_package_share_directory("rc_car_obstacle_detection")
    cspc_lidar_dir = get_package_share_directory("cspc_lidar")
    nav2_bringup_dir = get_package_share_directory("nav2_bringup")
    cartographer_config_dir = os.path.join(rc_car_dir, "cartographer_config")

    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
    )

    declare_params_file = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(rc_car_dir, "config", "nav2_params.yaml"),
    )

    # --- Lidar ---
    lidar_node = Node(
        package="cspc_lidar",
        executable="cspc_lidar",
        name="lidar",
        output="screen",
        parameters=[os.path.join(cspc_lidar_dir, "params", "cspc_lidar.yaml")],
    )

    # --- Static TF ---
    tf_base_to_laser = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_laser_link",
        arguments=["-0.12", "0", "0", "0", "0", "0", "base_link", "laser_link"],
    )
    tf_base_to_base_laser = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_base_laser",
        arguments=["-0.12", "0", "0", "0", "0", "0", "base_link", "base_laser"],
    )
    tf_base_to_base_footprint = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_base_footprint",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_footprint"],
    )
    tf_base_to_imu = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_imu_link",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "imu_link"],
    )

    # --- Scan Timestamp Fix ---
    scan_relay = ExecuteProcess(
        cmd=[
            "python3",
            "/home/pi/ros2_ws/src/rc_car_obstacle_detection/scripts/scan_retimestamp_relay.py",
        ],
        output="screen",
    )

    # --- Cartographer SLAM (delay 6s) ---
    cartographer_node = Node(
        package="cartographer_ros",
        executable="cartographer_node",
        name="cartographer",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        arguments=[
            "-configuration_directory",
            cartographer_config_dir,
            "-configuration_basename",
            "backpack_2d.lua",
        ],
        remappings=[("scan", "/scan_fixed")],
    )

    occupancy_grid_node = Node(
        package="cartographer_ros",
        executable="cartographer_occupancy_grid_node",
        name="occupancy_grid",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        arguments=["-resolution", "0.05", "-publish_period_sec", "1.0"],
    )

    cartographer_delayed = TimerAction(
        period=6.0,
        actions=[cartographer_node, occupancy_grid_node],
    )

    # --- Nav2 (delay 20s) ---
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": "true",
            "slam": "False",
            "use_localization": "False",
            "map": "",
        }.items(),
    )

    nav2_delayed = TimerAction(
        period=20.0,
        actions=[nav2_bringup],
    )

    # --- Auto-activate (delay 50s, configure + activate every node) ---
    auto_activate = ExecuteProcess(
    cmd=[
        "bash", "-c",
        "echo '[AUTO] Starting node activation...'; "
        "sleep 2; "
        "ros2 lifecycle set /controller_server configure 2>/dev/null; "
        "ros2 lifecycle set /controller_server activate 2>/dev/null; "
        "sleep 1; "
        "ros2 lifecycle set /planner_server configure 2>/dev/null; "
        "ros2 lifecycle set /planner_server activate 2>/dev/null; "
        "sleep 1; "
        "ros2 lifecycle set /bt_navigator configure 2>/dev/null; "
        "ros2 lifecycle set /bt_navigator activate 2>/dev/null; "
        "sleep 1; "
        "ros2 lifecycle set /behavior_server configure 2>/dev/null; "
        "ros2 lifecycle set /behavior_server activate 2>/dev/null; "
        "sleep 1; "
        "ros2 lifecycle set /collision_monitor configure 2>/dev/null; "
        "ros2 lifecycle set /collision_monitor activate 2>/dev/null; "
        "sleep 1; "
        "ros2 lifecycle set /smoother_server configure 2>/dev/null; "
        "ros2 lifecycle set /smoother_server activate 2>/dev/null; "
        "sleep 1; "
        "ros2 lifecycle set /waypoint_follower configure 2>/dev/null; "
        "ros2 lifecycle set /waypoint_follower activate 2>/dev/null; "
        "sleep 1; "
        "ros2 lifecycle set /velocity_smoother configure 2>/dev/null; "
        "ros2 lifecycle set /velocity_smoother activate 2>/dev/null; "
        "echo '[AUTO] All Nav2 nodes activation complete'"
    ],
    output="screen",
)

    auto_activate_delayed = TimerAction(
        period=50.0,
        actions=[auto_activate],
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_params_file,
            lidar_node,
            tf_base_to_laser,
            tf_base_to_base_laser,
            tf_base_to_base_footprint,
            tf_base_to_imu,
            scan_relay,
            cartographer_delayed,
            nav2_delayed,
            auto_activate_delayed,
        ]
    )