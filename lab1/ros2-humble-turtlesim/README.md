# turtlesim on ROS 2 Humble

A dev container that runs turtlesim (the classic ROS "hello world" GUI
simulator) with keyboard teleop, on ROS 2 Humble. No source build needed —
`turtlesim` is installed as a prebuilt apt package.

## Prerequisites

Finish the setup in the [top-level README](../README.md) first: Docker,
VS Code + the Dev Containers extension, and your OS's X11/GUI forwarding
(see [docs/x11-setup.md](../docs/x11-setup.md)).

## Open the container

1. Open this folder (`ros2-humble-turtlesim/`) in VS Code.
2. Run **Dev Containers: Reopen in Container** (Command Palette:
   `Ctrl+Shift+P` / `Cmd+Shift+P`).
3. VS Code will ask which configuration to use — pick the one matching your
   OS: `linux`, `macos`, or `windows`.
4. Wait for the image to build (first time only; a few minutes).

## Run turtlesim

Unlike ROS 1, ROS 2 has no central master — nodes find each other directly.
Open **two terminals** inside the container (VS Code: right-click the
terminal panel → "Split Terminal", or just open new ones — they all attach
to the same running container):

**Terminal 1 — start the simulator:**
```bash
ros2 run turtlesim turtlesim_node
```
A window with a turtle on a blue background should pop up on your host
screen.

**Terminal 2 — start keyboard teleop:**
```bash
ros2 run turtlesim turtle_teleop_key
```
Click into Terminal 2 so it has keyboard focus, then use the arrow keys to
drive the turtle. `Ctrl+C` in any terminal stops that node.

## Troubleshooting

No turtle window appears → this is almost always the host-side X11 setup,
not the container. Revisit [docs/x11-setup.md](../docs/x11-setup.md) for
your OS. See also the top-level README's
[Troubleshooting](../README.md#troubleshooting) section.
