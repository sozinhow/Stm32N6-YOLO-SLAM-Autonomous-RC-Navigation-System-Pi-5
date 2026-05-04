#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from action_msgs.msg import GoalStatusArray
import serial
import time
import threading
import sys

SERIAL_PORT = '/dev/ttyAMA0'
BAUD_RATE = 115200

S_LEFT = 100
S_CENTER = 187
S_RIGHT = 270

M_NEUTRAL = 300
M_SPEED_DEFAULT = 322

LINEAR_DEADZONE = 0.04
ANGULAR_DEADZONE = 0.01

WZ_MAX = 0.1
STOP_DELAY = 0.3
RESEND_INTERVAL = 0.5


def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))


class CmdVelToSTM32(Node):
    def __init__(self):
        super().__init__('cmd_vel_to_stm32')
        self.goal_done = False
        self.last_cmd_time = 0.0
        self.motor_speed = M_SPEED_DEFAULT

        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            self.get_logger().info(f'串口已连接: {SERIAL_PORT}')
        except Exception as e:
            self.get_logger().error(f'串口连接失败: {e}')
            self.ser = None

        self.last_steer_pwm = S_CENTER
        self.last_motor_cmd = 'P'
        self.last_move_time = 0.0
        self.straight_count = 0
        self.current_motor_msg = 'P\n'
        self.current_steer_msg = f'S{S_CENTER}\n'
        self.nav_active = False

        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.status_sub = self.create_subscription(
            GoalStatusArray,
            '/navigate_to_pose/_action/status',
            self.status_callback,
            10
        )

        self.timer = self.create_timer(RESEND_INTERVAL, self.resend_callback)

        # 键盘输入线程
        self.key_thread = threading.Thread(target=self.key_listener, daemon=True)
        self.key_thread.start()

        self.get_logger().info(
            f'cmd_vel -> STM32 PWM 桥接已启动 (速度: M{self.motor_speed})'
        )
        self.get_logger().info('输入 + 加速, - 减速')

    def key_listener(self):
        while True:
            try:
                cmd = input().strip()
                if cmd == '+':
                    self.motor_speed = min(self.motor_speed + 1, 400)
                    self.last_motor_cmd = ''  # 强制下次重发
                    self.get_logger().info(f'速度调整: M{self.motor_speed}')
                elif cmd == '-':
                    self.motor_speed = max(self.motor_speed - 1, M_NEUTRAL + 1)
                    self.last_motor_cmd = ''
                    self.get_logger().info(f'速度调整: M{self.motor_speed}')
            except EOFError:
                break

    def send(self, msg):
        if self.ser and self.ser.is_open:
            self.ser.write(msg.encode())

    def stop_car(self):
        """
        停止车辆并重置状态
        """
        self.current_motor_msg = 'P\n'
        self.current_steer_msg = f'S{S_CENTER}\n'
        
        # 循环发送10次停止指令，确保下位机接收成功
        for _ in range(10):
            self.send(self.current_motor_msg)
            self.send(self.current_steer_msg)
            
        self.last_motor_cmd = 'P'
        self.last_steer_pwm = S_CENTER
        self.nav_active = False
        self.goal_done = True
        self.straight_count = 0
        self.stop_time = time.time()
        self.get_logger().info('TX: P (stopped)')

    def resend_callback(self):
        """
        指令重发回调函数，用于维持控制指令或执行超时保护
        """
        if self.nav_active:
            # 如果导航激活中且超过2秒没有新指令，则强制停车（安全保护）
            if time.time() - self.last_cmd_time > 2.0:
                self.stop_car()
            else:
                # 否则重发当前的电机和转向指令
                self.send(self.current_motor_msg)
                self.send(self.current_steer_msg)
        
        # 如果导航刚结束且处于停止后的5秒窗口内，持续发送停止位
        elif self.goal_done and (time.time() - self.stop_time) < 5.0:
            self.send('P\n')

    def status_callback(self, msg):
        if len(msg.status_list) > 0:
            latest = msg.status_list[-1]
            if latest.status in [4, 5, 6]:
                if self.nav_active:
                    self.stop_car()
            elif latest.status == 2:
                self.goal_done = False


    def cmd_vel_callback(self, msg):
        if self.goal_done:
            return

        self.last_cmd_time = time.time()
        vx = msg.linear.x
        wz = msg.angular.z
        now = time.time()

        # === 电机逻辑 ===
        if abs(vx) < LINEAR_DEADZONE and abs(wz) < ANGULAR_DEADZONE:
            if self.last_motor_cmd != 'P' and (now - self.last_move_time) > STOP_DELAY:
                self.current_motor_msg = 'P\n'
                self.current_steer_msg = f'S{S_CENTER}\n'
                self.send(self.current_motor_msg)
                self.send(self.current_steer_msg)
                self.last_motor_cmd = 'P'
                self.last_steer_pwm = S_CENTER
                self.straight_count = 0
                self.nav_active = False
                self.get_logger().info('TX: P')
            return

        self.last_move_time = now
        self.nav_active = True

        if vx < -LINEAR_DEADZONE:
            if self.last_motor_cmd != 'b':
                self.current_motor_msg = 'b\n'
                self.send(self.current_motor_msg)
                self.last_motor_cmd = 'b'
                self.get_logger().info('TX: b')
        else:
            motor_cmd = f'M{self.motor_speed}\n'
            if self.last_motor_cmd != motor_cmd:
                self.current_motor_msg = motor_cmd
                self.send(self.current_motor_msg)
                self.last_motor_cmd = motor_cmd
                self.get_logger().info(f'TX: M{self.motor_speed}')

        # === 舵机逻辑 ===
        if abs(wz) < ANGULAR_DEADZONE:
            self.straight_count += 1
            if self.straight_count > 10:
                steer_pwm = S_CENTER
            else:
                return
        else:
            self.straight_count = 0
            ratio = clamp(wz / WZ_MAX, -1.0, 1.0)

            MIN_OFFSET = 20
            MAX_OFFSET = 87

            raw_offset = int(abs(ratio) * MAX_OFFSET)
            offset = max(raw_offset, MIN_OFFSET)

            if ratio > 0:
                steer_pwm = S_CENTER + offset
            else:
                steer_pwm = S_CENTER - offset

        steer_pwm = clamp(steer_pwm, S_LEFT, S_RIGHT)

        if steer_pwm != self.last_steer_pwm:
            self.current_steer_msg = f'S{steer_pwm}\n'
            self.send(self.current_steer_msg)
            self.last_steer_pwm = steer_pwm
            self.get_logger().info(f'TX: S{steer_pwm}')


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelToSTM32()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node.ser and node.ser.is_open:
            node.ser.write(b'P\n')
            node.ser.close()
        node.get_logger().info('已停车并关闭串口')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()