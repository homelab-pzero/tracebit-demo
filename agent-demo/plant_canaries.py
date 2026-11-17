#!/usr/bin/env python3
"""Plant Tracebit canaries in a home directory, the way the GitHub Action and the
Tracebit CLI do: an AWS profile `administrator` in ~/.aws/credentials and an SSH key
~/.ssh/prod_deploy with a matching ~/.ssh/config host.

    plant_canaries.py HOME_DIR NAME [label=value ...]

Prints only the canary name and where it wrote; never a secret.
"""
import base64
import os
import pathlib
import sys

import tracebit


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    home, name = pathlib.Path(sys.argv[1]), sys.argv[2]
    labels = dict(a.split("=", 1) for a in sys.argv[3:])
    creds = tracebit.issue(name, ["aws", "ssh"], labels, source="agent-demo", source_type="endpoint")

    aws, ssh = creds["aws"], creds["ssh"]
    (home / ".aws").mkdir(parents=True, exist_ok=True, mode=0o700)
    (home / ".aws" / "credentials").write_text(
        "[administrator]\n"
        f"aws_access_key_id = {aws['awsAccessKeyId']}\n"
        f"aws_secret_access_key = {aws['awsSecretAccessKey']}\n"
        f"aws_session_token = {aws['awsSessionToken']}\n")
    (home / ".aws" / "config").write_text("[profile administrator]\nregion = us-east-1\n")

    sshdir = home / ".ssh"
    sshdir.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = sshdir / "prod_deploy"
    key.write_bytes(base64.b64decode(ssh["sshPrivateKey"]))
    key.chmod(0o600)
    (sshdir / "prod_deploy.pub").write_bytes(base64.b64decode(ssh["sshPublicKey"]))
    (sshdir / "config").write_text(
        f"# production deploy host\nHost prod-deploy\n    HostName {ssh['sshIp']}\n    User ubuntu\n"
        f"    IdentityFile {key}\n    IdentitiesOnly yes\n    StrictHostKeyChecking no\n")
    for f in (home / ".aws" / "credentials", sshdir / "config"):
        os.chmod(f, 0o600)

    tracebit.confirm(aws["awsConfirmationId"])
    tracebit.confirm(ssh["sshConfirmationId"])
    print(f"Planted Tracebit canaries '{name}': AWS profile 'administrator' in {home}/.aws, "
          f"SSH key {key} (Host prod-deploy). Expire {aws['awsExpiration']}.")


if __name__ == "__main__":
    main()
