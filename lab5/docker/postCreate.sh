#!/bin/bash
# Runs once when the container is created (devcontainer postCreateCommand).
# Wires up ~/catkin_ws as a symlink into the mounted repo (so edits made on
# the host or in the container stay in sync) and does an initial full build
# so the lab works immediately.
#
# No apt and no rosdep here: every dependency is baked into the image, so
# creating the container needs no network and cannot fail on a mirror.
set -e

# A Windows checkout without .gitattributes hands us CRLF files, and a
# "#!/usr/bin/env python3\r" shebang makes rosrun fail with
# "python3\r: No such file or directory". Strip CRs from everything that is
# executed or parsed inside the container.
find "$PWD/catkin_ws/src" -type f \
    \( -name '*.py' -o -name '*.sh' -o -name '*.launch' -o -name '*.xacro' \
       -o -name '*.yaml' -o -name '*.xml' -o -name '*.world' -o -name 'CMakeLists.txt' \) \
    -exec sed -i 's/\r$//' {} +

# rosrun only runs files with the executable bit; Windows checkouts and some
# editors drop it.
find "$PWD/catkin_ws/src" -type f -path '*/scripts/*.py' -exec chmod +x {} +

# /opt/rosaria/setup.bash chains to /opt/ros/noetic, so the workspace built
# below overlays both and `rosrun rosaria RosAria` keeps working.
source /opt/rosaria/setup.bash

ln -sfn "$PWD/catkin_ws" ~/catkin_ws

cd ~/catkin_ws
catkin_make

grep -qxF '[ -f ~/catkin_ws/devel/setup.bash ] && source ~/catkin_ws/devel/setup.bash' ~/.bashrc || \
    echo '[ -f ~/catkin_ws/devel/setup.bash ] && source ~/catkin_ws/devel/setup.bash' >> ~/.bashrc

grep -qxF 'cd ~/catkin_ws' ~/.bashrc || \
    echo 'cd ~/catkin_ws' >> ~/.bashrc

echo
echo "AmigoBot workspace built. Open http://localhost:6080 for the desktop."
