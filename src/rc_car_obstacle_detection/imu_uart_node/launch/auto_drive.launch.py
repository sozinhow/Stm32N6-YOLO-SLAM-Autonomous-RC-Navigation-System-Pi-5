from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. CSPC Lidar Node
        Node(
            package='cspc_lidar',
            executable='cspc_lidar_node',
            name='lidar_node',
            output='screen'
        ),

        # 2. RF2O Laser Odometry (The Virtual Encoder)
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o',
            output='screen',
            parameters=[{
                'laser_scan_topic': '/scan',
                'odom_topic': '/odom_rf2o',
                'publish_tf': True,
                'base_frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'laser_frame_id': 'laser_frame',
                'freq': 10.0
            }],
        ),

        # 3. Static TF (Tell ROS where the Lidar is on the car)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.1', '0', '0.1', '0', '0', '0', 'base_link', 'laser_frame']
        )
    ])