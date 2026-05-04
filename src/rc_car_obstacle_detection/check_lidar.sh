#!/bin/bash
# Quick diagnostic script to check your LiDAR setup
# Run this on your Pi while LiDAR is running

echo "=========================================="
echo "LiDAR Diagnostic Check"
echo "=========================================="
echo ""

echo "1. Checking ROS 2 topics..."
ros2 topic list | grep -E "(scan|lidar|laser)"

echo ""
echo "2. Checking topic info..."
ros2 topic info /scan 2>/dev/null || echo "No /scan topic found"

echo ""
echo "3. Checking topic type..."
ros2 topic type /scan 2>/dev/null || echo "No /scan topic found"

echo ""
echo "4. Checking topic frequency..."
ros2 topic hz /scan --window 10 2>/dev/null &
TOPIC_PID=$!
sleep 5
kill $TOPIC_PID 2>/dev/null

echo ""
echo "5. Sample scan data (first message)..."
timeout 2 ros2 topic echo /scan --once 2>/dev/null || echo "No data received"

echo ""
echo "=========================================="
echo "Diagnostic complete!"
echo "=========================================="
