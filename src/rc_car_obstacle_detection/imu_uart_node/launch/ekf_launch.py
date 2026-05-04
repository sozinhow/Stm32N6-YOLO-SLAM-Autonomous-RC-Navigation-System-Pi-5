import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the path to the package and the config file
    package_share_directory = get_package_share_directory('imu_uart_node')
    config_file = os.path.join(package_share_directory, 'config', 'ekf.yaml')

    return LaunchDescription([
        # Launch the IMU node
        Node(
            package='imu_uart_node',  # Ensure this matches your package name
            executable='imu_uart_node',  # Replace with your executable name
            name='imu_uart_node',
            output='screen',
            parameters=[{'ros__parameters': config_file}],
            remappings=[
                ('/imu/data', '/imu/data'),  # Ensure this matches the IMU topic
                ('/scan', '/scan'),  # Adjust Lidar topic if necessary
            ]
        ),
        # Launch the EKF node
        Node(
            package='robot_localization',  # Assuming you are using robot_localization package
            executable='ekf_node',
            name='ekf_node',
            output='screen',
            parameters=[{'ros__parameters': config_file}],
            remappings=[
                ('/imu/data', '/imu/data'),  # Ensure EKF is subscribing to IMU topic
                ('/scan', '/scan'),  # Ensure EKF is subscribing to Lidar topic
            ]
        )
    ])
