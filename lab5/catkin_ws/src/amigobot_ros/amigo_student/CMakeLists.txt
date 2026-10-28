cmake_minimum_required(VERSION 3.0.2)
project(amigo_student)

find_package(catkin REQUIRED COMPONENTS rospy std_msgs sensor_msgs nav_msgs geometry_msgs)
catkin_package(CATKIN_DEPENDS rospy std_msgs sensor_msgs nav_msgs geometry_msgs)

catkin_install_python(PROGRAMS
  scripts/turn_circle.py
  scripts/sensor_listener.py
  scripts/my_odom.py
  scripts/wander.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

# ---------------------------------------------------------------------------
# Writing the nodes in C++ instead is fine -- the topics and message types are
# identical.  Add <depend>roscpp</depend> to package.xml, add roscpp to the
# COMPONENTS list in the find_package() call above, put the sources in src/,
# and uncomment:
#
# include_directories(${catkin_INCLUDE_DIRS})
# add_executable(turn_circle src/turn_circle.cpp)
# target_link_libraries(turn_circle ${catkin_LIBRARIES})
# install(TARGETS turn_circle
#         RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
#
# Mixing the two is allowed: nothing downstream cares which language published
# a message.
# ---------------------------------------------------------------------------
