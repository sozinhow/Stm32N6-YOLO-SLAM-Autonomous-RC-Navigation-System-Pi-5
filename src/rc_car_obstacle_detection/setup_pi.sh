#!/bin/bash
# Quick setup script for RC Car Obstacle Detection System
# Run this on your Raspberry Pi 5

set -e  # Exit on error

echo "=========================================="
echo "RC Car Obstacle Detection Setup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "ros2_ws" ]; then
    echo "Creating ros2_ws directory..."
    mkdir -p ~/ros2_ws/src
fi

cd ~/ros2_ws/src

# Check if package already exists
if [ -d "rc_car_obstacle_detection" ]; then
    echo "Package already exists. Removing old version..."
    rm -rf rc_car_obstacle_detection
fi

echo "Creating package structure..."
mkdir -p rc_car_obstacle_detection/{scripts,launch,config,resource,rc_car_obstacle_detection}

echo "Package structure created!"
echo ""
echo "Next steps:"
echo "1. Copy the package files from your Windows machine"
echo "2. Run: cd ~/ros2_ws"
echo "3. Run: colcon build --packages-select rc_car_obstacle_detection"
echo "4. Run: source install/setup.bash"
echo ""
echo "Or use the transfer script to copy files via SCP"
