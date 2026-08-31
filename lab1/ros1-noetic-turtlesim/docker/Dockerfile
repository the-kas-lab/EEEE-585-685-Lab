FROM osrf/ros:noetic-desktop

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
# for turtlesim itself. catkin_make (the traditional build tool) ships with
# every ROS 1 install already: this lab also uses a ~/catkin_ws for live
# package-creation / custom-message exercises.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-turtlesim \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME
WORKDIR /home/$USERNAME

# Auto-source ROS 1 on every new shell.
RUN echo "# Auto-source ROS 1 Noetic" >> ~/.bashrc && \
    echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc && \
    echo "export ROS_MASTER_URI=\${ROS_MASTER_URI:-http://localhost:11311}" >> ~/.bashrc && \
    echo "echo 'turtlesim tutorial container -- ROS 1 Noetic'" >> ~/.bashrc

CMD ["/bin/bash"]
