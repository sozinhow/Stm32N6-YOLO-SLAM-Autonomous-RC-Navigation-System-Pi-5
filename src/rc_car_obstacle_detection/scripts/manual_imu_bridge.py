#!/usr/bin/env python3
import math
import re
import threading
import serial
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

# ================== 配置参数 ==================
SERIAL_PORT = '/dev/ttyAMA0'
BAUD_RATE = 115200
VALID_COMMANDS = {'1', '2', '3', 'f', 'p', 'a', 'd', 's', 'b', 't'}

# LSM6 默认量程参数
ACCEL_SENSITIVITY_MG_PER_LSB = 0.061   # ±2g 模式下的灵敏度
GYRO_SENSITIVITY_MDPS_PER_LSB = 8.75    # ±245 dps 模式下的灵敏度

# ===== 校正系数 (关键调优参数) =====
# 目标：使静止时加速度模长接近 9.8 m/s^2
ACCEL_CALIB_SCALE = 5.90 
GYRO_CALIB_SCALE = 1.00

# 正则匹配 STM32 发送的文本：$IMU,ax,ay,az,gx,gy,gz,tick*
IMU_REGEX = re.compile(
    r'^\$IMU,([-+]?\d+),([-+]?\d+),([-+]?\d+),([-+]?\d+),([-+]?\d+),([-+]?\d+),(\d+)\*$'
)

class ManualImuBridge(Node):
    def __init__(self):
        super().__init__('manual_imu_bridge')
        self.imu_pub = self.create_publisher(Imu, '/imu', 50)
        
        # 缓存最新的加速度数据用于校正检查
        self.latest_ax = None
        self.latest_ay = None
        self.latest_az = None

        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05)
            self.get_logger().info(f'Connected to {SERIAL_PORT} @ {BAUD_RATE}')
        except Exception as e:
            self.get_logger().error(f'Failed to open serial: {e}')
            raise

        self.running = True
        # 线程1：读取串口数据并发布 ROS2 Topic
        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.read_thread.start()

        # 线程2：终端交互控制
        self.cmd_thread = threading.Thread(target=self.command_loop, daemon=True)
        self.cmd_thread.start()

        self.get_logger().info(
            "\n" + "="*30 +
            "\n--- 控制说明 ---\n"
            "速度档位: 1, 2, 3, f | 停止: p\n"
            "转向控制: a(左), d(右), s(中) | 后退: b | 测试: t\n"
            "调试工具: mag (查看加速度模长), exit (退出并停车)\n" +
            "="*30
        )

    def raw_to_imu(self, ax_raw, ay_raw, az_raw, gx_raw, gy_raw, gz_raw):
        """将原始 LSB 转换为 SI 标准单位"""
        accel_scale = ACCEL_SENSITIVITY_MG_PER_LSB * 1e-3 * 9.80665
        gyro_scale = GYRO_SENSITIVITY_MDPS_PER_LSB * 1e-3 * (math.pi / 180.0)

        # 应用校正系数
        ax = ax_raw * accel_scale * ACCEL_CALIB_SCALE
        ay = ay_raw * accel_scale * ACCEL_CALIB_SCALE
        az = az_raw * accel_scale * ACCEL_CALIB_SCALE
        gx = gx_raw * gyro_scale * GYRO_CALIB_SCALE
        gy = gy_raw * gyro_scale * GYRO_CALIB_SCALE
        gz = gz_raw * gyro_scale * GYRO_CALIB_SCALE

        self.latest_ax, self.latest_ay, self.latest_az = ax, ay, az

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'

        # 填充线性加速度和角速度
        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az
        msg.angular_velocity.x = gx
        msg.angular_velocity.y = gy
        msg.angular_velocity.z = gz

        # 协方差处理
        msg.orientation_covariance[0] = -1.0  # 表示不含姿态数据
        msg.angular_velocity_covariance[0] = 0.02
        msg.angular_velocity_covariance[4] = 0.02
        msg.angular_velocity_covariance[8] = 0.02
        msg.linear_acceleration_covariance[0] = 0.04
        msg.linear_acceleration_covariance[4] = 0.04
        msg.linear_acceleration_covariance[8] = 0.04
        return msg

    def read_loop(self):
        """串口监听主循环"""
        while self.running and rclpy.ok():
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                m = IMU_REGEX.match(line)
                if m:
                    ax, ay, az, gx, gy, gz, _tick = map(int, m.groups())
                    imu_msg = self.raw_to_imu(ax, ay, az, gx, gy, gz)
                    self.imu_pub.publish(imu_msg)
                else:
                    # 打印非数据消息（如 STM32 的调试文本）
                    print(f"\r[STM32] {line}\n[Command] ", end='', flush=True)
            except Exception as e:
                self.get_logger().error(f'Serial read error: {e}')

    def command_loop(self):
        """用户交互控制循环"""
        while self.running and rclpy.ok():
            try:
                cmd = input('[Command] ').strip()
                if not cmd:
                    continue
                
                low_cmd = cmd.lower()
                if low_cmd == 'exit':
                    self.send_cmd('p')
                    self.running = False
                    break
                elif low_cmd == 'mag':
                    if self.latest_ax is None:
                        print('IMU暂未收到数据')
                    else:
                        mag = math.sqrt(self.latest_ax**2 + self.latest_ay**2 + self.latest_az**2)
                        print(f'|a| = {mag:.4f} m/s^2 (x:{self.latest_ax:.2f}, y:{self.latest_ay:.2f}, z:{self.latest_az:.2f})')
                    continue
                
                self.send_cmd(cmd)
            except (EOFError, KeyboardInterrupt):
                self.send_cmd('p')
                self.running = False
                break

    def send_cmd(self, cmd):
        if cmd in VALID_COMMANDS:
            try:
                self.ser.write(cmd.encode())
            except Exception as e:
                self.get_logger().error(f'Serial write error: {e}')
        else:
            print(f'Invalid command: {cmd}')

    def destroy_node(self):
        self.running = False
        try:
            if hasattr(self, 'ser') and self.ser.is_open:
                self.ser.close()
        except: pass
        super().destroy_node()

def main():
    rclpy.init()
    node = ManualImuBridge()
    try:
        while rclpy.ok() and node.running:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        try: node.send_cmd('p') # 安全停车
        except: pass
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()