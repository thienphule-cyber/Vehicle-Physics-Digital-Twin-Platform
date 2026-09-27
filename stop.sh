#!/bin/bash
# stop.sh
# Stops the backend and frontend background processes started by
# start.sh, using the PID files saved under .run/.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${PROJECT_ROOT}/.run"

BACKEND_PID_FILE="${PID_DIR}/backend.pid"
FRONTEND_PID_FILE="${PID_DIR}/frontend.pid"

stop_process() {
  local pid_file=$1
  local label=$2

  if [ -f "${pid_file}" ]; then
    local pid
    pid=$(cat "${pid_file}")

    if kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}"
      echo "${label} stopped (PID ${pid})."
    else
      echo "${label} was not running (stale PID file removed)."
    fi

    rm -f "${pid_file}"
  else
    echo "${label} PID file not found. Nothing to stop."
  fi
}

stop_process "${BACKEND_PID_FILE}" "Backend"
stop_process "${FRONTEND_PID_FILE}" "Frontend"

echo "Done."