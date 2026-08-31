#!/bin/bash
# Runs once when the container is created (devcontainer postCreateCommand).
# Wires up ~/ros2_ws as a symlink into the mounted repo (so packages
# students create live inside the container are visible on the host, and
# vice versa) and does an initial build so a fresh workspace is ready to go.
set -e

source /opt/ros/humble/setup.bash

ln -sfn "$PWD/ros2_ws" ~/ros2_ws

cd ~/ros2_ws
colcon build

grep -qxF 'source ~/ros2_ws/install/setup.bash' ~/.bashrc || \
    echo 'source ~/ros2_ws/install/setup.bash' >> ~/.bashrc

grep -qxF 'cd ~/ros2_ws' ~/.bashrc || \
    echo 'cd ~/ros2_ws' >> ~/.bashrc
