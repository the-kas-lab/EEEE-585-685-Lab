FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-c"]
LABEL authors="husky-lab"

# Arguments for user creation (with defaults; override to match host UID/GID)
ARG USERNAME=robotuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    ca-certificates \
    iputils-ping \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user with passwordless sudo, UID matched to the host user because
# the repo is bind-mounted.
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m --shell /bin/bash $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# twist_mux: the same command arbitration node that runs on the Husky (the
# simulator uses it with the robot's configuration).
# teleop_twist_keyboard: the stock ROS 2 teleop node students try in Task 1.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-twist-mux \
    ros-humble-teleop-twist-keyboard \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

# The Lab 6 checker (handout, Lab Setup).
COPY lab6-check /usr/local/bin/lab6-check
RUN sed -i 's/\r$//' /usr/local/bin/lab6-check && chmod 755 /usr/local/bin/lab6-check

USER $USERNAME
WORKDIR /home/$USERNAME

RUN echo "# Auto-source ROS 2 Humble" >> ~/.bashrc && \
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-0}" >> ~/.bashrc && \
    echo "echo 'Husky lab -- ROS 2 Humble'" >> ~/.bashrc

CMD ["/bin/bash"]
