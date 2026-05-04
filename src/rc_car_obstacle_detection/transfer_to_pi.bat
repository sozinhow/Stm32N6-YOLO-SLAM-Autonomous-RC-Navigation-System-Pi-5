@echo off
REM Transfer RC Car package to Raspberry Pi
REM Run this on Windows PowerShell or CMD

set PI_IP=172.20.10.2
set PI_USER=pi
set PI_PASS=1
set LOCAL_PATH=C:\Users\david\rc_car_obstacle_detection
set REMOTE_PATH=/home/pi/ros2_ws/src/

echo ==========================================
echo Transferring RC Car Package to Pi
echo ==========================================
echo.
echo Pi IP: %PI_IP%
echo Local Path: %LOCAL_PATH%
echo Remote Path: %REMOTE_PATH%
echo.

REM Using SCP to transfer files
echo Copying files to Pi...
scp -r "%LOCAL_PATH%" %PI_USER%@%PI_IP%:%REMOTE_PATH%

echo.
echo ==========================================
echo Transfer complete!
echo ==========================================
echo.
echo Next steps:
echo 1. SSH into Pi: ssh pi@%PI_IP%
echo 2. Build package: cd ~/ros2_ws ^&^& colcon build --packages-select rc_car_obstacle_detection
echo 3. Source workspace: source install/setup.bash
echo.
pause
