#!/usr/bin/env bash
# Runpod Docker command wrapper: stop this Pod even if the desktop disconnects.
set -euo pipefail
pod_id="${RUNPOD_POD_ID:?Missing Runpod Pod ID}"
command -v runpodctl >/dev/null
if runpodctl pod stop --help >/dev/null 2>&1; then
  stop_form=modern
elif runpodctl stop pod --help >/dev/null 2>&1; then
  stop_form=legacy
else
  echo 'No supported native Pod stop command; refusing workload startup.' >&2
  exit 70
fi
stop_guard() {
  trap '' HUP
  sleep 3000
  for attempt in 1 2 3; do
    if [ "$stop_form" = modern ]; then
      runpodctl pod stop "$pod_id" && exit 0
    else
      runpodctl stop pod "$pod_id" && exit 0
    fi
    sleep 15
  done
}
stop_guard > /tmp/recovery-autostop.log 2>&1 &
guard_pid=$!
python - "$guard_pid" "$stop_form" <<'PY'
import json,os,sys,time
record=dict(armed=True,pid=int(sys.argv[1]),stop_form=sys.argv[2],pod_id=os.environ['RUNPOD_POD_ID'],deadline_unix=int(time.time())+3000)
with open('/tmp/recovery-stop-guard.json','w') as f:json.dump(record,f)
print('RECOVERY_NATIVE_POD_STOP_TIMER_ARMED_50_MINUTES',flush=True)
PY
exec /start.sh
