import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    rc_car_dir = get_package_share_directory("rc_car_obstacle_detection")

    # --- 1. IMU Bridge (立即启动) ---
    imu_bridge = ExecuteProcess(
        cmd=[
            "python3",
            "/home/pi/ros2_ws/src/rc_car_obstacle_detection/scripts/yb_imu_bridge.py",
        ],
        output="screen",
    )

    # --- 2. Nav2 SLAM (延迟 3 秒，等 IMU 就绪) ---
    nav2_slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rc_car_dir, "launch", "nav2_slam.launch.py")
        ),
    )
    nav2_slam_delayed = TimerAction(
        period=3.0,
        actions=[nav2_slam],
    )

    return LaunchDescription(
        [
            imu_bridge,
            nav2_slam_delayed,
        ]
    )