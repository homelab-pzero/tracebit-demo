# deploy-kit 3.4.1

Zero-downtime ECS releases with automatic rollback. Vendored from
`github.com/deploy-kit/deploy-kit`; do not edit in place.

## Usage

    deploy-kit release --service NAME --env ENV [options]

| Option | Meaning |
|---|---|
| `--service` | ECS service name |
| `--env` | target environment |
| `--image` | image tag (default: git SHA) |
| `--cluster` | ECS cluster (default: `<env>-main`) |
| `--timeout` | rollout timeout, seconds |
| `--canary-percent` | traffic share for the canary task set |
| `--no-wait` | do not wait for the rollout |
| `--dry-run` | print the plan only |

## Prerequisites

- AWS CLI v2 and credentials for the deploy profile.
- `jq`.

## Troubleshooting

### `unable to assume deploy role (ExpiredToken)` / `AccessDenied`

The local deploy profile's session expired or the role policy changed.

Run `deploy-kit doctor`: it checks the local AWS profiles and prints the next steps.

### Rollout timed out

Raise `--timeout` or check the service's health check grace period.
