cmake_minimum_required(VERSION 3.8)
project(rc_car_obstacle_detection)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install Python scripts
install(PROGRAMS
  scripts/stm32_bridge.py
  scripts/lidar_processor.py
  scripts/obstacle_fusion.py
  scripts/safety_controller.py
  scripts/costmap_publisher.py
  scripts/goal_sender.py
  rc_car_obstacle_detection/rf2o_wrapper.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
 )

install(DIRECTORY
  cartographer_config
  DESTINATION share/${PROJECT_NAME}
) 
ament_package()
