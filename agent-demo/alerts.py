#!/usr/bin/env python3
"""Show Tracebit alerts with the detail behind them: which canary, where it was planted,
what the attacker called, from where, with what client.

    alerts.py [--since 2026-11-16T00:00:00Z] [--name SUBSTRING] [--wait SECONDS]

--name keeps alerts whose canary name contains SUBSTRING (CI canaries are named
"<repo>@<workflow>"; agent-demo canaries "agent-demo@<run id>"). --wait polls until at
least one matching alert exists, for up to SECONDS.
"""
import argparse
import sys
import time

import tracebit

LABELS = ("github.repo", "github.workflow", "github.job", "github.run_id", "github.sha",
          "agent", "model", "scenario", "host")


def matching(since, name):
    out = []
    for a in tracebit.alerts(since=since):
        logs = tracebit.alert_logs(a["id"])
        cname = next((l["canary_credential"]["name"] for l in logs if l.get("canary_credential")), "")
        if name and name not in cname:
            continue
        out.append((a, cname, logs))
    return out


def show(a, cname, logs):
    print(f"\n\033[1;31m[{a['severity']}] {a['title']}\033[0m  {a['start_time']}")
    print(f"  canary:  {cname}")
    labels = next((l["canary_credential"].get("labels") or [] for l in logs if l.get("canary_credential")), [])
    for lab in labels:
        if lab["name"] in LABELS:
            print(f"  {lab['name']:<16} {lab['value']}")
    for l in sorted(logs, key=lambda l: l["timestamp"]):
        ev = l.get("event") or {}
        req = ev.get("request") or {}
        ua = (req.get("user_agent") or {}).get("label") or ""
        outcome = (ev.get("outcome") or {}).get("result") or ""
        print(f"  {l['timestamp']}  {ev.get('operation', ''):<38} {outcome:<8} from {req.get('ip', '?')}  {ua}")
    print(f"  portal:  {a['tracebit_portal_url']}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--since")
    p.add_argument("--name")
    p.add_argument("--wait", type=int, default=0)
    args = p.parse_args()
    deadline = time.time() + args.wait
    while True:
        found = matching(args.since, args.name)
        if found or time.time() >= deadline:
            break
        time.sleep(15)
    for a, cname, logs in found:
        show(a, cname, logs)
    if not found:
        print("No matching Tracebit alerts.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
