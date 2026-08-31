#!/bin/bash
set -e

# One-time host-side setup for these turtlesim dev containers, on a
# Debian/Ubuntu host. Installs Docker Engine + the Compose plugin, and adds
# the current user to the `docker` group so VS Code's Dev Containers
# extension can talk to the daemon without sudo.
#
# Run once per machine:
#   bash scripts/host-setup-linux.sh

echo "======================================"
echo "turtlesim dev container -- host setup"
echo "======================================"

if command -v docker >/dev/null 2>&1; then
    echo "Docker is already installed: $(docker --version)"
else
    echo "Installing Docker Engine + Compose plugin..."

    # Remove old/distro docker packages that conflict with docker-ce (ignore
    # failures — most hosts won't have any of these installed).
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    sudo apt-get update
    sudo apt-get install -y ca-certificates curl

    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    echo "Docker installed: $(docker --version)"
fi

if id -nG "$USER" | grep -qw docker; then
    echo "$USER is already in the docker group."
else
    echo "Adding $USER to the docker group (lets you run docker without sudo)..."
    sudo usermod -aG docker "$USER"
    echo "NOTE: log out/in (or run 'newgrp docker') for the new group membership to take effect."
fi

echo ""
echo "======================================"
echo "Host setup complete."
echo ""
echo "Remaining one-time steps:"
echo "  1. Install the VS Code 'Dev Containers' extension (ms-vscode-remote.remote-containers)."
echo "  2. Each login session, before using turtlesim from inside the container, run:"
echo "       xhost +local:docker"
echo "     (see docs/x11-setup.md for details, and for macOS/Windows steps)"
echo "======================================"
