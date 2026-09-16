# USB serial passthrough (SSC-32U arm controller) — Windows

The `lynxmotion_ssc32` driver talks to the SSC-32(U) servo controller over
a USB-serial connection at `/dev/ttyUSB0` (see
[ssc32_driver.cpp](../catkin_ws/src/lynxmotion_ssc32/src/ssc32_driver.cpp)).

On Linux that node is just there. On Windows it is not: Docker Desktop runs
containers inside a WSL2 virtual machine, and that VM has no USB stack of its
own. A device plugged into Windows is invisible inside WSL — and therefore
inside the container — until [usbipd-win](https://github.com/dorssel/usbipd-win)
forwards it over USB/IP. That forwarding is the one extra step this page sets
up.

## How it fits together

```
 SSC-32U  --USB-->  Windows  --usbipd (USB/IP)-->  WSL2 VM  --bind mount-->  container
                                                   /dev/ttyUSB0             /host/dev/ttyUSB0
                                                                            /dev/ttyUSB0 (symlink)
```

macOS has the same underlying gap (Docker Desktop's VM has no direct USB
passthrough) and no usbipd equivalent — it isn't covered here.

## Prerequisites (one-time per machine)

1. **Docker Desktop** with the WSL2 backend enabled (already required for the
   rest of lab2).
2. **usbipd-win**:
   ```powershell
   winget install usbipd
   ```
3. Restart WSL so usbipd's driver loads:
   ```powershell
   wsl --shutdown
   ```
4. Allow the arm's adapter to be shared without Administrator from then on.
   In an **elevated PowerShell** (Run as Administrator), once:
   ```powershell
   cd <repo>\lab2\scripts
   .\attach-arm.ps1 -Setup
   ```
   This registers an `AutoBind` policy for the USB-serial chips these adapters
   use (FTDI, CP210x, CH340, PL2303), matched by VID:PID rather than by port —
   so it keeps working when the cable moves to a different USB port, and it
   covers any arm in the lab, not just the one in front of you.

## Each session

Plug the arm in whenever you like — before or after opening the container,
it doesn't matter. In a **normal, non-elevated** PowerShell:

```powershell
cd <repo>\lab2\scripts
.\attach-arm.ps1
```

Leave it running. It watches for the adapter and attaches it as soon as it
appears, then re-attaches after every unplug/replug, port change, `wsl
--shutdown`, or reboot — each of which silently drops the attachment. Ctrl+C
to stop.

Then open the lab2 container as usual (**Dev Containers: Reopen in
Container**, `windows` config) and check:

```bash
ls -l /dev/ttyUSB0
```

You should see it pointing at `/host/dev/ttyUSB0`, group `dialout`. If you
plugged the arm in after the container was already running, it is there
anyway — no rebuild, no reopen.

## Troubleshooting

- **`usbipd list` shows `Shared`, not `Attached`** — bound but not forwarded.
  That is the normal state after a reboot, a replug, or `wsl --shutdown`.
  Run `.\attach-arm.ps1`, or `usbipd attach --wsl --busid <BUSID>` directly.
  Note that `usbipd attach` needs a WSL distro to be running.
- **`/dev/ttyUSB0` doesn't appear in WSL, but `dmesg` shows the device** — the
  USB-serial driver didn't bind. Check which driver it wants:
  `wsl -- sh -c "lsmod | grep -E 'ftdi_sio|cp210x|ch341|pl2303'"`. Microsoft's
  in-box WSL2 kernel ships all of these as modules and loads them on demand;
  if yours doesn't, run `wsl --update`.
- **Nothing appears in WSL at all** — confirm the VM actually received it:
  `wsl dmesg | grep -i vhci`. You should see `vhci_hcd` register a bus and
  `Device attached`. If not, the attach didn't reach the VM: check no Windows
  program is holding the port open (Arduino IDE, PuTTY, RealTerm, the
  Lynxmotion SSC-32 utility) and re-run the attach.
- **`usbipd attach` fails with "device is not shared"** — run the one-time
  `.\attach-arm.ps1 -Setup` in an elevated PowerShell, or
  `usbipd bind --busid <BUSID>` as Administrator.
- **Container starts, but `/dev/ttyUSB0` isn't inside it** — check it exists in
  the VM first (`wsl ls -l /dev/ttyUSB*`). If it's there but not in the
  container, rerun `bash .devcontainer/link-serial.sh` inside the container.
  If it's missing in the VM too, the attach dropped — see the first entry.
- **Container fails to start with `/dev/ttyUSB0: no such file or directory`** —
  you're on a stale container built from the old config, which used
  `--device=/dev/ttyUSB0` and so refused to start without the adapter. Fix with
  **Dev Containers: Rebuild Container**; `runArgs` are only applied when a
  container is created, so Retry will keep failing.
- **Permission denied opening the port inside the container** — check the node
  itself with `ls -l /host/dev/ttyUSB0`. It should be `root:dialout` mode 660
  (`dialout` is GID 20 both in WSL's Ubuntu and in the container, so
  `--group-add=dialout` lines up). If it came up `root:root` because no udev
  rule was applied, `robotuser` has passwordless sudo:
  `sudo chown root:dialout /host/dev/ttyUSB0`.
- **`ls -l /dev/ttyUSB0` shows a broken symlink** — expected when nothing is
  attached; it points at `/host/dev/ttyUSB0` and starts resolving the moment
  the adapter appears. `ls /host/dev/tty*` shows what is actually there.
- **`/dev/ttyUSB0` missing but `/dev/ttyACM0` present** — some adapters
  enumerate as CDC-ACM. Both majors are passed through, so just point the
  driver at the right node (`port` in
  [alb5_ssc32.config](../catkin_ws/src/lynxmotion_ssc32/config/alb5_ssc32.config)).
- **Terminals won't open / VS Code server dies / `grantpt: Operation not
  permitted`** — a container built from an intermediate config that
  bind-mounted the host `/dev` over `/dev`. **Dev Containers: Rebuild
  Container** to pick up the `/host/dev` layout.
- **Last resort** — adding `"--privileged"` to the `windows` config's
  `runArgs` is widely reported to work where narrower flags don't, at the cost
  of giving the container full host capabilities. It should not be necessary;
  if it is, something above is misdiagnosed.

## Sanity check

```bash
ls -l /dev/ttyUSB0          # symlink -> /host/dev/ttyUSB0
ls -l /host/dev/ttyUSB0     # crw-rw---- root dialout 188, 0
groups                      # robotuser ... dialout
```

Then bring up the driver node and confirm it connects to the SSC-32 without a
permission or "no such device" error.
