#!/usr/bin/env bash
# Run the attacker-rate x traffic-load grid. Requires the testbed to be up
# (run testbed/up.sh first). usage: run_grid.sh [seconds_per_cell]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
OUT="$ROOT/data/raw"
MON=wlan5; ATT=wlan4
BSSID=$(cat /sys/class/net/wlan0/address)
DUR="${1:-180}"
RATES=(none low moderate high)
LOADS=(low moderate high)

mkdir -p "$OUT"
echo "[*] BSSID=$BSSID  ${DUR}s/cell  12 cells"

for load in "${LOADS[@]}"; do
  for rate in "${RATES[@]}"; do
    tag="rate-${rate}_load-${load}"
    pcap="$OUT/${tag}.pcap"; gt="$OUT/${tag}.gt"
    echo "[*] cell: $tag"
    sudo timeout $((DUR+5)) tcpdump -i "$MON" -e -s0 -w "$pcap" 'type mgt' 2>/dev/null &
    CAP=$!; sleep 1; t0=$(date +%s)
    sudo python3 "$HERE/legit_traffic.py" --load "$load" --duration "$DUR" &
    LEGIT=$!
    if [ "$rate" != "none" ]; then
      third=$(( DUR / 3 )); sleep "$third"
      a0=$(date +%s); "$HERE/attack.sh" "$rate" "$third" "$BSSID" "$ATT"; a1=$(date +%s)
      echo "attacker_on=$a0 attacker_off=$a1" > "$gt"
    else
      echo "attacker_on= attacker_off=" > "$gt"
    fi
    wait "$LEGIT" 2>/dev/null || true
    wait "$CAP" 2>/dev/null || true
    echo "cell_start=$t0 duration=$DUR rate=$rate load=$load bssid=$BSSID" >> "$gt"
    echo "    -> $pcap"
    sleep 3
  done
done
echo "[*] Grid done. Captures + ground truth in $OUT"
