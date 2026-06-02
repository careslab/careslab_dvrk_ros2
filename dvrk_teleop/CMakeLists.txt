cmake_minimum_required(VERSION 3.8)
project(dvrk_teleop)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)

install(PROGRAMS
  scripts/teleoperation.py
  scripts/arm.py
  scripts/mtm.py
  scripts/psm.py
  scripts/__common_imports__.py
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES
  README.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
