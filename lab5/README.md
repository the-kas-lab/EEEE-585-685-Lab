# AmigoBot lab (Lab 5)

ROS 1 Noetic, Gazebo 11 and the MobileRobots AmigoBot. Read the
[student handout](docs/Robotics_Lab_instruction_2026-5.pdf) for the lab tasks
and report requirements. This README covers setup, commands and troubleshooting.

Everything the lab needs is inside the container, including ROSARIA and the
ARIA robot library. No additional repository clones or launch-file fixes
are needed.

## How it's organized

```
lab5/
├── .devcontainer/devcontainer.json   # one config for Linux, macOS and Windows
├── docker/
│   ├── Dockerfile                    # ROS, Gazebo, ROSARIA, the desktop
│   ├── postCreate.sh                 # wires up ~/catkin_ws, runs the first build
│   ├── start-desktop.sh              # the in-container desktop (noVNC)
│   └── entrypoint.sh
├── catkin_ws/src/amigobot_ros/
│   ├── amigo_description/            # robot model (URDF) and physical parameters
│   ├── amigo_gazebo/                 # simulation launch file and lab world
│   ├── amigo_bringup/                # real robot launch file (RosAria)
│   ├── amigo_tools/                  # helper nodes: wheel velocities, sonar, test drives
│   └── amigo_student/                # YOUR package: the four task skeletons
└── docs/                             # student handout, LaTeX source and images
```

As in the other labs, the `catkin_ws/` above **is** the workspace. Inside
the container, `~/catkin_ws` is a link to it, so edits made on either side
show up on the other.

## Prerequisites

1. **Docker.** On Linux, Docker Engine via
   [lab1/scripts/host-setup-linux.sh](../lab1/scripts/host-setup-linux.sh).
   On macOS and Windows,
   [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. **VS Code** with the **Dev Containers** extension
   ([`ms-vscode-remote.remote-containers`](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)).

You do **not** need an X server (XQuartz, VcXsrv, `xhost`) for this lab,
unlike labs 1, 2 and 4. Gazebo and RViz draw on a desktop that runs inside
the container, and you open that desktop in your web browser.

## Quick start

1. Open **this folder** (`lab5/`) in VS Code, not the repo root.
2. Run **Dev Containers: Reopen in Container**. There is a single
   configuration, so VS Code won't ask which OS you're on.
3. Wait for the build. The first one takes a few minutes (about 2.5 minutes
   on an M-series Mac with a fast connection), and the image is about
   5.5 GB on disk. Do it before the lab, not on lab Wi-Fi. It finishes with:
   ```
   AmigoBot workspace built. Open http://localhost:6080 for the desktop.
   ```
4. Open **http://localhost:6080** in your web browser. That's the desktop
   where Gazebo and RViz windows appear. Keep the tab open.

Every new terminal in VS Code starts in `~/catkin_ws` with ROS, ROSARIA and
the workspace already sourced. Open as many terminals as you need; they all
attach to the same container.

## Simulation

```bash
roslaunch amigo_gazebo amigo_sim.launch
```

Gazebo and RViz open on the desktop tab. The robot starts in the middle of a
6 m × 6 m room with a few obstacles, so the sonar has something to see.

Useful arguments:

| Argument | Effect |
|---|---|
| `steering:=true` | also open the Robot Steering slider window |
| `gui:=false` | no Gazebo window (faster; RViz still opens) |
| `rviz:=false` | no RViz |

### Check that everything works

With the simulator running, in a second terminal:

```bash
roslaunch amigo_tools verify.launch
```

This drives the robot about 0.5 m and turns it once, so it needs a little
clear space. It should end with:

```
26 checks: 25 passed, 0 failed, 1 warnings
```

The one warning is `/my_odom present`, which you write in Task 4.

### Driving the robot (Task 1)

Use either the slider window (start the simulator with `steering:=true`, then
move the slider; it starts at zero speed):

```bash
roslaunch amigo_gazebo amigo_sim.launch steering:=true
```

or the keyboard, in its own terminal (keys only register while that
terminal has focus; `i` forward, `k` stop):

```bash
rosrun teleop_twist_keyboard teleop_twist_keyboard.py
```

Use one or the other. The slider window publishes its own value (zero, until
you move it) ten times a second, so with both running they fight over the
robot.

### Your package: `amigo_student`

Your four tasks are skeletons in
[catkin_ws/src/amigobot_ros/amigo_student/scripts/](catkin_ws/src/amigobot_ros/amigo_student/scripts/).
Each one runs as-is (and does nothing) until you fill in its TODOs:

| Task | Run it with |
|---|---|
| 2: drive a circle | `rosrun amigo_student turn_circle.py _speed:=0.15 _radius:=0.5` |
| 3: sonar + odometry subscriber | `rosrun amigo_student sensor_listener.py` |
| 4: dead reckoning on `/my_odom` | `roslaunch amigo_student my_odom.launch` |
| Extra credit: wander | `rosrun amigo_student wander.py` |

No rebuild is needed after editing a Python script. If you **add** a new
script, make it executable once and `rosrun` finds it:

```bash
chmod +x ~/catkin_ws/src/amigobot_ros/amigo_student/scripts/my_new_node.py
rosrun amigo_student my_new_node.py
```

**Task 4 test drive.** `my_odom.launch` starts your node together with a
logger that compares `/my_odom` with the simulator's ground truth. In another
terminal, drive a fixed pattern:

```bash
rosrun amigo_tools drive_pattern.py _pattern:=square _side:=1.5 _laps:=2
```

Start from a freshly launched simulator so the square has clear space. The
drive takes about 2 minutes. Then stop `my_odom.launch` with `Ctrl-C`. The
logger prints final and peak position errors and final heading error, and
writes `~/amigo_odom_error.csv`. Use these measurements to evaluate your
dead reckoning estimate.

Other patterns: `_pattern:=circle _radius:=0.5`,
`_pattern:=spin _turns:=1`, and `_pattern:=stop` (sends the robot a zero
command).

## Real robot

Test your code in simulation first. Physical-robot connectivity is still
being restored, and the old `amigoN.rit.edu` hostnames no longer resolve.
Ask the TA for the current bridge address and network instructions before
attempting a physical-robot check-off.

Stop Gazebo, connect to the robot's network, set `ROBOT_IP` to the address
provided by the TA, and run:

```bash
roslaunch amigo_bringup amigo_real.launch robot_ip:=$ROBOT_IP
```

After connecting, check the stationary interface before attempting motion:

```bash
roslaunch amigo_tools verify.launch hardware:=true move:=false
```

| Argument | Effect |
|---|---|
| `robot_ip:=<name or IP>` | the robot's Wi-Fi serial bridge |
| `tcp_port:=8101` | the bridge's TCP port (8101 is the default) |
| `rviz:=false` | no RViz |
| `steering:=true` | also open the Robot Steering slider window |

Your laptop has to be on the same network as the robot's Wi-Fi bridge. The
container makes an outgoing TCP connection to the robot, so the container
itself needs no extra network setup.

Everything you wrote against the simulator runs unchanged: the robot provides
the same topics with the same names (see [Topics](#topics)). The only
difference is that `/ground_truth/state` exists only in simulation. On the
robot, compare your odometry with the robot's own:

```bash
roslaunch amigo_student my_odom.launch reference:=/odom
```

On hardware, `/wheel_velocities` is reconstructed from the body twist in
`/odom`. Agreement with `/odom` checks consistency; it does not establish
physical accuracy. Use an external position measurement to assess drift.

Keep speeds gentle indoors (`_speed:=0.10`).

What you'll see:

| Output | Meaning |
|---|---|
| `[preflight] <robot> answers ping -- connecting.` then `Connected to robot.` and `Subtype: amigo-sh` | connected |
| `[preflight] Cannot resolve '<name>'.` | that robot name doesn't exist; check it, or use its IP address |
| `[preflight] WARNING: no ping reply from <robot> within 2 s.` | robot off, or your laptop isn't on the robot's network. The launch keeps trying for about 75 s, then exits |
| `RosAria: ARIA could not connect to robot!` then `REQUIRED process [RosAria-...] has died!` | the connection failed and the launch stopped itself; read the lines above it |

## Topics

The simulator and the robot provide the same interface:

| Topic | Type | Notes |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | command in |
| `/odom` | `nav_msgs/Odometry` | the robot's own dead reckoning |
| `/sonar` | `sensor_msgs/PointCloud` | 8 echo points, with `index` and `range` channels |
| `/sonar/range_0` … `_7` | `sensor_msgs/Range` | one per transducer |
| `/wheel_velocities` | `std_msgs/Float32MultiArray` | `[ω_left, ω_right]` in rad/s |
| `/ground_truth/state` | `nav_msgs/Odometry` | **simulation only**: where the robot really is |

TF: `odom → base_link → {wheels, caster, sonar_0..7, base_footprint}`.
To see it: `rosrun rqt_tf_tree rqt_tf_tree`.

Sonar numbering: 0 is the left side, 1–4 sweep across the front, 5 is the
right side, and 6–7 are at the rear.

Physical parameters (wheel radius, wheelbase, sonar positions) are in
[amigo_description/config/amigo_params.yaml](catkin_ws/src/amigobot_ros/amigo_description/config/amigo_params.yaml).
`my_odom.launch` loads them into your node as `~wheel_radius` and
`~wheel_separation`.

## Troubleshooting

- **The desktop tab says it can't connect, or shows a black screen.** Run
  `start-desktop` in a container terminal, then reload the tab. Any GUI
  programs that were open have to be started again.
- **The container won't start: `Bind for 127.0.0.1:6080 failed`.** Something
  else on your computer is already using port 6080, usually another copy of
  this container. Stop it (`docker ps` lists running containers) and reopen.
- **The robot keeps driving after your node exits.** In simulation the
  robot keeps the last command it received until it gets a new one, so make
  your nodes publish a zero `Twist` on shutdown (the Task 2 skeleton says
  where). To stop it by hand:
  `rosrun amigo_tools drive_pattern.py _pattern:=stop`.
- **The simulator is slow.** Gazebo and RViz render in software inside the
  container. Start with `gui:=false` to drop the Gazebo window; the robot
  still simulates and RViz still shows it.
- **`rosrun` can't find a script you just created.** Make it executable:
  `chmod +x <file>`.
- **"Reopen in Container" isn't offered.** Make sure you opened `lab5/`
  itself as the VS Code folder, not the repository root.
