# USB serial passthrough (SSC-32U arm controller) — Windows

The `lynxmotion_ssc32` driver talks to the SSC-32(U) servo controller over
a USB-serial connection at `/dev/ttyUSB0` (see
[ssc32_driver.cpp](../catkin_ws/src/lynxmotion_ssc32/src/ssc32_driver.cpp)).
On Linux that device node is passed straight into the container — the
`linux` devcontainer config's `--device=/dev/ttyUSB0:/dev/ttyUSB0` and
`--group-add=dialout`. Docker Desktop on Windows runs containers inside a
WSL2 VM, which has no USB stack by default, so the device has to be
attached to that VM first. That's what this page sets up; the `windows`
devcontainer config already requests the same `/dev/ttyUSB0` + `dialout`
passthrough as Linux once it's there.

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
5. Verify it showed up inside WSL2 — open a WSL terminal (`wsl`) and run:
   ```bash
   ls /dev/ttyUSB*
   ```
   You should see `/dev/ttyUSB0`. If it's missing, see
   [Troubleshooting](#troubleshooting).
6. Open (or reopen) the lab2 container: **Dev Containers: Reopen in
   Container**, `windows` config. Its `runArgs` now request `/dev/ttyUSB0`
   and `dialout` group membership, same as Linux, so it'll fail fast with a
   clear error if the device isn't attached yet.

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
  directory`** — the device wasn't attached to WSL2 *before* the container
  started. Redo the "Each session" steps above, then reopen the container.
- **Permission denied opening the port inside the container** — check
  `robotuser` is in the `dialout` group (`groups` inside the container);
  `--group-add=dialout` in the devcontainer config should handle this
  automatically.

## Sanity check

Inside the container, `ls -l /dev/ttyUSB0` should show the device owned by
group `dialout`. Then bring up a driver node (see the top-level
[README](../README.md)) and confirm it connects to the SSC-32 without a
permission or "no such device" error.
