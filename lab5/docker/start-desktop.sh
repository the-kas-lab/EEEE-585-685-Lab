#!/bin/bash
# Start (or restart) the in-container desktop:
#   Xvnc on display :1  ->  fluxbox  ->  noVNC on port 6080
# Open http://localhost:6080 on your host to see it.
#
# Runs automatically when the container starts (see amigo-entrypoint). Run it
# by hand -- `start-desktop` -- if the browser tab says it cannot connect.
# Safe to run repeatedly: it stops any previous copy first.

DISPLAY_NUM=1
VNC_PORT=$((5900 + DISPLAY_NUM))
NOVNC_PORT=6080
GEOMETRY=${DESKTOP_GEOMETRY:-1600x900}
LOG_DIR=/tmp/desktop
mkdir -p "$LOG_DIR"

pkill -u "$(id -u)" -f "Xtigervnc :$DISPLAY_NUM" 2>/dev/null
pkill -u "$(id -u)" -f "websockify.*$NOVNC_PORT" 2>/dev/null
pkill -u "$(id -u)" -x fluxbox 2>/dev/null
sleep 0.5
# A crashed X server leaves its lock behind, and the next one refuses to start.
rm -f "/tmp/.X${DISPLAY_NUM}-lock" "/tmp/.X11-unix/X${DISPLAY_NUM}"

# -SecurityTypes None: no VNC password. That is only acceptable because
# -localhost keeps VNC inside the container, and the devcontainer publishes
# noVNC on the host's 127.0.0.1 only -- nobody else on the lab network can
# reach it.
setsid Xtigervnc ":$DISPLAY_NUM" \
    -geometry "$GEOMETRY" -depth 24 \
    -rfbport "$VNC_PORT" -localhost \
    -SecurityTypes None \
    -AlwaysShared \
    -AcceptSetDesktopSize \
    >"$LOG_DIR/xvnc.log" 2>&1 < /dev/null &

for _ in $(seq 1 50); do
    xdpyinfo -display ":$DISPLAY_NUM" >/dev/null 2>&1 && break
    sleep 0.1
done
if ! xdpyinfo -display ":$DISPLAY_NUM" >/dev/null 2>&1; then
    echo "start-desktop: X server did not start, see $LOG_DIR/xvnc.log" >&2
    exit 1
fi

DISPLAY=":$DISPLAY_NUM" setsid fluxbox >"$LOG_DIR/fluxbox.log" 2>&1 < /dev/null &

# Bound to all interfaces *inside* the container so Docker's port publish can
# reach it; the host side is restricted to 127.0.0.1 in devcontainer.json.
setsid websockify --web /usr/share/novnc "$NOVNC_PORT" "localhost:$VNC_PORT" \
    >"$LOG_DIR/novnc.log" 2>&1 < /dev/null &

echo "start-desktop: desktop running -- open http://localhost:$NOVNC_PORT on your computer."
