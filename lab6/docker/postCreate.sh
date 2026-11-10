#!/bin/bash
# Runs once when the container is created (devcontainer postCreateCommand).
# Wires up ~/ros2_ws as a symlink into the mounted repo (so packages
# students create inside the container are visible on the host, and vice
# versa), resolves each package's own rosdep dependencies, and does an
# initial build so the simulator is ready to go.
set -e

source /opt/ros/humble/setup.bash

ln -sfn "$PWD/ros2_ws" ~/ros2_ws

sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths ~/ros2_ws/src --ignore-src -r -y

# No --symlink-install: on Windows/macOS hosts the workspace is a Docker
# Desktop bind mount, where creating symlinks is unreliable. Rebuild after
# editing a package instead.
cd ~/ros2_ws
colcon build

grep -qxF 'source ~/ros2_ws/install/setup.bash' ~/.bashrc || \
    echo 'source ~/ros2_ws/install/setup.bash' >> ~/.bashrc

grep -qxF 'cd ~/ros2_ws' ~/.bashrc || \
    echo 'cd ~/ros2_ws' >> ~/.bashrc
