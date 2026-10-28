# AmigoBot lab (EEEE-585/685 Lab 5) -- ROS 1 Noetic, Gazebo 11, ROSARIA.
#
# Base image: the OFFICIAL multi-arch ros:noetic-ros-base, not osrf/ros:noetic-*.
#  - osrf/ros:noetic-desktop(-full) is amd64-only, so on Apple Silicon it runs
#    under emulation -- tolerable for RViz, unusable for Gazebo.
#  - ros:noetic-ros-base points apt at snapshots.ros.org/noetic/final, the
#    frozen post-EOL archive, signed with a current key. Images that still
#    point at packages.ros.org fail `apt-get update` with EXPKEYSIG.
FROM ros:noetic-ros-base

SHELL ["/bin/bash", "-c"]
LABEL authors="amigobot-lab"

ARG USERNAME=robotuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG DEBIAN_FRONTEND=noninteractive

# Third-party robot driver, pinned by commit so an upstream push can never
# change what students get. Bump deliberately, then re-run the TA checklist.
#   AriaCoda: maintained fork of MobileRobots' ARIA (GPLv2)
#   rosaria:  ROS 1 wrapper around ARIA (BSD)
ARG ARIACODA_REPO=https://github.com/reedhedges/AriaCoda.git
ARG ARIACODA_SHA=b0d02e05888f9317eb2cedbac2b6f14deabdd6ee
ARG ROSARIA_REPO=https://github.com/amor-ros-pkg/rosaria.git
ARG ROSARIA_SHA=c289f1d400f4e41601cf8a4a8fa7f3cfd741f8ea

# Base tooling, plus the network tools used to find and reach the robot
# (ping, nc for "is port 8101 open?", dig for "does amigo3.rit.edu resolve?").
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    ca-certificates \
    git \
    build-essential \
    iputils-ping \
    iproute2 \
    net-tools \
    netcat-openbsd \
    dnsutils \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with passwordless sudo. Matching UID/GID to the host
# user avoids file-permission mismatches since the whole repo is bind-mounted.
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m --shell /bin/bash $USERNAME \
    && usermod -aG dialout $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# ROS: desktop (RViz, rqt, tf tools) + Gazebo 11 and everything the course
# packages under catkin_ws/src depend on, so postCreate never needs apt or
# rosdep (both need network, and both have failed in lab sections before).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-desktop \
    ros-noetic-gazebo-ros-pkgs \
    ros-noetic-gazebo-plugins \
    ros-noetic-xacro \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher \
    ros-noetic-joint-state-publisher-gui \
    ros-noetic-rqt-robot-steering \
    ros-noetic-rqt-tf-tree \
    ros-noetic-teleop-twist-keyboard \
    liburdfdom-tools \
    python3-nose \
    && rm -rf /var/lib/apt/lists/*

# In-container desktop: a virtual X display (TigerVNC), a window manager, and
# noVNC so the desktop opens in any web browser. No host X server (XQuartz,
# VcXsrv, xhost) is involved, so it behaves the same on every host OS.
# Rendering is Mesa llvmpipe (software), which Gazebo and RViz both run on.
# feh: fluxbox sets its wallpaper through fbsetbg, which pops an error dialog
# over the desktop on every start if it finds no wallpaper tool to call.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tigervnc-standalone-server \
    novnc \
    python3-websockify \
    fluxbox \
    feh \
    xterm \
    x11-utils \
    mesa-utils \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Opening http://localhost:6080/ goes straight to a connected, auto-resizing
# desktop instead of noVNC's file listing.
RUN printf '%s\n' \
    '<!DOCTYPE html><meta charset="utf-8"><title>AmigoBot desktop</title>' \
    '<meta http-equiv="refresh" content="0; url=vnc.html?autoconnect=true&resize=remote&reconnect=true&reconnect_delay=2000">' \
    '<a href="vnc.html?autoconnect=true&resize=remote&reconnect=true">Open the desktop</a>' \
    > /usr/share/novnc/index.html

# AriaCoda -> /usr/local (lib, headers, params/amigo-sh.p, ariaDemo).
# install-default + install-utils skips install-doc, which needs doxygen.
RUN git clone "$ARIACODA_REPO" /tmp/AriaCoda \
    && cd /tmp/AriaCoda \
    && git checkout --quiet "$ARIACODA_SHA" \
    && make -j"$(nproc)" \
    && make install-default install-utils \
    && ldconfig \
    && rm -rf /tmp/AriaCoda

# rosaria -> an install-space underlay at /opt/rosaria. Students' catkin_ws
# overlays it, so `rosrun rosaria RosAria` works without cloning anything.
RUN mkdir -p /tmp/rosaria_ws/src \
    && git clone "$ROSARIA_REPO" /tmp/rosaria_ws/src/rosaria \
    && cd /tmp/rosaria_ws/src/rosaria \
    && git checkout --quiet "$ROSARIA_SHA" \
    && cd /tmp/rosaria_ws \
    && source /opt/ros/noetic/setup.bash \
    && catkin_make install -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/rosaria \
    && rm -rf /tmp/rosaria_ws

# sed: a Windows checkout without .gitattributes hands us CRLF files, and a
# CRLF entrypoint ("/bin/bash^M: bad interpreter") stops the container from
# starting at all.
COPY start-desktop.sh /usr/local/bin/start-desktop
COPY entrypoint.sh /usr/local/bin/amigo-entrypoint
RUN sed -i 's/\r$//' /usr/local/bin/start-desktop /usr/local/bin/amigo-entrypoint \
    && chmod 755 /usr/local/bin/start-desktop /usr/local/bin/amigo-entrypoint

# ROS networking: everything runs inside this one container, so pin the node
# address to localhost. Without it, nodes advertise the container's random
# hostname, which is fine until something tries to resolve it.
#
# DISABLE_ROS1_EOL_WARNINGS: Noetic's final RViz opens a *modal* "ROS 1
# End-of-Life" dialog on every start and blocks until someone clicks OK --
# behind Gazebo's window, that reads as "RViz is frozen".
ENV ROS_MASTER_URI=http://localhost:11311 \
    ROS_HOSTNAME=localhost \
    DISABLE_ROS1_EOL_WARNINGS=1 \
    DISPLAY=:1 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    QT_X11_NO_MITSHM=1

USER $USERNAME
WORKDIR /home/$USERNAME

# Auto-source ROS 1 + the ROSARIA underlay on every new shell.
RUN echo "# Auto-source ROS 1 Noetic + ROSARIA (/opt/rosaria chains to /opt/ros/noetic)" >> ~/.bashrc && \
    echo "source /opt/rosaria/setup.bash" >> ~/.bashrc && \
    echo "echo 'AmigoBot lab -- ROS 1 Noetic.  Desktop: http://localhost:6080'" >> ~/.bashrc

ENTRYPOINT ["/usr/local/bin/amigo-entrypoint"]
CMD ["sleep", "infinity"]
