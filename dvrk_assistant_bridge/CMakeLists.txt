cmake_minimum_required(VERSION 3.8)
project(dvrk_assistant_bridge)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(bridge src/bridge_node.cpp)
ament_target_dependencies(bridge
  rclcpp
  std_msgs
  sensor_msgs
)

install(TARGETS bridge
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES
  README.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
