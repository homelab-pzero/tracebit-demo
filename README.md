# tracebit-demo

A small Node.js project whose GitHub Actions pipeline is protected by
[Tracebit Community Edition](https://community.tracebit.com/supplychainattacks) canaries,
plus a staged supply-chain attack that shows them catching a credential thief.

> Everything under `attack/` is a **simulation**. The "stolen" credentials are Tracebit
> canaries: decoys that grant no access and alert the moment anyone tries them.

## What is in here

| Path | What it is |
|---|---|
| `src/`, `test/` | The "product": a price formatter and its tests. |
| `.github/workflows/ci.yml` | The normal pipeline: `npm ci`, `npm test`. |
| `.github/workflows/simulated-compromise.yml` | The attack, run on demand from the Actions tab. |
| `attack/telemetry-helper/` | A fake malicious npm package. Its `postinstall` hook sweeps `~/.aws`, the environment and `~/.ssh`, then exfiltrates the loot. |
| `attack/use-loot.sh` | The attacker. On a different machine, after the build has finished, it tries the stolen AWS keys (`sts get-caller-identity`, `secretsmanager list-secrets`, `s3 ls`) and the SSH key. |

## How Tracebit protects the pipeline

The `tracebit-com/tracebit-community-action` step runs right after checkout. It issues a
fresh set of canary credentials for each run:

- an AWS profile `administrator` in `~/.aws/credentials`, also in environment variables and in process memory
- an SSH key in `~/.ssh` with a matching `~/.ssh/config` host entry

When the job finishes, the action tells Tracebit that the run ended normally. Any later
use of those credentials is an attacker's, and Tracebit alerts with the repository,
workflow, job, commit SHA and run ID. That signal is high-confidence and needs no tuning:
nothing legitimate ever uses a canary.

Malware of the kind behind tj-actions/changed-files (March 2025), the Trivy and KICS
action compromises, and the trojanized LiteLLM package (March 2026) does exactly what
`harvest.js` does: it collects credential files and environment variables from the runner
and tries them elsewhere.

## Running the demo

1. **Before Tracebit.** Run *Simulated supply-chain compromise* from the Actions tab.
   The build log shows the payload finding nothing worth stealing, and the attacker job
   reports "no canaries to steal". Nobody is alerted, which is also what happens when the
   payload *does* find real keys.
2. **Turn Tracebit on.** With the repository added to the Tracebit Community Edition GitHub
   App, the Tracebit portal offers to cover its workflows and opens a pull request, "Cover
   new GitHub workflows with Tracebit Community Edition Canaries", that adds its step to
   both workflows. Review the diff and merge it. The dashboard now shows full coverage.
   (Fallback: the draft PR from branch `tracebit-canaries` adds the same step.)
3. **Attack again.** Run *Simulated supply-chain compromise* again. The build log shows
   the payload collecting the `administrator` AWS profile, the `__AWS__*` variables and the
   SSH key. The attacker job then tries them from another machine.
4. **The alert.** The Tracebit dashboard (and email) shows the canary use, tied to this
   repository, the *Simulated supply-chain compromise* workflow, the `build` job, the
   commit and the run ID. You know which pipeline leaked, and when, before anyone has
   touched a real credential.

The loot travels between the two jobs as an artifact that the attacker job deletes as soon
as it has read it, so stolen canaries are not left lying around in a public repository.

## Act 2: an AI agent goes out of scope

[`agent-demo/`](agent-demo/README.md): an ordinary coding agent, debugging a failed deploy,
follows a compromised vendored tool's advice and uses an admin AWS credential nobody gave
it. The credential is a Tracebit canary, so the alert names the agent, the model and the
calls it made, while the agent's own summary tells the user not to do what it just did.

## Setup notes

- Secret `SECURITY_API_TOKEN`: the Tracebit Community Edition API token. It is managed
  outside this repo (homelab-pzero `terraform-github`). Without it the action only logs a
  warning and issues no canaries.
- The org's Actions policy allows `tracebit-com/tracebit-community-action` at v1.4.0's
  commit SHA only. A Tracebit PR that pins another ref fails until the allowlist matches.
