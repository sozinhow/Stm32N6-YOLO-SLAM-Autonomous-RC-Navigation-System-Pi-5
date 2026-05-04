import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # --- 1. 路径获取 ---
    rc_car_dir = get_package_share_directory("rc_car_obstacle_detection")
    cspc_lidar_dir = get_package_share_directory("cspc_lidar")
    nav2_bringup_dir = get_package_share_directory("nav2_bringup")

    # --- 2. 声明启动参数 (Launch Arguments) ---
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_yaml = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")
    autostart = LaunchConfiguration("autostart")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="是否使用仿真时间 (Gazebo)"
    )

    declare_map = DeclareLaunchArgument(
        "map",
        default_value="/home/pi/my_map_new.yaml",
        description="地图 YAML 文件的完整路径"
    )

    declare_params_file = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(rc_car_dir, "config", "nav2_params.yaml"),
        description="Nav2 参数文件的完整路径"
    )

    declare_autostart = DeclareLaunchArgument(
        "autostart",
        default_value="true",
        description="是否自动启动 Nav2 堆栈"
    )

    # --- 3. 传感器驱动与静态坐标转换 (TF) ---
    # 启动 CSPC 激光雷达节点
    lidar_node = Node(
        package="cspc_lidar",
        executable="cspc_lidar",
        name="lidar",
        output="screen",
        parameters=[os.path.join(cspc_lidar_dir, "params", "cspc_lidar.yaml")],
    )

    # 发布静态 TF: base_link -> laser_link
    tf_base_to_laser = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_laser_link",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "laser_link"],
    )

    # 发布静态 TF: base_link -> base_laser
    tf_base_to_base_laser = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_base_laser",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_laser"],
    )

    # 发布静态 TF: base_link -> base_footprint
    tf_base_to_base_footprint = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="tf_pub_base_to_base_footprint",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_footprint"],
    )

    # --- 4. 数据处理脚本 ---
    # Scan 时间戳修复脚本 (解决雷达数据延迟或同步问题)
    scan_retimestamp_relay = ExecuteProcess(
        cmd=[
            "python3",
            "/home/pi/ros2_ws/src/rc_car_obstacle_detection/scripts/scan_retimestamp_relay.py",
        ],
        output="screen",
    )

    # --- 5. 激光里程计 (rf2o) ---
    # 延迟 5 秒启动，确保雷达驱动已稳定运行
    rf2o_node = Node(
        package="rf2o_laser_odometry",
        executable="rf2o_laser_odometry_node",
        name="rf2o_laser_odometry",
        output="screen",
        parameters=[
            os.path.join(rc_car_dir, "config", "rf2o.yaml"),
            {"use_sim_time": use_sim_time},
        ],
        remappings=[("/scan", "/scan_fixed")], # 使用修复后的雷达数据
    )

    rf2o_delayed = TimerAction(period=5.0, actions=[rf2o_node])

    # --- 6. 导航堆栈 (Nav2 Bringup) ---
    # 延迟 10 秒启动，确保雷达、里程计和 TF 均已就绪
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "map": map_yaml,
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": autostart,
            "slam": "True", # 使用定位模式而非建图模式
        }.items(),
    )

    nav2_delayed = TimerAction(period=10.0, actions=[nav2_bringup])

    # --- 7. 返回启动描述项 ---
    return LaunchDescription([
        declare_use_sim_time,
        declare_map,
        declare_params_file,
        declare_autostart,
        
        lidar_node,
        tf_base_to_laser,
        tf_base_to_base_laser,
        tf_base_to_base_footprint,
        scan_retimestamp_relay,
        
        rf2o_delayed,
        nav2_delayed,
    ])