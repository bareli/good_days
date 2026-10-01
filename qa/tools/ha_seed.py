"""Seed the QA dev Home Assistant: owner via onboarding, a non-admin user, Good Days entry."""
import json
import secrets
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8129"
CLIENT = BASE + "/"
OUT = sys.argv[1]


def call(method, path, body=None, token=None, form=False):
    headers = {}
    data = None
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode()
        return json.loads(text) if text else None


admin_pw = secrets.token_urlsafe(12)
user_pw = secrets.token_urlsafe(12)
code = call("POST", "/api/onboarding/users", {
    "client_id": CLIENT, "name": "QA Admin", "username": "qa_admin", "password": admin_pw, "language": "he",
})["auth_code"]
token = call("POST", "/auth/token", {"grant_type": "authorization_code", "code": code, "client_id": CLIENT}, form=True)["access_token"]
for step, body in (("core_config", {}), ("analytics", {}), ("integration", {"client_id": CLIENT, "redirect_uri": CLIENT + "?auth_callback=1"})):
    try:
        call("POST", f"/api/onboarding/{step}", body, token)
    except Exception as err:  # noqa: BLE001
        print("onboarding", step, err)

flow = call("POST", "/api/config/config_entries/flow", {"handler": "good_days", "show_advanced_options": False}, token)
result = call("POST", f"/api/config/config_entries/flow/{flow['flow_id']}", {
    "location": {"latitude": 32.5, "longitude": 34.9}, "diaspora": False,
    "candle_lighting_minutes": 30, "havdalah_minutes": 0, "language": "auto",
}, token)
print("flow:", result.get("type"), result.get("title"))

json.dump({"base": BASE, "admin": {"username": "qa_admin", "password": admin_pw, "token": token},
           "user": {"username": "qa_user", "password": user_pw}}, open(OUT, "w"), indent=2)
print("seeded")
