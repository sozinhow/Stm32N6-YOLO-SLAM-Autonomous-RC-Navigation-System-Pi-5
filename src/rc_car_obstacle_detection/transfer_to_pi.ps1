# PowerShell script to transfer package to Pi
# Run this in PowerShell: .\transfer_to_pi.ps1

$PI_IP = "172.20.10.2"
$PI_USER = "pi"
$LOCAL_PATH = "C:\Users\david\rc_car_obstacle_detection"
$REMOTE_PATH = "/home/pi/ros2_ws/src/"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Transferring RC Car Package to Pi" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pi IP: $PI_IP"
Write-Host "Local Path: $LOCAL_PATH"
Write-Host "Remote Path: $REMOTE_PATH"
Write-Host ""

# Check if local path exists
if (-not (Test-Path $LOCAL_PATH)) {
    Write-Host "Error: Local path not found!" -ForegroundColor Red
    exit 1
}

# Transfer using SCP
Write-Host "Copying files to Pi..." -ForegroundColor Yellow
scp -r $LOCAL_PATH "${PI_USER}@${PI_IP}:${REMOTE_PATH}"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Transfer complete!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. SSH into Pi: ssh pi@$PI_IP"
    Write-Host "2. Build package: cd ~/ros2_ws && colcon build --packages-select rc_car_obstacle_detection"
    Write-Host "3. Source workspace: source install/setup.bash"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Transfer failed! Check your connection." -ForegroundColor Red
}

Read-Host "Press Enter to exit"
