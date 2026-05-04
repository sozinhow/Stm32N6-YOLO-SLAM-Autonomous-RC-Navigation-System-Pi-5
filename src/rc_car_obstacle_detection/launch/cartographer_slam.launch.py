import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # ===================== 1) 路径 =====================
    cspc_lidar_dir = get_package_share_directory("cspc_lidar")
    rc_car_dir = get_package_share_directory("rc_car_obstacle_detection")
    cartographer_config_dir = os.path.join(rc_car_dir, "cartographer_config")

    # ===================== 2) 启动参数 =====================
    use_sim_time = LaunchConfiguration("use_sim_time")
    resolution = LaunchConfiguration("resolution")
    publish_period_sec = LaunchConfiguration("publish_period_sec")
    configuration_basename = LaunchConfiguration("configuration_basename")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation clock if true",
    )
    declare_resolution = DeclareLaunchArgument(
        "resolution",
        default_value="0.05",
        description="Resolution of occupancy grid",
    )
    declare_publish_period_sec = DeclareLaunchArgument(
        "publish_period_sec",
        default_value="1.0",
        description="Occupancy grid publish period (s)",
    )
    declare_configuration_basename = DeclareLaunchArgument(
        "configuration_basename",
        default_value="backpack_2d.lua",
        description="Cartographer Lua config file name",
    )

    # ===================== 3) 传感器节点 =====================
    lidar_node = Node(
        package="cspc_lidar",
        executable="cspc_lidar",
        name="lidar",
        output="screen",
        parameters=[os.path.join(cspc_lidar_dir, "params", "cspc_lidar.yaml")],
    )

    # ===================== 4) 静态 TF =====================
    tf_base_to_laser = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_laser_link",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "laser_link"],
        output="screen",
    )

    tf_base_to_base_laser = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_base_laser",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_laser"],
        output="screen",
    )

    tf_base_to_imu = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_imu_link",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "imu_link"],
        output="screen",
    )

    # ===================== 5) Cartographer =====================
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
            configuration_basename,
        ],
        remappings=[
            ("scan", "/scan_fixed"),
        ],
    )

    occupancy_grid_node = Node(
        package="cartographer_ros",
        executable="cartographer_occupancy_grid_node",
        name="occupancy_grid",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        arguments=[
            "-resolution",
            resolution,
            "-publish_period_sec",
            publish_period_sec,
        ],
    )

    # ===================== 6) 启动清单 =====================
    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_resolution,
            declare_publish_period_sec,
            declare_configuration_basename,
            lidar_node,
            tf_base_to_laser,
            tf_base_to_base_laser,
            tf_base_to_imu,
            cartographer_node,
            occupancy_grid_node,
        ]
    )