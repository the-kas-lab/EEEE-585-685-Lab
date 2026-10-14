# UR5e arm lab

ROS 2 Humble only. Lab handout:
[docs/Robotics_Lab4_instruction_2026.pdf](docs/Robotics_Lab4_instruction_2026.pdf).

The container has everything the handout installs on the lab machines
(`ros-humble-ur`: the UR driver, its fake-hardware simulator, the UR5e MoveIt
config and description) plus MoveIt's RViz panels, the `ros2 control` CLI,
`ping`/`arp`, and turtlesim for the ROS 2 pre-lab. You can do the whole
simulation part of the lab on your own laptop, on any OS.

## How it's organized

Same shape as [lab2](../lab2/), with a colcon workspace instead of catkin:

```
lab4/
├── docker/
│   ├── Dockerfile
│   └── postCreate.sh           # wires up ~/ros2_ws, runs the first build
├── .devcontainer/
│   ├── linux/devcontainer.json
│   ├── macos/devcontainer.json
│   └── windows/devcontainer.json
├── docs/
│   ├── x11-setup.md            # getting RViz onto your screen, per OS
│   └── real-robot.md           # driving the physical UR5e from the container
└── ros2_ws/
    └── src/                    # your packages go here
```

The `ros2_ws/` you see above **is** the workspace: when the container starts,
`~/ros2_ws` inside it is a symlink straight back to `ros2_ws/` in this mounted
repo (and a new terminal drops you there directly), so anything you create or
edit shows up on your host too, and vice versa.

## Prerequisites (all OSes)

1. **Docker** — Linux: Docker Engine, via
   [lab1/scripts/host-setup-linux.sh](../lab1/scripts/host-setup-linux.sh);
   macOS/Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/).
   The image is large (~5 GB) — build it on a good connection, not in the lab.
2. **VS Code** + the **Dev Containers** extension
   ([`ms-vscode-remote.remote-containers`](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)).
3. **X11 / GUI forwarding**, so RViz can reach your screen — follow
   [docs/x11-setup.md](docs/x11-setup.md) for your OS. **Windows:** uncheck
   "Native opengl" in XLaunch, or RViz 2 will crash / show a black view.

## Quick start

1. Do the prerequisites above once per machine.
2. Open **this folder** (`lab4/`) in VS Code, not the repo root.
3. **Dev Containers: Reopen in Container**, pick your OS's config.
4. Wait for `postCreateCommand` to finish — it resolves your packages'
   dependencies via `rosdep` and runs an initial `colcon build`, so the
   workspace is ready as soon as the container is up.

Every new terminal starts `cd`'d into `~/ros2_ws` with ROS 2 and the
workspace's `install/setup.bash` already sourced. Open as many as you need
(VS Code: **+** in the terminal panel, or right-click → Split Terminal) —
they all attach to the same running container.

## Pre-lab: turtlesim on ROS 2

Part 1 of this lab, [docs/ROS2_Introduction.pdf](docs/ROS2_Introduction.pdf),
works entirely in this container — turtlesim, rqt / rqt_graph, `ros2 bag`,
`git`, and the custom-message build tools are all installed. Do the
tutorials' workspace steps in `~/ros2_ws` and skip any `sudo apt install`
they ask for.

Unlike ROS 1, ROS 2 has no central master — nodes find each other directly,
so there's no `roscore` step:

```bash
ros2 run turtlesim turtlesim_node      # terminal 1 — a turtle window pops up
ros2 run turtlesim turtle_teleop_key   # terminal 2 — click here, use arrow keys
```

## Simulation (handout §4–5)

MoveIt and RViz (§4.2):

```bash
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur5e launch_rviz:=true
```

The fake-hardware driver (§5.1), and commanding it (§5.2) from a second
terminal:

```bash
# terminal 1
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=yyy.yyy.yyy.yyy use_fake_hardware:=true launch_rviz:=true

# terminal 2
ros2 control list_controllers
ros2 launch ur_robot_driver test_scaled_joint_trajectory_controller.launch.py
ros2 run ur_robot_driver example_move.py
```

RViz is rendered in software inside the container on Windows/macOS, so it's
usable but not fast — give MoveIt a few seconds after launching before you
start dragging the interactive markers.

## Your pick-and-place package

Create packages under `~/ros2_ws/src` **from a container terminal**, so they
land in the mounted repo:

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python ur5e_pick_place --dependencies rclpy
# copy example_move.py in and adapt it (handout §5.2):
cp /opt/ros/humble/lib/ur_robot_driver/example_move.py ur5e_pick_place/ur5e_pick_place/
```

Register your script under `entry_points` in the package's `setup.py`, then
build and run:

```bash
cd ~/ros2_ws
colcon build --packages-select ur5e_pick_place
source install/setup.bash
ros2 run ur5e_pick_place <your_script>
```

Rebuild after every edit — the workspace is built without
`--symlink-install` (creating symlinks on a Windows/macOS bind mount is
unreliable), so `install/` holds a copy of your code, not a link to it.

## Real robot (handout §6)

On the lab laptop nothing changes — it runs ROS 2 natively. To drive the
UR5e from **this container** on your own laptop, see
[docs/real-robot.md](docs/real-robot.md): Windows and macOS need one extra
launch argument and a firewall rule, because the robot connects *back* to
your laptop.

## Troubleshooting

- **No GUI window appears** — almost always the host-side X11 setup, not the
  container. Re-check [docs/x11-setup.md](docs/x11-setup.md); on Windows,
  confirm VcXsrv is running (tray icon) with "Disable access control"
  checked.
- **RViz opens, then crashes (`Segmentation fault`, `GLXBadContext`,
  `failed to create drawable`), or the 3D view is black** — Windows: restart
  VcXsrv with "Native opengl" *unchecked*. Then check
  `echo $LIBGL_ALWAYS_SOFTWARE` prints `1`; if not, you're in a container
  built from an older config — **Dev Containers: Rebuild Container**.
- **`postCreate.sh: line N: $'\r': command not found`** or **`/usr/bin/env:
  'python3\r': No such file or directory`** — a script was checked out with
  Windows line endings. The `postCreateCommand` already strips them from
  `postCreate.sh`; for your own file run `sed -i 's/\r$//' <file>`. This
  folder's `.gitattributes` keeps it from happening for `.sh`/`.py` files on
  a fresh clone, and files created in the container's VS Code default to LF.
- **`ros2 node list` / `ros2 topic list` shows nothing, or nodes from other
  people's laptops** — every config sets `ROS_LOCALHOST_ONLY=1`, so only
  nodes in *your* container can see each other. That's deliberate: on Linux
  the container shares the host network, and a lab full of laptops on
  `ROS_DOMAIN_ID=0` would otherwise all see (and command) each other's arms.
  The UR driver talks to the robot over plain TCP, not DDS, so the real robot
  works with it set. If a list is empty, run `ros2 daemon stop` and try again.
- **`RTPS_TRANSPORT_SHM Error` / `open_and_lock_file failed`** — Fast DDS
  shared-memory transport running out of room. The configs give the container
  1 GB of `/dev/shm` (Docker's default is 64 MB); if you see this, you're on a
  container from an older config — **Rebuild Container**.
- **Image build fails at `apt-get update` with `EXPKEYSIG` / `invalid
  signature`** — your locally cached `osrf/ros:humble-desktop` has an expired
  ROS apt key. `docker pull osrf/ros:humble-desktop`, then **Dev Containers:
  Rebuild Container Without Cache**.
- **Container fails to start: `ports are not available` / `bind: address
  already in use` (50001–50004)** — something else on your laptop holds those
  ports (often a second copy of this container). Close other lab4 containers,
  or see [docs/real-robot.md](docs/real-robot.md).
- **`colcon build` is very slow on Windows** — the workspace lives on the
  Windows filesystem and every file access crosses into Docker's VM. It works,
  just slowly; build only what you changed with `--packages-select`. For a
  big speedup, clone the repo inside WSL (`\\wsl$\Ubuntu\home\<you>\...`) and
  open `lab4/` from there with **WSL: Open Folder in WSL** before reopening
  in the container.
- **"Reopen in Container" doesn't ask which OS config to use** — make sure
  you opened `lab4/` itself as the VS Code workspace root.
