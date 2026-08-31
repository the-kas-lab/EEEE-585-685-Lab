# GUI forwarding setup (X11)

turtlesim opens a real GUI window (the turtle simulator canvas). The
container itself has no display — it draws into an X11 server running on
your **host** machine. Each `devcontainer.json` in this repo tells the
container where to send its display output (the `DISPLAY` environment
variable), but your host still needs an X server listening and willing to
accept connections from Docker. Do the steps for your OS once per machine
(the "each session" steps need repeating whenever you reboot / log back in).

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

Windows has no X server at all — install one. This tutorial uses
[VcXsrv](https://sourceforge.net/projects/vcxsrv/) (free, and its config
tool is called **XLaunch**).

**Prerequisites:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with the
  WSL2 backend enabled.
- [VcXsrv](https://sourceforge.net/projects/vcxsrv/) installed.

**Each session**, start an X server via XLaunch before opening the
container:

1. Launch **XLaunch** (Start menu).
2. **Display settings** → select **"Multiple windows"**, Display number
   `0` → Next.
3. **Select how to start clients** → **"Start no client"** → Next.
4. **Extra settings** → check:
   - **"Disable access control"** (required — without this, Docker's
     connections are rejected)
   - leave "Native opengl" unchecked if you hit rendering glitches
5. Click **Finish**. VcXsrv now sits in your system tray, listening.
6. When the Windows Firewall prompt appears the first time, **allow access**
   for both Private and Public networks (needed for Docker's virtual
   network to reach it).

The `windows` devcontainer config points `DISPLAY` at
`host.docker.internal:0`, Docker Desktop's alias for your Windows host —
that's what reaches VcXsrv.

> Leave the VcXsrv tray icon running for the whole session; closing it
> drops the turtlesim window.

---

## Sanity check

The real test is turtlesim itself — follow the per-ROS-version README to
open the container and run `turtlesim_node`. If the turtle window appears
on your screen, X11 forwarding is working. If it doesn't, re-check the
steps above first (they're the most common culprit), then see
[Troubleshooting](../README.md#troubleshooting) in the top-level README.
