cmake_minimum_required(VERSION 2.8.3)
project(lynxmotion_ssc32)

find_package(catkin REQUIRED COMPONENTS roscpp sensor_msgs trajectory_msgs joint_state_publisher)

catkin_package(
   INCLUDE_DIRS include
   LIBRARIES ssc32
   CATKIN_DEPENDS roscpp sensor_msgs joint_state_publisher
)

include_directories(include
  ${catkin_INCLUDE_DIRS}
)

add_library(ssc32 src/ssc32.cpp)
target_link_libraries(ssc32 ${catkin_LIBRARIES})

#add_library(ssc32_driver src/ssc32_driver.cpp)
#target_link_libraries(ssc32_driver ssc32 ${catkin_LIBRARIES})

#add_executable(ssc32_node src/ssc32_node.cpp)
#target_link_libraries(ssc32_node ssc32_driver ${catkin_LIBRARIES})

#add_executable(test_ssc32 src/test_ssc32.cpp)
#target_link_libraries(test_ssc32 ssc32_driver ${catkin_LIBRARIES})

add_executable(joint_controller src/joint_controller.cpp)
target_link_libraries(joint_controller ssc32 ${catkin_LIBRARIES})

install(TARGETS ssc32 joint_controller
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY include/${PROJECT_NAME}/
  DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
)
