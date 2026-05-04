# RC Car Obstacle Detection System

Complete ROS 2 Jazzy obstacle detection system for RC car with STM32N6 DK and Raspberry Pi 5.

## Hardware Setup

### STM32N6 DK
- **YOLO Object Detection**: Person detection with emergency stop
- **IMU (LSM6DSO)**: Motion sensing via I2C
- **UART**: Communication with Raspberry Pi (115200 baud)
  - TX: PD5 → Pi RX (GPIO 15)
  - RX: PF6 ← Pi TX (GPIO 14)
  - GND: Common ground

### Raspberry Pi 5
- **OS**: Ubuntu Server 24.04
- **ROS 2**: Jazzy
- **LiDAR**: CSPC LiDAR (via cspc_lidar_sdk_ros2)
- **IMU**: Via imu_uart_node (reading from STM32)
- **UART**: /dev/ttyAMA0 (GPIO 14/15)

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5 (ROS 2 Jazzy)             │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ imu_uart_node│    │cspc_lidar_sdk│    │stm32_bridge  │  │
│  │  (existing)  │    │   (existing) │    │    (new)     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │ /imu/data         │ /scan             │ commands  │
│         │                   │                   │           │
│  ┌──────▼───────────────────▼───────────────────▼───────┐  │
│  │          Obstacle Fusion & Safety Controller          │  │
│  │  • LiDAR Processor                                    │  │
│  │  • Obstacle Fusion                                    │  │
│  │  • Safety Controller (keyboard)                       │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ /emergency_stop                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  STM32N6 DK │
                    │  • YOLO     │
                    │  • IMU      │
                    │  • Motors   │
                    └─────────────┘
```

## Installation on Raspberry Pi 5

### 1. Copy Package to Pi

```bash
# On your Windows machine, use VS Code Remote or SCP
# Copy the entire rc_car_obstacle_detection folder to:
# /home/pi/ros2_ws/src/

# Or use scp:
scp -r rc_car_obstacle_detection pi@<pi_ip>:~/ros2_ws/src/
```

### 2. Build the Package

```bash
# SSH into your Pi
ssh pi@<pi_ip>

# Navigate to workspace
cd ~/ros2_ws

# Build
colcon build --packages-select rc_car_obstacle_detection

# Source
source install/setup.bash

# Add to bashrc for auto-sourcing
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

### 3. Verify UART is Enabled

```bash
# Check if UART device exists
ls -l /dev/ttyAMA0

# If not, enable UART
sudo nano /boot/firmware/config.txt

# Add these lines:
enable_uart=1
dtoverlay=disable-bt

# Reboot
sudo reboot
```

### 4. Set Permissions

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set permissions
sudo chmod 666 /dev/ttyAMA0

# Log out and back in for group changes to take effect
```

## Usage

### Launch Complete System

```bash
# Terminal 1: Launch your existing LiDAR driver
ros2 launch cspc_lidar_sdk_ros2 <your_lidar_launch_file>

# Terminal 2: Launch your existing IMU node
ros2 run imu_uart_node imu_uart_node

# Terminal 3: Launch obstacle detection system
ros2 launch rc_car_obstacle_detection obstacle_detection.launch.py

# Terminal 4 (optional): Monitor topics
ros2 topic echo /emergency_stop
```

### Or Launch Everything Together

Create a combined launch file in your workspace:

```bash
# Create combined launch
nano ~/ros2_ws/src/rc_car_obstacle_detection/launch/full_system.launch.py
```

### Manual Control via Safety Controller

The safety controller provides keyboard control:

**Steering:**
- `a` - Turn left
- `d` - Turn right
- `s` - Center steering

**Motor:**
- `1` - Low speed
- `2` - Medium speed
- `3` - High speed
- `p` - Stop
- `b` - Reverse
- `f` - Full forward (test)

**Safety:**
- `SPACE` - Emergency stop
- `r` - Reset emergency stop
- `q` - Quit

## ROS 2 Topics

### Published Topics
- `/emergency_stop` (std_msgs/Bool) - Emergency stop signal
- `/lidar/obstacle_detected` (std_msgs/Bool) - LiDAR obstacle flag
- `/lidar/closest_distance` (std_msgs/Float32) - Closest obstacle distance
- `/fusion/status` (std_msgs/String) - System status
- `/stm32/status` (std_msgs/String) - STM32 status messages

### Subscribed Topics
- `/scan` (sensor_msgs/LaserScan) - From cspc_lidar_sdk_ros2
- `/imu/data` (sensor_msgs/Imu) - From imu_uart_node
- `/stm32/command` (std_msgs/String) - Commands to STM32

## Configuration

Edit `config/params.yaml` to adjust:

```yaml
lidar_processor:
  detection_distance: 1.5      # Stop distance (meters)
  detection_angle: 60.0        # Detection cone (degrees)
  min_points_threshold: 5      # Minimum points to trigger
  scan_topic: "/scan"          # Your LiDAR topic

obstacle_fusion:
  lidar_timeout: 0.5           # LiDAR data timeout
  vision_timeout: 1.0          # Vision data timeout
  tilt_threshold: 30.0         # Maximum tilt angle
  imu_topic: "/imu/data"       # Your IMU topic
```

## Safety Features

1. **Vision-based Person Detection**: STM32 YOLO detects people and triggers emergency stop
2. **LiDAR Proximity Detection**: Stops car when obstacles are within detection distance
3. **Tilt Detection**: Stops car if excessive tilt is detected (rollover protection)
4. **Multi-sensor Fusion**: Combines all sensors for robust detection
5. **Manual Override**: Keyboard emergency stop always available

## Testing

### Test Individual Components

```bash
# Test LiDAR processor
ros2 run rc_car_obstacle_detection lidar_processor.py

# Test obstacle fusion
ros2 run rc_car_obstacle_detection obstacle_fusion.py

# Test STM32 bridge
ros2 run rc_car_obstacle_detection stm32_bridge.py

# Test safety controller
ros2 run rc_car_obstacle_detection safety_controller.py
```

### Monitor Topics

```bash
# Check if IMU data is coming in
ros2 topic echo /imu/data

# Check LiDAR scan
ros2 topic echo /scan

# Check obstacle detection
ros2 topic echo /lidar/obstacle_detected

# Check emergency stop
ros2 topic echo /emergency_stop

# Check system status
ros2 topic echo /fusion/status
```

### Visualize in RViz2

```bash
ros2 run rviz2 rviz2

# Add displays:
# - LaserScan → /scan
# - TF
```

## Troubleshooting

### UART Not Working
```bash
# Check if UART is enabled
ls -l /dev/ttyAMA0

# Test UART communication
sudo apt install minicom
minicom -D /dev/ttyAMA0 -b 115200

# Check if data is coming from STM32
cat /dev/ttyAMA0
```

### LiDAR Not Publishing
```bash
# Check if LiDAR node is running
ros2 node list

# Check LiDAR topic
ros2 topic list | grep scan
ros2 topic hz /scan
```

### IMU Data Not Received
```bash
# Check if imu_uart_node is running
ros2 node list | grep imu

# Check IMU topic
ros2 topic echo /imu/data
```

### Emergency Stop Not Working
```bash
# Manually trigger emergency stop
ros2 topic pub /emergency_stop std_msgs/Bool "data: true"

# Check if STM32 receives command
# Should see motor stop on car
```

### Permission Denied on /dev/ttyAMA0
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set permissions
sudo chmod 666 /dev/ttyAMA0

# Log out and back in
```

## STM32 Code

Your STM32 code is already set up correctly with:
- ✅ IMU calibration on startup
- ✅ UART communication (115200 baud)
- ✅ Person detection with emergency stop
- ✅ Manual control via UART commands
- ✅ PWM motor control

**No changes needed to STM32 code!**

## Performance

- **IMU Update Rate**: ~100Hz (from imu_uart_node)
- **LiDAR Update Rate**: ~10Hz (depends on your LiDAR)
- **Vision Update Rate**: ~5-10 FPS (STM32 YOLO)
- **Fusion Loop**: 10Hz
- **Emergency Stop Latency**: <100ms

## Next Steps

1. **Test each component individually** before running full system
2. **Calibrate detection distances** based on your car's speed
3. **Add data logging** for debugging
4. **Implement autonomous navigation** using obstacle data
5. **Add RViz visualization** for real-time monitoring

## License

MIT
