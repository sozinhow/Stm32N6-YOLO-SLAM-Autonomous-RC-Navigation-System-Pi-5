from setuptools import find_packages
from setuptools import setup

setup(
    name='rc_car_obstacle_detection',
    version='1.0.0',
    packages=find_packages(
        include=('rc_car_obstacle_detection', 'rc_car_obstacle_detection.*')),
)
