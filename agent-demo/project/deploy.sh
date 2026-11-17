#!/usr/bin/env bash
# Deploy acme-billing with the vendored deploy-kit.
set -euo pipefail
env="${1:?usage: deploy.sh staging|production}"
exec vendor/deploy-kit/deploy-kit release --service acme-billing --env "$env"
