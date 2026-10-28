cmake_minimum_required(VERSION 3.0.2)
project(amigo_tools)

find_package(catkin REQUIRED COMPONENTS rospy std_msgs sensor_msgs nav_msgs geometry_msgs)
catkin_package(CATKIN_DEPENDS rospy std_msgs sensor_msgs nav_msgs geometry_msgs)

catkin_install_python(PROGRAMS
  scripts/wheel_velocity_publisher.py
  scripts/sonar_aggregator.py
  scripts/sonar_splitter.py
  scripts/odom_error_logger.py
  scripts/drive_pattern.py
  scripts/verify_interface.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

# Offline consistency check: amigo_params.yaml vs the URDF vs the hardcoded
# fallbacks in the nodes.  No master, no Gazebo, no robot.
#   catkin_make run_tests_amigo_tools
if(CATKIN_ENABLE_TESTING)
  catkin_add_nosetests(test/test_param_consistency.py)
endif()
