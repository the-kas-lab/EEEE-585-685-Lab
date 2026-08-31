FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-c"]
LABEL authors="turtlesim-devcontainer-tutorial"

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
# user avoids file-permission mismatches if you ever bind-mount files in.
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m --shell /bin/bash $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# turtlesim ships both the simulator (turtlesim_node) and the keyboard
# teleop (turtle_teleop_key) in a single apt package -- no build required
# for turtlesim itself. colcon is installed anyway: this lab also uses a
# ~/ros2_ws for live package-creation / custom-message exercises.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-turtlesim \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME
WORKDIR /home/$USERNAME

# Auto-source ROS 2 on every new shell.
RUN echo "# Auto-source ROS 2 Humble" >> ~/.bashrc && \
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-0}" >> ~/.bashrc && \
    echo "echo 'turtlesim tutorial container -- ROS 2 Humble'" >> ~/.bashrc

CMD ["/bin/bash"]
