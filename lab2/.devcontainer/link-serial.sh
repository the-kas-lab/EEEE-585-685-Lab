#!/usr/bin/env bash
# Bridge the host's USB-serial device nodes into the container's own /dev.
#
# The host /dev is bind-mounted at /host/dev rather than over /dev itself.
# Mounting it over /dev also replaces the container's devpts instance with the
# host's, after which pty allocation fails ("grantpt: Operation not
# permitted") -- that takes out the VS Code server and every integrated
# terminal. See https://github.com/moby/moby/issues/15070.
#
# Symlinks are created unconditionally, including for nodes that do not exist
# yet: a dangling symlink costs nothing and starts resolving the moment the
# adapter is plugged in, so hotplug keeps working with no rebuild.
set -euo pipefail

if [ ! -d /host/dev ]; then
	echo "link-serial: /host/dev is not mounted; serial passthrough unavailable." >&2
	exit 0
fi

for n in 0 1 2 3; do
	for prefix in ttyUSB ttyACM; do
		sudo ln -sfn "/host/dev/${prefix}${n}" "/dev/${prefix}${n}"
	done
done

attached=$(ls -d /host/dev/ttyUSB* /host/dev/ttyACM* 2>/dev/null || true)
if [ -n "$attached" ]; then
	echo "link-serial: serial adapter(s) attached:" $attached
else
	echo "link-serial: no serial adapter attached yet. Plug one in -- it will" \
	     "appear at /dev/ttyUSB0 with no rebuild needed."
fi
