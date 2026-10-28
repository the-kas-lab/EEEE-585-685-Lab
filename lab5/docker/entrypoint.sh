#!/bin/bash
# Container entrypoint: bring the desktop up with the container, then hand
# over to the real command (`sleep infinity` for the dev container).
#
# Started from here rather than from postStartCommand so the desktop's
# processes belong to the container itself, not to a `docker exec` session
# that VS Code may tear down.
/usr/local/bin/start-desktop || echo "amigo-entrypoint: desktop failed to start; run start-desktop" >&2
exec "$@"
