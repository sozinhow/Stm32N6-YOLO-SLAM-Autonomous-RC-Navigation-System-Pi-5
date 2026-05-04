import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import serial
import re

# Calibration offsets (use real values as per your STM32 calibration)
offset_ax = 0
offset_ay = 0
offset_az = 0
offset_gx = 0
offset_gy = 0
offset_gz = 0

class IMU_UART_Node(Node):
    def __init__(self):
        super().__init__('imu_uart_node')

        # Initialize the UART connection (replace with your actual port)
        self.ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)

        # Publisher for IMU data
        self.publisher = self.create_publisher(Imu, '/imu/data', 10)

        # Timer to read from UART every 100ms
        self.timer = self.create_timer(0.1, self.read_imu_data)

        # Debug log
        self.get_logger().info("IMU UART Node Initialized")

    def read_imu_data(self):
        # Read one line of data from the UART buffer
        line = self.ser.readline().decode('utf-8').strip()
        self.get_logger().info(f"Read line: {line}")  # Log the received data

        # Parse IMU data from the string (e.g., "$IMU,13,29,13327,12,-23,10,138840*")
        match = re.match(r"\$IMU,(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(\d+)\*", line)
        if match:
            # Extract IMU values
            ax, ay, az, gx, gy, gz, timestamp = map(int, match.groups())

            # Apply calibration offsets
            ax -= offset_ax
            ay -= offset_ay
            az -= offset_az
            gx -= offset_gx
            gy -= offset_gy
            gz -= offset_gz

            # Create and populate the IMU message
            imu_msg = Imu()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = 'base_link'

            # Fill in the accelerometer and gyroscope data (convert to m/s^2 and rad/s)
            imu_msg.linear_acceleration.x = ax * 9.81 / 1000.0  # Convert to m/s^2
            imu_msg.linear_acceleration.y = ay * 9.81 / 1000.0
            imu_msg.linear_acceleration.z = az * 9.81 / 1000.0
            imu_msg.angular_velocity.x = gx * (3.14159 / 180.0)  # Convert to radians/s
            imu_msg.angular_velocity.y = gy * (3.14159 / 180.0)
            imu_msg.angular_velocity.z = gz * (3.14159 / 180.0)

            # Publish the IMU data
            self.publisher.publish(imu_msg)
            self.get_logger().info("IMU data published")

        else:
            self.get_logger().warn(f"Failed to parse IMU data: {line}")

def main(args=None):
    rclpy.init(args=args)
    node = IMU_UART_Node()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
