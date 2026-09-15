# Lynxmotion AL5B arm lab

ROS 1 Noetic only.

- **[catkin_ws/src/alb5_description/](catkin_ws/src/alb5_description/)** —
  URDF model of the arm, plus an RViz display launch file.
- **[catkin_ws/src/lynxmotion_ssc32/](catkin_ws/src/lynxmotion_ssc32/)** —
  driver for the Lynxmotion SSC-32(U) servo controller that moves the arm.

## How it's organized

Same shape as [lab1](../lab1/), plus an actual catkin workspace this time
(lab1's turtlesim is apt-installed and needs no packages; this lab's arm
driver and URDF are real catkin packages you build):

```
lab2/
├── docker/
│   ├── Dockerfile
│   └── postCreate.sh           # wires up ~/catkin_ws, runs the first build
├── .devcontainer/
│   ├── linux/devcontainer.json
│   ├── macos/devcontainer.json
│   └── windows/devcontainer.json
└── catkin_ws/
    └── src/
        ├── alb5_description/
        └── lynxmotion_ssc32/
```

The `catkin_ws/` you see above **is** the workspace, when the container
starts, `~/catkin_ws` inside it is a symlink straight back to `catkin_ws/`
in this mounted repo (and a new terminal drops you there directly), so
anything you build or edit shows up on your host too, and vice versa.

## Prerequisites (all OSes)

Same as lab1:

1. **Docker** — Linux: Docker Engine, via
   [lab1/scripts/host-setup-linux.sh](../lab1/scripts/host-setup-linux.sh);
   macOS/Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. **VS Code** + the **Dev Containers** extension
   ([`ms-vscode-remote.remote-containers`](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)).
3. **X11 / GUI forwarding**, so RViz can reach your screen — follow
   [lab1/docs/x11-setup.md](../lab1/docs/x11-setup.md) for your OS.
4. **Windows only** — the SSC-32(U) arm controller connects over USB
   serial, which needs one extra passthrough step so the container can see
   it. Follow [docs/usb-serial-setup.md](docs/usb-serial-setup.md).

## Quick start

1. Do the prerequisites above once per machine.
2. Open **this folder** (`lab2/`) in VS Code, not the repo root.
3. **Dev Containers: Reopen in Container**, pick your OS's config.
4. Wait for `postCreateCommand` to finish, it resolves each package's
   dependencies via `rosdep` and runs an initial `catkin_make`, so the
   workspace is ready to use as soon as the container is up.
5. `roslaunch alb5_description display.launch` to bring up RViz with the
   arm model.

## Building packages

`~/catkin_ws` is already built once by `postCreateCommand`. Every new
terminal already starts `cd`'d into `~/catkin_ws` and has
`source ~/catkin_ws/devel/setup.bash` wired into `.bashrc`.

```bash
catkin_make                                          # everything
catkin_make --pkg alb5_description                   # just one package
catkin_make --pkg alb5_description lynxmotion_ssc32  # a chosen subset
```

As more lab2 packages get added under `catkin_ws/src/`, this same
`catkin_make --pkg <names>` pattern is how you build only the ones you're
currently working with.

## Troubleshooting

See the [lab1 troubleshooting section](../lab1/README.md#troubleshooting) —
the X11/GUI issues are identical since they're host-side, not lab-specific.
