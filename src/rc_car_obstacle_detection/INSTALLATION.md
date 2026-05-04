# RC Car Obstacle Detection - Installation & Testing Guide

## Quick Start

### 1. Transfer Package to Raspberry Pi

From Windows PowerShell:
```powershell
scp -r C:\Users\david\rc_car_obstacle_detection pi@172.20.10.2:~/ros2_ws/src/
```

### 2. Build Package

On Raspberry Pi:
```bash
cd ~/ros2_ws
colcon build --packages-select rc_car_obstacle_detection
source install/setup.bash
```

### 3. Make Scripts Executable

```bash
chmod +x ~/ros2_ws/src/rc_car_obstacle_detection/scripts/*.py
```

### 4. Verify UART Permissions

```bash
sudo usermod -a -G dialout pi
sudo chmod 666 /dev/ttyAMA0
```

## Testing Sequence

### Test 1: Obstacle Detection Only

```bash
# Terminal 1: Start LiDAR
ros2 run cspc_lidar cspc_lidar

# Terminal 2: Launch obstacle detection
ros2 launch rc_car_obstacle_detection obstacle_detection.launch.py

# Terminal 3: Monitor topics
ros2 topic echo /lidar/obstacle_detected
ros2 topic echo /emergency_stop
ros2 topic echo /obstacle_cloud
```

### Test 2: Full System with Odometry

```bash
# Single command launches everything
ros2 launch rc_car_obstacle_detection full_system.launch.py

# In another terminal, verify topics
ros2 topic list
ros2 topic hz /odometry/filtered
ros2 topic hz /obstacle_cloud
```

### Test 3: With SLAM

```bash
ros2 launch rc_car_obstacle_detection full_system.launch.py enable_slam:=true

# In RViz2
ros2 run rviz2 rviz2
# Add: Map, LaserScan (/scan), PointCloud2 (/obstacle_cloud), TF
```

## Key Topics

- `/scan` - LiDAR scan data
- `/imu/data` - IMU data (for odometry only)
- `/odom_rf2o` - Laser odometry
- `/odometry/filtered` - EKF fused odometry
- `/lidar/obstacle_detected` - Boolean obstacle flag
- `/lidar/closest_distance` - Distance to nearest obstacle
- `/lidar/obstacle_points` - Obstacle point cloud
- `/obstacle_cloud` - Combined obstacles for costmap
- `/obstacle_markers` - Visualization markers
- `/emergency_stop` - Emergency stop signal
- `/stm32/command` - Commands to STM32
- `/stm32/status` - Status from STM32

## Keyboard Controls (safety_controller)

- **Steering:** a (left), d (right), s (center)
- **Motor:** 1 (low), 2 (med), 3 (high), p (stop), b (reverse), f (full)
- **Safety:** SPACE (emergency), r (reset), q (quit)

## Troubleshooting

### No LiDAR data
```bash
ros2 topic hz /scan
# If no output, check LiDAR connection
```

### No IMU data
```bash
ros2 topic hz /imu/data
# Check UART connection and permissions
```

### Emergency stop not working
```bash
ros2 topic echo /emergency_stop
# Place obstacle in front, should see "true"
```

### Costmap not showing obstacles
```bash
ros2 topic echo /obstacle_cloud
# Should see point cloud data when obstacles detected
```

## Performance Expectations

- IMU Rate: ~100Hz
- LiDAR Rate: ~10Hz
- Odometry Rate: ~100Hz (EKF output)
- Obstacle Detection: 10Hz
- Emergency Stop Latency: <100ms

## Next Steps

1. Test odometry system (IMU + EKF + rf2o)
2. Add obstacle detection incrementally
3. Verify costmap publishing in RViz
4. Install SLAM (slam_toolbox recommended)
5. Build map of environment
6. Install nav2 for autonomous navigation
