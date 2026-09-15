#!/bin/bash
# Runs once when the container is created (devcontainer postCreateCommand).
# Wires up ~/catkin_ws as a symlink into the mounted repo (so edits made on
# the host or in the container stay in sync), resolves each package's own
# rosdep dependencies, and does an initial full build so the lab works
# immediately.
set -e

source /opt/ros/noetic/setup.bash

ln -sfn "$PWD/catkin_ws" ~/catkin_ws

sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths ~/catkin_ws/src --ignore-src -r -y

cd ~/catkin_ws
catkin_make

grep -qxF 'source ~/catkin_ws/devel/setup.bash' ~/.bashrc || \
    echo 'source ~/catkin_ws/devel/setup.bash' >> ~/.bashrc

grep -qxF 'cd ~/catkin_ws' ~/.bashrc || \
    echo 'cd ~/catkin_ws' >> ~/.bashrc
