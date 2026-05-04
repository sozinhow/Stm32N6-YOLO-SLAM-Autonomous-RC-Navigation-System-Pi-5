import os
from glob import glob
from setuptools import setup, find_packages

package_name = 'rc_car_obstacle_detection'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    package_data={
        package_name: ['*.py'],
    },
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='RC Car Obstacle Detection System with SLAM Integration',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stm32_bridge = rc_car_obstacle_detection.stm32_bridge:main',
            'lidar_processor = rc_car_obstacle_detection.lidar_processor:main',
            'obstacle_fusion = rc_car_obstacle_detection.obstacle_fusion:main',
            'safety_controller = rc_car_obstacle_detection.safety_controller:main',
            'costmap_publisher = rc_car_obstacle_detection.costmap_publisher:main',
            'rf2o_wrapper = rc_car_obstacle_detection.rf2o_wrapper:main',
            'goal_sender = rc_car_obstacle_detection.goal_sender:main',
        ],
    },
)