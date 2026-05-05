# SLAM and Edge AI–Based Autonomous Mobile Robot System — Architecture & Details
Demo Video: https://youtu.be/_l2b3o806oM 
---
## I. System Architecture Diagram

```text
 ┌─────────────────────────────────────────────────────────────────────────────────────┐
 │                             PC (Windows)                                            │
 │                                                                                     │
 │   ┌──────────────┐                                                                  │
 │   │   RViz2      │  ← SSH/WiFi →  Display Map, Path, LiDAR Point Cloud, Costmap     │
 │   │              │                Set 2D Pose Estimate / Nav2 Goal                  │
 │   └──────────────┘                                                                  │
 └────────────────────────────────────────┬────────────────────────────────────────────┘
                                          │ ROS 2 DDS (WiFi)
 ┌────────────────────────────────────────┴────────────────────────────────────────────┐
 │                            Raspberry Pi 5 (Ubuntu + ROS 2 Jazzy)                    │
 │                                                                                     │
 │  ┌─────────────────────┐    ┌──────────────────────┐    ┌───────────────────────┐   │
 │  │ yb_imu_bridge.py    │    │ scan_retimestamp_    │    │  cmd_vel_to_stm32.py  │   │
 │  │ (Term 1, Manual)    │    │ relay.py (in launch) │    │  (Term 2, Manual)     │   │
 │  │                     │    │                      │    │                       │   │
 │  │ USB(/dev/ttyUSB1)   │    │ /scan → /scan_fixed  │    │ /cmd_vel → UART TX    │   │
 │  │ YB-MRA02 IMU        │    │ Fixes timestamp &    │    │ M323/S187/P/b Protocol│   │
 │  │ → /imu (100Hz)      │    │ frame_id(laser_link) │    │ Speed +/- adjustable  │   │
 │  └────────┬────────────┘    └──────────┬───────────┘    └───────────┬───────────┘   │
 │           │                            │                            │               │
 │           ▼                            ▼                            ▲               │
 │  ┌────────────────────────────────────────────────────────────────────────────────┐ │
 │  │                      nav2_slam.launch.py (Main Launch)                         │ │
 │  │                                                                                │ │
 │  │  ┌──────────┐  ┌─────────────────┐  ┌──────────────────────────────────────┐   │ │
 │  │  │ cspc_    │  │ static_transform│  │         Cartographer SLAM            │   │ │
 │  │  │ lidar    │  │ _publisher (x4) │  │       (Starts with 6s delay)         │   │ │
 │  │  │ driver   │  │                 │  │                                      │   │ │
 │  │  │ /scan    │  │ base_link →     │  │  Subscribes: /scan_fixed, /imu       │   │ │
 │  │  │ (10Hz)   │  │  laser_link     │  │  Publishes: /map, TF(map→odom)       │   │ │
 │  │  │          │  │  base_laser     │  │  Config: backpack_2d.lua             │   │ │
 │  │  │ USB      │  │  base_footprint │  │  - IMU assisted localization         │   │ │
 │  │  │/ttyUSB0  │  │  imu_link       │  │  - Real-time mapping                 │   │ │
 │  │  └──────────┘  └─────────────────┘  └──────────────────────────────────────┘   │ │
 │  │                                                                                │ │
 │  │  ┌──────────────────────────────────────────────────────────────────────────┐  │ │
 │  │  │                   Nav2 Navigation Stack (Starts with 15s delay)          │  │ │
 │  │  │                                                                          │  │ │
 │  │  │  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────────┐     │  │ │
 │  │  │  │ NavFn        │  │ MPPI          │  │ BT Navigator               │     │  │ │
 │  │  │  │ Planner      │→ │ Controller    │→ │ (Behavior Tree Navigator)  │     │  │ │
 │  │  │  │              │  │ (Ackermann)   │  │                            │     │  │ │
 │  │  │  │ /plan Path   │  │ /cmd_vel_nav  │  │ Manages Plan/Ctrl/Recovery │     │  │ │
 │  │  │  └──────────────┘  └───────────────┘  └────────────────────────────┘     │  │ │
 │  │  │                                                                          │  │ │
 │  │  │  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────────┐     │  │ │
 │  │  │  │ Velocity     │  │ Collision     │  │ Behavior Server            │     │  │ │
 │  │  │  │ Smoother     │→ │ Monitor       │→ │ (spin/backup/wait)         │     │  │ │
 │  │  │  │              │  │               │  │                            │     │  │ │
 │  │  │  │ Smoothing    │  │ FootprintApp  │  │ Recovery Mgmt              │     │  │ │
 │  │  │  │ /cmd_vel_    │  │ roach avoid   │  │                            │     │  │ │
 │  │  │  │ smoothed     │  │ → /cmd_vel    │  │                            │     │  │ │
 │  │  │  └──────────────┘  └───────────────┘  └────────────────────────────┘     │  │ │
 │  │  │                                                                          │  │ │
 │  │  │  ┌──────────────────────────┐  ┌──────────────────────────────────┐      │  │ │
 │  │  │  │ Local Costmap            │  │ Global Costmap                   │      │  │ │
 │  │  │  │ (3m x 3m Rolling Window) │  │ (Global Static + Obstacle Layer) │      │  │ │
 │  │  │  │ VoxelLayer + Inflation   │  │ StaticLayer+ObstacleLayer+Infl   │      │  │ │
 │  │  │  │ Subscribes: /scan_fixed  │  │ Subscribes: /scan_fixed, /map    │      │  │ │
 │  │  │  └──────────────────────────┘  └──────────────────────────────────┘      │  │ │
 │  │  │                                                                          │  │ │
 │  │  │  Auto-activation script (30s delay): Sequentially configures &           │  │ │
 │  │  │  activates all lifecycle nodes                                           │  │ │
 │  │  └──────────────────────────────────────────────────────────────────────────┘  │ │
 │  └────────────────────────────────────────────────────────────────────────────────┘ │
 │                                          │                                          │
 │                                     UART │ /dev/ttyAMA0                             │
 │                                   115200 │ baud                                     │
 └──────────────────────────────────────────┼──────────────────────────────────────────┘
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      │         STM32N6570-DK Dev Board           │
                      │                                           │
                      │  ┌────────────────────────────────────┐   │
                      │  │  UART2 Interrupt (USART2_IRQHandler│   │
                      │  │  → UART_ProcessByte()              │   │
                      │  │  → Process_Command() / Process_    │   │
                      │  │    Manual_Control()                │   │
                      │  │                                    │   │
                      │  │  Protocol Parsing:                 │   │
                      │  │   M<val>\n → Motor PWM (TIM1_CH3)  │   │
                      │  │   S<val>\n → Servo PWM (TIM1_CH1)  │   │
                      │  │   P\n      → Full Stop             │   │
                      │  │   b        → Brake→Neutral→Reverse │   │
                      │  │   1/2/3    → Preset speeds         │   │
                      │  │   a/d/s    → Preset steering       │   │
                      │  └────────────────────────────────────┘   │
                      │                                           │
                      │  ┌────────────────────────────────────┐   │
                      │  │  YOLO Object Detection (NPU Accel) │   │
                      │  │  Camera → NN Inference → Post-proc │   │
                      │  │  Person detected(class 0, conf>0.5)│   │
                      │  │  → is_emergency_stop = 1           │   │
                      │  │  → Motor immediate switch M_NEUTRAL│   │
                      │  │  → Rejects all M cmds until reset  │   │
                      │  └────────────────────────────────────┘   │
                      │                                           │
                      │  ┌──────────────┐  ┌──────────────────┐   │
                      │  │ TIM1 PWM     │  │ I2C1 (Onbrd IMU) │   │
                      │  │ 50Hz/20ms    │  │ LSM6DSO          │   │
                      │  │              │  │ LCD display only │   │
                      │  │ CH1(PE9)→Srv │  │ TX func removed  │   │
                      │  │ CH3(PE13)→ESC│  └──────────────────┘   │
                      │  │              │                         │
                      │  │ Period=4000  │  ┌──────────────────┐   │
                      │  │ Prescaler=   │  │ LCD Display      │   │
                      │  │ 2000         │  │ BBox+Confidence  │   │
                      │  │              │  │ IMU Data         │   │
                      │  │ S100=Full L  │  │ Inference Time   │   │
                      │  │ S187=Center  │  └──────────────────┘   │
                      │  │ S270=Full R  │                         │
                      │  │              │                         │
                      │  │ M300=Neutral │                         │
                      │  │ M319=Min Spd │                         │
                      │  │ M340=High Spd│                         │
                      │  │ M200=Brake   │                         │
                      │  └──────────────┘                         │
                      └──────────────┬─────────────┬──────────────┘
                                     │             │
                                PWM CH1          PWM CH3
                                     │             │
                              ┌──────┴──┐   ┌──────┴──┐
                              │  Servo  │   │   ESC   │
                              │(Steering│   │ (Drive) │
                              └─────────┘   └─────────┘
                                     │             │
                              ┌──────┴─────────────┴──────┐
                              │      TT02 RC Chassis      │
                              │ Front Steer / Rear Drive  │
                              │ Wheelbase ~0.257m         │
                              │ Dimension ~0.50m x 0.24m  │
                              └───────────────────────────┘


Sensor Layer              Processing Layer                 Decision Layer             Execution Layer
 ─────────                 ──────                           ──────                     ──────

 YB-MRA02 ───→ /imu ─────────────────────────→ Cartographer ──→ TF(map→odom)
 (100Hz)      (imu_link)                       SLAM             /map
                                                ↑
 CSPC LiDAR ─→ /scan ──→ scan_retimestamp ───→ /scan_fixed ───→ Local/Global Costmaps
 (10Hz)                  _relay.py                                    ↓
                                                                Nav2 Stack
                                                                (Planner/Controller)
                                                                      ↓
 STM32 UART ←─ M/S/P/b cmds ←─ cmd_vel_to_stm32.py ←─────────── /cmd_vel
                 │
                 ▼
          PWM Generation
         (Motor & Servo)


```
---
## III. Launch & Startup Procedures

The system utilizes a staggered startup sequence to manage dependencies between sensor data, coordinate transforms, and navigation algorithms.

### 1. Full system lanch (Start First)
These scripts bridge the hardware to the ROS 2 environment. Open two separate terminals on the Raspberry Pi 5:

*   **Terminal 1 (Ros node/Slam/nav2/lidar&imu driver):**
    ```bash
    ros2 launch rc_car_obstacle_detection full_nav.launch.py
    ```
    Run the main launch file to start the navigation stack. It follows an internal timer to ensure stability:

| Time | Component | Description |
| :--- | :--- | :--- |
| **0s** | **LiDAR Driver** | Starts the CSPC LiDAR at 10Hz. |
| **0s** | **TF Transforms** | Publishes static transforms (`base_link` → `laser_link`, etc.). |
| **6s** | **Cartographer** | Begins SLAM once LiDAR/IMU data is stable. |
| **15s** | **Nav2 Stack** | Initializes the MPPI Controller and Planner. |
| **30s** | **Lifecycle Manager** | Sequentially activates all nodes to the "Active" state. |


### 2.  Manual Bridges - handle the communication and control commands between ROS2 and STM32
*   **Terminal 2 (STM32 Control):**
    
    ```bash
    python3 ~/ros2_ws/src/rc_car_obstacle_detection/scripts/cmd_vel_to_stm32.py
    ```
    *Listens to `/cmd_vel` and sends serial commands to the STM32 N6570.*

---
## V. Deployment & Quick Start Guide

### 1. Build and Workspace Setup
On the **Raspberry Pi 5**, ensure your ROS 2 workspace is compiled and the environment variables are sourced:
```bash
# Navigate to workspace
cd ~/ros2_ws

# Build the specific navigation package
colcon build --packages-select rc_car_obstacle_detection

# Source the workspace
source install/setup.bash
```
2. Execution Sequence
The system requires a staggered startup to allow hardware drivers and lifecycle nodes to initialize correctly.

Step 1: Start the Hardware Bridges (Terminal 1 & 2)
Open two terminals to bridge the sensors and the STM32 controller:

Terminal 1 (Ros node/Slam/nav2/lidar&imu driver):

```Bash
# Source ROS 2 Jazzy and workspace
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch rc_car_obstacle_detection full_nav.launch.py
```

Step 2: Verify Lifecycle Activation
Wait 35 seconds after launching for the auto-activation script to finish. Run these commands to ensure all servers are active:
```
```Bash
ros2 lifecycle list /controller_server
ros2 lifecycle list /planner_server
ros2 lifecycle list /bt_navigator
ros2 lifecycle list /behavior_server
ros2 lifecycle list /collision_monitor
```

Terminal 2 (STM32 Control):
Note: This started after the navigation stack is active (Step 3).

```Bash
python3 ~/ros2_ws/src/rc_car_obstacle_detection/scripts/cmd_vel_to_stm32.py
```

3. Testing and Interaction
Remote Control/Monitoring: On a Windows PC connected to the same network, open RViz2 to view the map and set goals using the Nav2 Goal tool.

Command Debugging: To monitor the velocity commands generated by the navigation stack, run:

```Bash
ros2 topic echo /cmd_vel
```
VI. Troubleshooting
Node Activation: If lifecycle nodes remain in the unconfigured state after 40 seconds, restart the nav2_slam.launch.py.

Serial Communication: Ensure /dev/ttyUSB0 (LiDAR), /dev/ttyUSB1 (IMU), and /dev/ttyAMA0 (STM32) have the correct permissions:

```Bash
sudo chmod 666 /dev/ttyUSB* /dev/ttyAMA0
```
Emergency Stop: If the car refuses to move, check the STM32 LCD. The YOLOv8n NPU model will trigger an emergency stop if a person is detected in the camera frame.

---
## IV. Manual Control Utility (`listen.py`)

For hardware debugging and manual testing, the `listen.py` script allows you to send direct keyboard commands to the STM32 via the Raspberry Pi serial bridge. This bypasses the autonomous Nav2 stack.

### 1. Execution
Run this script in a separate terminal on the Raspberry Pi:
```bash
python3 ~/ros2_ws/src/rc_car_obstacle_detection/scripts/listen.py
```
Command ReferenceThe script maps keyboard inputs to specific PWM duty cycles on the STM32 (TIM1 CH1 for Steering, CH3 for Motor):


1 – Low Speed: Sets motor to M_SPEED_1.

2 – Mid Speed: Sets motor to M_SPEED_2.

3 – High Speed: Sets motor to M_SPEED_3.

f – Full Forward: Stress test mode (PWM 400 / 2.0ms).

p – Stop: Immediate reset to M_NEUTRAL (300).

b – Reverse Sequence: Executes Brake → Neutral → Reverse with 400ms staggered delays.

a – Steering Left: Sets servo to S_LEFT .

d – Steering Right: Sets servo to S_RIGHT .

s – Center Steering: Sets servo to S_CENTER .
