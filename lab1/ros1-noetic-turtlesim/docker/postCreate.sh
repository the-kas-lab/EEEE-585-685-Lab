#!/bin/bash
# Runs once when the container is created (devcontainer postCreateCommand).
# Wires up ~/catkin_ws as a symlink into the mounted repo (so packages
# students create live inside the container are visible on the host, and
# vice versa) and does an initial build so a fresh workspace is ready to go.
set -e

source /opt/ros/noetic/setup.bash

ln -sfn "$PWD/catkin_ws" ~/catkin_ws

cd ~/catkin_ws
catkin_make

grep -qxF 'source ~/catkin_ws/devel/setup.bash' ~/.bashrc || \
    echo 'source ~/catkin_ws/devel/setup.bash' >> ~/.bashrc

grep -qxF 'cd ~/catkin_ws' ~/.bashrc || \
    echo 'cd ~/catkin_ws' >> ~/.bashrc
