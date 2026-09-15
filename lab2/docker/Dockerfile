FROM osrf/ros:noetic-desktop

SHELL ["/bin/bash", "-c"]
LABEL authors="lynxmotion-arm-lab"

# Arguments for user creation (with defaults; override to match host UID/GID)
ARG USERNAME=robotuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG DEBIAN_FRONTEND=noninteractive

# Base tooling needed to create the dev user
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with passwordless sudo. Matching UID/GID to the host
# user avoids file-permission mismatches since the whole repo is bind-mounted.
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m --shell /bin/bash $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# catkin_make (the traditional catkin build tool) ships with every ROS 1
# install already
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-rosdep \
    ros-noetic-joint-state-publisher-gui \
    ros-noetic-robot-state-publisher \
    ros-noetic-rviz \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME
WORKDIR /home/$USERNAME

# Auto-source ROS 1 on every new shell.
RUN echo "# Auto-source ROS 1 Noetic" >> ~/.bashrc && \
    echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc && \
    echo "export ROS_MASTER_URI=\${ROS_MASTER_URI:-http://localhost:11311}" >> ~/.bashrc && \
    echo "echo 'lynxmotion arm lab -- ROS 1 Noetic'" >> ~/.bashrc

CMD ["/bin/bash"]
