#!/bin/bash
# preflight.sh <robot host> <command...>
#
# Used as RosAria's launch-prefix in amigo_real.launch: checks that the robot
# is reachable, says so in plain words if it is not, then execs RosAria.
#
# Why: when the robot is off or you are on the wrong network, ARIA sits on
# "Connnecting to robot..." for ~75 s (the OS TCP timeout) before failing,
# which looks exactly like a hang.  This prints the likely cause up front.
#
# Only ICMP is used.  Probing TCP 8101 first would open and drop a connection
# on the robot's single-client serial bridge just before ARIA needs it.
# A failed ping is a warning, not an error: some networks block ping.

host="$1"
shift

if ! getent ahosts "$host" >/dev/null 2>&1; then
    echo "[preflight] Cannot resolve '$host'." >&2
    echo "[preflight]   Check the robot name (robot:=amigo3 -> amigo3.rit.edu)," >&2
    echo "[preflight]   or pass its address instead: robot_ip:=<IP>." >&2
elif ping -c1 -W2 "$host" >/dev/null 2>&1; then
    echo "[preflight] $host answers ping -- connecting."
else
    echo "[preflight] WARNING: no ping reply from $host within 2 s." >&2
    echo "[preflight]   Is the robot switched on, and is your laptop on the lab network?" >&2
    echo "[preflight]   ARIA will keep trying for about 75 s before giving up." >&2
fi

exec "$@"
