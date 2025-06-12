#!/usr/bin/env bash
###############################################################################
# portscan.sh – Simple concurrent TCP port scanner in pure shell
#
# Usage:
#   ./portscan.sh [-t TIMEOUT] [-c CONCURRENCY] host [portSpec]
#
# Arguments:
#   host          – IPv4/IPv6 address or DNS name to scan
#   portSpec      – (optional) One of the following:
#                     • single port        e.g. 443
#                     • range              e.g. 20-80
#                     • list               e.g. 22,53,80,443
#                     • omitted → 1‑1024
#
# Options:
#   -t TIMEOUT    – seconds to wait for each connection   (default: 1)
#   -c CONCURRENCY– simultaneous probes (background jobs) (default: 128)
#
# Exit codes:
#   0 – ran successfully
#   2 – bad arguments
#
# Tested on bash 4.x / 5.x under Linux, macOS, WSL.
###############################################################################

set -euo pipefail
IFS=$'\n\t'

## ───────────────────────────── Helpers ──────────────────────────────────── ##
err() { printf "Error: %s\n" "$*" >&2; exit 2; }

print_usage() {
  awk '/^#/{sub(/^# ?/,"");print}' "$0" | sed -n '1,/^$/p'
}

is_num() { [[ $1 =~ ^[0-9]+$ ]]; }

# Format ports into a flat, deduplicated, sorted list
expand_ports() {
  local spec="$1" port arr=() p
  IFS=',' read -ra arr <<< "$spec"
  for p in "${arr[@]}"; do
    if [[ $p =~ ^([0-9]+)-([0-9]+)$ ]]; then
      seq "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
    elif is_num "$p"; then
      echo "$p"
    else
      err "Invalid port specifier: $p"
    fi
  done | sort -n | uniq
}

## ───────────────────────────── Defaults ─────────────────────────────────── ##
TIMEOUT=1
CONCURRENCY=128

## ───────────────────────────── Parse args ───────────────────────────────── ##
while getopts ":t:c:h" opt; do
  case $opt in
    t) TIMEOUT=$OPTARG ;;
    c) CONCURRENCY=$OPTARG ;;
    h) print_usage; exit 0 ;;
    \?) err "Unknown option -$OPTARG" ;;
    :)  err "Option -$OPTARG requires an argument." ;;
  esac
done
shift $((OPTIND-1))

[[ $# -ge 1 ]] || { print_usage; exit 2; }

HOST=$1
PORTSPEC=${2:-1-1024}

# Validate numeric options
is_num "$TIMEOUT" || err "TIMEOUT must be numeric."
is_num "$CONCURRENCY" || err "CONCURRENCY must be numeric."

PORTS=( $(expand_ports "$PORTSPEC") )
[[ ${#PORTS[@]} -gt 0 ]] || err "No valid ports to scan."

## ───────────────────────────── Scanner ──────────────────────────────────── ##
scan_port() {
  local host=$1 port=$2
  # Use "timeout" where available; fall back to bash read trick otherwise.
  if command -v timeout >/dev/null 2>&1; then
    timeout "$TIMEOUT" bash -c "echo > /dev/tcp/${host}/${port}" \
      2>/dev/null && echo "$port open" || echo "$port closed"
  else
    # Portable but less precise timeout: background read with subshell
    (exec 3<>"/dev/tcp/${host}/${port}") 2>/dev/null && {
      exec 3<&- 3>&-
      echo "$port open"
    } || echo "$port closed"
  fi
}

export -f scan_port err
export HOST TIMEOUT

printf "Scanning %s … (%d ports, %s s timeout, %d threads)\n" \
       "$HOST" "${#PORTS[@]}" "$TIMEOUT" "$CONCURRENCY"

# shellcheck disable=SC2016
printf '%s\n' "${PORTS[@]}" \
  | xargs -n1 -P "$CONCURRENCY" -I{} bash -c 'scan_port "$HOST" "{}"' \
  | sort -n | awk '
    BEGIN { print "\nPORT  STATE"; print "----  -----"; }
         { printf "%-4s  %s\n", $1, $2; }
    END   { print "\nDone." }'

exit 0
