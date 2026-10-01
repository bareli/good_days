#!/usr/bin/env bash
# Create and start a fresh QA dev Home Assistant on a port: ha_instance.sh <port>
# Seeds qa_admin (owner), qa_user (non-admin) and a Good Days entry.
set -euo pipefail
PORT="$1"
S="C:/Users/barel/AppData/Local/Temp/claude/D--Code-home-assistant-extensions-good-days/f3802ecc-2b66-432d-963d-f0b1f5d18979/scratchpad"
REPO="D:/Code/home assistant extensions/good_days"
CFG="$S/haconfig-$PORT"
[ "$(basename "$CFG")" = "haconfig-$PORT" ] || { echo "refusing: $CFG"; exit 1; }
mkdir -p "$CFG/custom_components"
rm -rf "$CFG/custom_components/good_days"
cp -r "$REPO/custom_components/good_days" "$CFG/custom_components/"
sed "s/server_port: 8129/server_port: $PORT/" "$S/haconfig/configuration.yaml" > "$CFG/configuration.yaml"
(cd "$S" && PYTHONPATH="$S" nohup venv314/Scripts/python.exe ha_launch.py -c "$CFG" --ignore-os-check --skip-pip > "$S/ha-$PORT.log" 2>&1 &)
for i in $(seq 1 40); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/" || true)
  [ "$code" = "200" ] || [ "$code" = "302" ] && break
  sleep 3
done
echo "port $PORT http=$code"
ACC="$REPO/qa/fixtures/dev-accounts-$PORT.json"
if [ ! -f "$ACC" ]; then
  sed "s/127.0.0.1:8129/127.0.0.1:$PORT/" "$S/ha_seed.py" > "$S/ha_seed_$PORT.py"
  "$S/venv314/Scripts/python.exe" "$S/ha_seed_$PORT.py" "$ACC"
  UPW=$("$S/venv314/Scripts/python.exe" -c "import json;print(json.load(open(r'$ACC'))['user']['password'])")
  OUT=$("$S/venv314/Scripts/python.exe" "$S/ha_ws.py" "$ACC" '{"type":"config/auth/create","name":"QA User","group_ids":["system-users"],"local_only":false}')
  USER_ID=$(echo "$OUT" | "$S/venv314/Scripts/python.exe" -c "import sys,json;print(json.loads(sys.stdin.read())['result']['user']['id'])")
  "$S/venv314/Scripts/python.exe" "$S/ha_ws.py" "$ACC" "{\"type\":\"config/auth_provider/homeassistant/create\",\"user_id\":\"$USER_ID\",\"username\":\"qa_user\",\"password\":\"$UPW\"}" >/dev/null
  echo "seeded $ACC"
fi
# HA 2026.9: YAML http settings are "pending" and revert (with a restart) after 5 min unless promoted.
"$S/venv314/Scripts/python.exe" "$S/ha_ws.py" "$ACC" '{"type":"http/config/promote"}' >/dev/null && echo "http config promoted"
