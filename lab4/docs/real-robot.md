# Driving the real UR5e from the container

The lab laptop already runs ROS 2 natively — if you're using it, follow the
handout (§6) and ignore this page. This page is for running handout §6 from
**this container on your own laptop**.

> Only one computer can control the arm at a time. Coordinate with your TA
> before connecting, and keep someone at the teach pendant's e-stop.

## Why the container needs extra setup

The connection to a UR robot goes both ways:

```
 container ──TCP 30001–30004──▶ UR5e          driver reads state, sends dashboard commands
 container ◀──TCP 50001–50004── UR5e          External Control program connects BACK to the driver
```

The first direction just works from any container. The second is the catch:
the External Control program on the pendant opens connections to **your
laptop's IP** on ports 50001–50004, and the driver tells it which IP to use.

- **Linux host** — the container uses `--network=host`, so it *is* your
  laptop on the network. Nothing extra to do.
- **Windows / macOS host** — Docker Desktop runs the container behind NAT in
  a VM, with an internal address like `172.17.0.2` that the robot can't
  reach. The `windows`/`macos` configs already publish ports 50001–50004 on
  your laptop and forward them into the container. You still have to (1) let
  those ports through your firewall and (2) tell the driver your laptop's real
  IP with `reverse_ip:=...` — otherwise it auto-detects and advertises the
  unreachable internal address, and the pendant program fails with a
  connection / "socket" error.

## One-time setup (Windows)

In an **elevated PowerShell** (Run as Administrator):

```powershell
New-NetFirewallRule -DisplayName "UR5e ROS 2 driver (lab4)" -Direction Inbound `
  -Protocol TCP -LocalPort 50001-50004 -Action Allow -Profile Any
```

`-Profile Any` matters: Windows usually classifies lab/campus Wi-Fi as a
*Public* network, which blocks inbound connections by default. To remove the
rule after the course:
`Remove-NetFirewallRule -DisplayName "UR5e ROS 2 driver (lab4)"`.

**macOS:** if the firewall is on (System Settings → Network → Firewall),
allow incoming connections for Docker when prompted.

## Each session

1. **Join the lab router's network** (the one the UR5e is wired to) and turn
   off any VPN.
2. **Find your laptop's IP on that network** — on the *host*, not in the
   container (the container only sees its own internal address):
   - Windows: `ipconfig` → your Wi-Fi adapter's **IPv4 Address**
     (e.g. `192.168.131.150`)
   - macOS: `ipconfig getifaddr en0`

   To see what else is on the network (handout's `arp -a`), also run it on
   the host — inside a Windows/macOS container `arp -a` only shows Docker's
   internal gateway.
3. **Check the robot is reachable**, from a container terminal:
   ```bash
   ping 192.168.131.143
   ```
4. **On the teach pendant**, in the External Control node's settings, set the
   host IP to **your laptop's IP from step 2** (not the lab laptop's
   `192.168.131.146` from the handout) and keep the port at `50002`.
5. **Launch the driver** in the container, passing that same IP as
   `reverse_ip`:
   ```bash
   ros2 launch ur_robot_driver ur_control.launch.py \
     ur_type:=ur5e robot_ip:=192.168.131.143 use_fake_hardware:=false \
     reverse_ip:=<your laptop IP> launch_rviz:=true
   ```
   (On a Linux host, `reverse_ip` is optional.)
6. **Start the External Control program** on the pendant. The driver's log
   should print `Robot connected to reverse interface. Ready to receive
   control commands.`
7. Run your node in another terminal, as in the handout:
   ```bash
   ros2 run ur5e_pick_place <your_script>
   ```

## Troubleshooting

- **`ping` fails** — you're not on the lab router's network, or a VPN is
  routing the `192.168.131.x` range elsewhere. Check from the host too
  (`ping 192.168.131.143` in PowerShell): if the host can ping but the
  container can't, restart Docker Desktop.
- **Driver starts, but the pendant program errors / times out connecting** —
  in order of likelihood: `reverse_ip` not passed (Windows/macOS), pendant
  host IP doesn't match your laptop's current IP (it changes between
  sessions on DHCP), firewall rule missing, or another laptop is already
  connected to the robot.
- **Container won't start: `ports are not available` for 50001–50004** —
  another program (or a second lab4 container) holds those ports. Close it;
  on Windows, `netstat -ano | findstr :5000` shows the owning PID.
- **Robot connects but doesn't move** — check the pendant is in *remote* or
  *local* mode as your TA set it up, the External Control program is
  actually *running* (play button), and the speed slider isn't at 0%.
- **`ros2 topic list` shows nothing from the lab laptop** — expected: the
  container sets `ROS_LOCALHOST_ONLY=1` and DDS discovery doesn't cross
  Docker Desktop's NAT anyway. You don't need it; the driver talks to the
  robot directly over TCP.
