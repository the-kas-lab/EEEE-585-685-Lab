# GUI forwarding setup (X11)

RViz (and turtlesim, for the pre-lab) open real GUI windows. The container
itself has no display — it draws into an X11 server running on your **host**
machine. Each `devcontainer.json` in this lab tells the container where to
send its display output (the `DISPLAY` environment variable), but your host
still needs an X server listening and willing to accept connections from
Docker. Do the steps for your OS once per machine (the "each session" steps
need repeating whenever you reboot / log back in).

If you already did this for lab1/lab2, nothing changes — same X server, same
steps.

Pick your OS:
- [Linux](#linux)
- [macOS](#macos)
- [Windows](#windows)

---

## Linux

Linux already has an X server running (it's what your desktop is). Nothing
to install.

**Each session**, before opening the container, allow local Docker
containers to connect to it:

```bash
xhost +local:docker
```

That's it — the `linux` devcontainer config mounts `/tmp/.X11-unix` and
forwards your host's `$DISPLAY` straight through.

> To revoke access when you're done: `xhost -local:docker`

---

## macOS

Install [XQuartz](https://www.xquartz.org/) (macOS's X server; not included
by default):

```bash
brew install --cask xquartz
```

Then, **one-time setup**:

1. Log out and back in (or reboot) so XQuartz is fully registered.
2. Open XQuartz → **Preferences → Security** → check **"Allow connections
   from network clients"**.
3. Restart XQuartz for the setting to take effect.

**Each session**, before opening the container:

1. Open XQuartz (it needs to be running).
2. Allow local connections:
   ```bash
   xhost + 127.0.0.1
   ```

The `macos` devcontainer config points `DISPLAY` at
`host.docker.internal:0`, which is Docker Desktop's DNS alias for your Mac
— that's what reaches XQuartz.

---

## Windows

Windows has no X server at all — install one. This lab uses
[VcXsrv](https://sourceforge.net/projects/vcxsrv/) (free, and its config
tool is called **XLaunch**).

**Prerequisites:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with the
  WSL2 backend enabled.
- [VcXsrv](https://sourceforge.net/projects/vcxsrv/) installed
  (`winget install marha.VcXsrv` works too).

**Each session**, start an X server via XLaunch before opening the
container:

1. Launch **XLaunch** (Start menu).
2. **Display settings** → select **"Multiple windows"**, Display number
   `0` → Next.
3. **Select how to start clients** → **"Start no client"** → Next.
4. **Extra settings** → check:
   - **"Disable access control"** (required — without this, Docker's
     connections are rejected)
   - **uncheck "Native opengl"**. The container renders RViz in software
     (`LIBGL_ALWAYS_SOFTWARE=1` in the `windows` config) and only sends the
     finished pixels to VcXsrv; VcXsrv's own OpenGL path is what makes RViz 2
     crash or draw a black 3D view.
5. *(optional)* Click **Save configuration** and save it as `config.xlaunch`
   on your Desktop — double-clicking that file next time starts VcXsrv with
   these exact settings, so you can skip steps 1–4.
6. Click **Finish**. VcXsrv now sits in your system tray, listening.
7. When the Windows Firewall prompt appears the first time, **allow access**
   for both Private and Public networks (needed for Docker's virtual
   network to reach it — and campus/lab Wi-Fi is usually a *Public* network).

The `windows` devcontainer config points `DISPLAY` at
`host.docker.internal:0`, Docker Desktop's alias for your Windows host —
that's what reaches VcXsrv.

> Leave the VcXsrv tray icon running for the whole session; closing it
> closes every RViz window.

---

## Sanity check

Inside the container:

```bash
ros2 run turtlesim turtlesim_node   # quick 2D check
rviz2                               # the one the lab actually needs
```

If both windows appear on your screen and RViz shows its grid in the 3D view,
X11 forwarding is working. If not, re-check the steps above first (they're the
most common culprit), then see [Troubleshooting](../README.md#troubleshooting)
in the lab4 README.
