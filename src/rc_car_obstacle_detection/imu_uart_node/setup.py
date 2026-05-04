from setuptools import setup

package_name = 'imu_uart_node'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    install_requires=['setuptools', 'pyserial'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    entry_points={
        'console_scripts': [
            'imu_uart_node = imu_uart_node.imu_uart_node:main',
        ],
    },
)
