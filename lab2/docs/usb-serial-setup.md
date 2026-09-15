# USB serial passthrough (SSC-32U arm controller) — Windows

The `lynxmotion_ssc32` driver talks to the SSC-32(U) servo controller over
a USB-serial connection at `/dev/ttyUSB0` (see
[ssc32_driver.cpp](../catkin_ws/src/lynxmotion_ssc32/src/ssc32_driver.cpp)).
On Linux the host's `/dev` is bind-mounted into the container **at
`/host/dev`**, access to the USB-serial tty majors is granted via
`--device-cgroup-rule`, and
[link-serial.sh](../.devcontainer/link-serial.sh) symlinks
`/dev/ttyUSB* -> /host/dev/ttyUSB*` on every container start so the
driver's default path still works. That container starts whether or not
the arm is attached, and picks up a device plugged in later without a
rebuild — an earlier `--device=/dev/ttyUSB0:/dev/ttyUSB0` made the arm
mandatory just to open the workspace.

> **Why not mount the host `/dev` straight onto `/dev`?** It works for the
> serial port and breaks everything else: the container inherits the host's
> devpts instance, pty allocation then fails with `grantpt: Operation not
> permitted`, and you get a container with no working terminal and a VS Code
> server that won't start ([moby#15070](https://github.com/moby/moby/issues/15070)). Docker Desktop on Windows runs containers inside a
WSL2 VM, which has no USB stack by default, so the device has to be
attached to that VM first. That's what this page sets up; the `windows`
devcontainer config then exposes it the same way the `linux` one does.

macOS has the same underlying gap (Docker Desktop's VM has no direct USB
passthrough) but isn't covered here — ask if you need it.

## Prerequisites (one-time)

1. **Docker Desktop** with the WSL2 backend enabled (already required for
   the rest of lab2).
2. **[usbipd-win](https://github.com/dorssel/usbipd-win)** — lets WSL2
   attach to USB devices connected to Windows.
   ```powershell
   winget install usbipd
   ```
3. Restart WSL after installing so the usbipd kernel-mode driver loads:
   ```powershell
   wsl --shutdown
   ```

## Each session

1. Plug in the SSC-32(U) (USB cable to the controller board).
2. In an **elevated PowerShell** (Run as Administrator), list USB devices:
   ```powershell
   usbipd list
   ```
   Find the SSC-32(U) / USB-serial adapter — it usually shows up as
   something like "USB Serial Port", "FT232R USB UART", or "CP210x UART
   Bridge" — and note its `BUSID` (e.g. `2-4`).
3. **First time only** for this device, bind it (persists across reboots):
   ```powershell
   usbipd bind --busid <BUSID>
   ```
4. Attach it to WSL2 — repeat this every time you plug the device back in
   or reboot Windows:
   ```powershell
   usbipd attach --wsl --busid <BUSID>
   ```
   Add `--auto-attach` to have usbipd re-attach automatically on replug:
   ```powershell
   usbipd attach --wsl --busid <BUSID> --auto-attach
   ```
   All WSL2 distros share one kernel, so an attach made from any distro
   (including Docker Desktop's own `docker-desktop`) is visible to the
   Docker engine — usbipd says as much: *"the device will be available in
   all WSL 2 distributions."*
5. Verify it showed up inside WSL2 — open a WSL terminal (`wsl`) and run:
   ```bash
   ls /dev/ttyUSB*
   ```
   You should see `/dev/ttyUSB0`. If it's missing, see
   [Troubleshooting](#troubleshooting).
6. Open (or reopen) the lab2 container: **Dev Containers: Reopen in
   Container**, `windows` config. The container starts whether or not the
   adapter is attached, and an attach made *after* it's running shows up
   inside without a rebuild — so if you forget step 4, just do it and carry
   on rather than reopening.

> Unplugging/replugging the controller, or restarting Windows, drops the
> WSL attachment — redo step 4 (not the full bind) each time.

## Troubleshooting

- **`/dev/ttyUSB0` doesn't appear in WSL** — your WSL2 kernel may be
  missing USB-serial (`usbserial` / `ftdi_sio` / `cp210x`) modules.
  Microsoft's in-box WSL2 kernel has included these since 2022; run
  `wsl --update` and try again.
- **`usbipd attach` fails ("device is bound to a different driver" or
  similar)** — another Windows program has the port open. Close any
  Windows-side serial tools (Arduino IDE, PuTTY, the Lynxmotion SSC-32
  utility, etc.) first.
- **Container fails to start with `/dev/ttyUSB0: no such file or
  directory`** — this shouldn't happen any more on either platform. If it
  does, you're on a stale container built from the old config, which used
  `--device=/dev/ttyUSB0` and so refused to start without the adapter. Fix
  with **Dev Containers: Rebuild Container** — `runArgs` are only applied
  when a container is created, so Retry will keep failing.
- **Windows: container starts, but `/dev/ttyUSB0` isn't inside it** — check
  it exists in the VM first (`wsl ls /dev/ttyUSB*`). If it's there but not
  in the container, redo step 4; if it's missing there too, the attach
  dropped. As a last resort add `"--privileged"` to the `windows` config's
  `runArgs` — widely reported to work where narrower flags don't, at the
  cost of giving the container full host capabilities.
- **Linux: `/dev/ttyUSB0` missing but `/dev/ttyACM0` present** — some
  adapters enumerate as CDC-ACM. Both majors are passed through, so just
  point the driver at the right node (`port` in
  [alb5_ssc32.config](../catkin_ws/src/lynxmotion_ssc32/config/alb5_ssc32.config)).
- **Fedora/RHEL: permission denied on the port even though the node is
  visible** — those hosts own serial devices by GID 18, while `dialout`
  inside the Ubuntu-based container is GID 20; the `linux` config adds both.
  If SELinux is enforcing and still denies access, check `sudo ausearch -m
  avc -ts recent`.
- **Terminals won't open / VS Code server dies / `grantpt: Operation not
  permitted`** — a container built from the intermediate config that
  bind-mounted the host `/dev` over `/dev`. **Dev Containers: Rebuild
  Container** to pick up the `/host/dev` layout.
- **`ls -l /dev/ttyUSB0` shows a broken symlink** — expected when nothing is
  plugged in; it points at `/host/dev/ttyUSB0` and resolves as soon as the
  adapter appears. `ls /host/dev/tty*` shows what's actually attached. If a
  device *is* attached and the link is still broken, rerun
  `bash .devcontainer/link-serial.sh`.
- **Permission denied opening the port inside the container** — check
  `robotuser` is in the `dialout` group (`groups` inside the container);
  the `--group-add` entries in the devcontainer config should handle this
  automatically. If the node came up `root:root` (no udev rule applied it
  to `dialout`), `ls -l /dev/ttyUSB0` will show it — `robotuser` has
  passwordless sudo, so `sudo chown root:dialout /dev/ttyUSB0` unblocks
  you for that session.

## Sanity check

Inside the container, `ls -l /dev/ttyUSB0` should show the device owned by
group `dialout`. Then bring up a driver node (see the top-level
[README](../README.md)) and confirm it connects to the SSC-32 without a
permission or "no such device" error.
