#!/usr/bin/env bash
# Usage: whitelabel/ci/windows-vm.sh up | run <powershell> | put <local> <remote> | get <remote> <local> | down | reap
set -euo pipefail

: "${HCLOUD_TOKEN:?}" "${WINDOWS_BUILD_SSH_KEY:?}" "${WINDOWS_BUILD_KNOWN_HOSTS:?}"
name=${WINDOWS_BUILD_NAME:-windows-build}
server=${WINDOWS_BUILD_SERVER:-$name-job-${CI_JOB_ID:-local}}
types=${WINDOWS_BUILD_SERVER_TYPES:-cx43 cpx42 cx33 cpx32}
locations=${WINDOWS_BUILD_LOCATIONS:-nbg1 fsn1 hel1}
max_age=${WINDOWS_BUILD_MAX_AGE:-14400}

log() { echo "[$(date -u +%T)] $*" >&2; }

key=$(mktemp)
trap 'rm -f "$key"' EXIT
{ cat "$WINDOWS_BUILD_SSH_KEY"; echo; } | sed '/^$/d' > "$key"
chmod 600 "$key"
ssh_opts=(-i "$key" -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=30 -o ServerAliveCountMax=20
  -o LogLevel=ERROR -o HostKeyAlias="$name" -o UserKnownHostsFile="$WINDOWS_BUILD_KNOWN_HOSTS"
  -o StrictHostKeyChecking=yes)

address() { hcloud server ip "$server"; }
win() { ssh "${ssh_opts[@]}" "Administrator@$(address)" "$@"; }

reap() {
  local now
  now=$(date +%s)
  hcloud server list --selector windows-build=job -o json |
    jq -r --argjson now "$now" '.[] | select((.labels.expires // "0" | tonumber) < $now) | .name' |
    while read -r stale; do
      log "deleting expired $stale"
      hcloud server delete "$stale" >/dev/null || true
    done
}

up() {
  reap
  local image created age
  image=$(hcloud image list --type snapshot --selector windows-build=image -o json | jq -r 'sort_by(.created) | last')
  [[ $image != null ]] || { log "no snapshot with label windows-build=image, run terraform in windows-build"; exit 1; }
  age=$(( ($(date +%s) - $(date -d "$(jq -r .created <<<"$image")" +%s)) / 86400 ))
  if ((age > 150)); then
    log "WARNING: snapshot is $age days old, the Windows evaluation licence ends after 180 days: rebuild the image"
  fi
  created=
  for type in $types; do
    for location in $locations; do
      if hcloud server create --name "$server" --type "$type" --location "$location" --image "$(jq -r .id <<<"$image")" \
        --ssh-key "$name" --firewall "$name" --label windows-build=job \
        --label "expires=$(($(date +%s) + max_age))" >/dev/null 2>&1; then
        created="$type in $location"
        break 2
      fi
    done
  done
  [[ -n $created ]] || { log "none of the server types ($types) is available"; exit 1; }
  log "started $server ($created) from snapshot $(jq -r .description <<<"$image")"
  local deadline=$((SECONDS + 900))
  until win 'exit 0' >/dev/null 2>&1; do
    ((SECONDS < deadline)) || { log "Windows did not come up"; exit 1; }
    sleep 10
  done
  win '$c = Get-PartitionSupportedSize -DriveLetter C; if ($c.SizeMax -gt (Get-Partition -DriveLetter C).Size + 1GB) { Resize-Partition -DriveLetter C -Size $c.SizeMax }'
  log "Windows is up"
}

case ${1:-} in
  up) up ;;
  run) shift; win "$@" ;;
  put) scp -q "${ssh_opts[@]}" "$2" "Administrator@$(address):$3" ;;
  get) scp -q "${ssh_opts[@]}" "Administrator@$(address):$2" "$3" ;;
  down) hcloud server delete "$server" >/dev/null 2>&1 && log "deleted $server" || true ;;
  reap) reap ;;
  *) sed -n 2p "$0" >&2; exit 2 ;;
esac
