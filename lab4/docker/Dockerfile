FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-c"]
LABEL authors="ur5e-arm-lab"

# Arguments for user creation (with defaults; override to match host UID/GID)
ARG USERNAME=robotuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG DEBIAN_FRONTEND=noninteractive

# Base tooling needed to create the dev user, plus the network tools the lab
# uses to find and reach the real robot (ping, arp, ip).
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    ca-certificates \
    iputils-ping \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with passwordless sudo. Matching UID/GID to the host
# user avoids file-permission mismatches since the whole repo is bind-mounted.
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m --shell /bin/bash $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# ros-humble-ur is the Universal Robots metapackage: ur_robot_driver (incl.
# example_move.py and the fake-hardware sim), ur_moveit_config and
# ur_description. moveit adds the RViz MotionPlanning / Trajectory Slider
# panels, ros2controlcli provides `ros2 control list_controllers`.
# turtlesim is kept for the "Introduction to ROS 2" pre-lab.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-ur \
    ros-humble-moveit \
    ros-humble-ros2controlcli \
    ros-humble-turtlesim \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME
WORKDIR /home/$USERNAME

# Auto-source ROS 2 on every new shell.
RUN echo "# Auto-source ROS 2 Humble" >> ~/.bashrc && \
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-0}" >> ~/.bashrc && \
    echo "echo 'UR5e arm lab -- ROS 2 Humble'" >> ~/.bashrc

CMD ["/bin/bash"]
