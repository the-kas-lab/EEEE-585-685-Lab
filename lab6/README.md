# Husky A200 lab

ROS 2 Humble. Lab handout:
[docs/Robotics_Lab6_instruction_2026.pdf](docs/Robotics_Lab6_instruction_2026.pdf).

The container is the lab 4 image (`osrf/ros:humble-desktop`) plus
`twist_mux`, the stock `teleop_twist_keyboard`, and the `lab6-check` checker.
If lab 4 still works on your laptop, the base image is already downloaded and
this one builds in a few minutes.

## How it's organized

```
lab6/
├── docker/
│   ├── Dockerfile
│   ├── postCreate.sh           # wires up ~/ros2_ws, runs the first build
│   └── lab6-check              # the checker (installed in the container)
├── .devcontainer/
│   ├── linux/devcontainer.json
│   ├── macos/devcontainer.json
│   └── windows/devcontainer.json
├── starter/
│   ├── keyboard.py             # given: terminal key input (handout Task 2)
│   └── teleop_main.py          # given: main() with a safe shutdown
├── docs/                       # the handout
└── ros2_ws/
    └── src/
        └── husky_lab/          # the simulated Husky (don't edit)
```

`~/ros2_ws` inside the container is a symlink to `ros2_ws/` in this folder, so
the package you create there is also on your laptop. You need that for
Task 3, where you build a Docker image from it.

## Prerequisites

Same as lab 4: Docker (Docker Desktop on macOS/Windows), VS Code with the Dev
Containers extension, and X11 for RViz, set up as in
[lab4/docs/x11-setup.md](../lab4/docs/x11-setup.md). Windows: keep "Native
opengl" unchecked in XLaunch.

## Quick start

1. Open **this folder** (`lab6/`) in VS Code, not the repository root.
2. **Dev Containers: Reopen in Container**, and pick your OS's config.
3. Wait for `postCreateCommand` to finish. It builds the simulator package.
4. In a container terminal:

   ```bash
   ros2 launch husky_lab sim.launch.py
   ```

   RViz opens with the Husky on a grid, the taped line, and the stopping
   mark at 3 m. Use `rviz:=false` if you only want the topics.

Every new terminal starts in `~/ros2_ws` with ROS 2 and the workspace
sourced. After you build your own package, open a new terminal or run
`source install/setup.bash` so `ros2 run` can find it.

## Docker commands for Task 3

Run `docker build` and `docker run` in a terminal **on your laptop**, not in
the VS Code container terminal (there is no Docker inside the container):

- macOS / Linux: Terminal, `cd <repo>/lab6/ros2_ws/src/husky_teleop`
- Windows: PowerShell, `cd <repo>\lab6\ros2_ws\src\husky_teleop`. If you
  cloned the repository inside WSL, use a WSL terminal instead.

On your laptop, run your image with plain `docker run --rm -it <image>`.
Don't add the `--network host --ipc host` options from the TA's command: on
your laptop they make your container and the dev container share ROS 2
files that belong to different users, and messages are lost without any
error.

## Troubleshooting

- **`ros2 run husky_teleop teleop` says the package is not found**: build it
  (`colcon build --packages-select husky_teleop`) and source
  `install/setup.bash`, or open a new terminal.
- **`lab6-check` warns that your source files are newer than the build**:
  you edited the code but did not rebuild. The workspace is built without
  `--symlink-install`, so `install/` holds a copy of your code.
- **`keyboard input needs a terminal`**: the node was started without a
  terminal attached. With `docker run`, use `-it`.
- **Keys do nothing**: click in the terminal that runs your node first. Key
  presses go to whichever window has focus.
- **Your container runs but the simulated robot doesn't move**: start it
  with plain `docker run --rm -it <image>`, without `--network host`. In the
  dev container, `ros2 topic info /a200_0252/cmd_vel` should show a
  publisher.
- **`ros2 topic list` shows nothing**: run `ros2 daemon stop` and try again.
  Containers on your laptop see each other, but not other laptops.
- **`$'\r': command not found`** or **`python3\r`**: a file has Windows line
  endings. Run `sed -i 's/\r$//' <file>` in the container.
- **No RViz window**: the host X11 setup, see
  [lab4/docs/x11-setup.md](../lab4/docs/x11-setup.md).
