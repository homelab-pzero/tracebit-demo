"""Minimal Tracebit Community Edition API client (https://community.tracebit.com/api-docs).

The API token comes from TRACEBIT_API_TOKEN, or from the file named by
TRACEBIT_API_TOKEN_FILE, never from argv.
"""
import json
import os
import urllib.parse
import urllib.request

API = os.environ.get("TRACEBIT_API_HOST", "https://community.tracebit.com")


def _token() -> str:
    tok = os.environ.get("TRACEBIT_API_TOKEN")
    if not tok and os.environ.get("TRACEBIT_API_TOKEN_FILE"):
        with open(os.environ["TRACEBIT_API_TOKEN_FILE"]) as f:
            tok = f.read()
    if not tok or not tok.strip():
        raise SystemExit("Set TRACEBIT_API_TOKEN or TRACEBIT_API_TOKEN_FILE (your Tracebit Community Edition API token).")
    return tok.strip()


def call(method: str, path: str, body=None, query=None):
    url = API + path + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")
    req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode())
    req.add_header("Authorization", "Bearer " + _token())
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return json.loads(data) if data else None


def issue(name: str, types, labels: dict, source="script", source_type="endpoint"):
    return call("POST", "/api/v1/credentials/issue-credentials", {
        "name": name, "types": list(types), "source": source, "sourceType": source_type,
        "labels": [{"name": k, "value": str(v)} for k, v in labels.items()],
    })


def confirm(confirmation_id: str):
    call("POST", "/api/v1/credentials/confirm-credentials", {"id": confirmation_id})


def alerts(since: str | None = None, limit: int = 50):
    q = {"limit": str(limit)}
    if since:
        q["start_time_after"] = since
    return call("GET", "/api/v1/alerts", query=q).get("alerts", [])


def alert_logs(alert_id: str):
    return call("GET", f"/api/v1/alerts/{alert_id}/logs").get("logs", [])
