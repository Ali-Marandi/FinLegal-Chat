# FinLegal-Chat v0.2.0 QA and Security Sign-off Checklist

**Pull request:** [Ali-Marandi/FinLegal-Chat #2](https://github.com/Ali-Marandi/FinLegal-Chat/pull/2)  
**Branch:** `release/v0.2.0-enterprise`  
**Scope:** Electron desktop workspace, Windows NSIS packaging, macOS DMG packaging, Linux packages, release workflow, provenance validation, enterprise governance documentation, and customer-facing claims.

## Merge decision rule

Merge only when every **Required** item is marked **Pass**, an owner and evidence link are recorded, and all exceptions have written approval from Security, Release Engineering, and the accountable product owner. A successful CI status alone is not sufficient evidence for code signing, provenance, data residency, customer suitability, or regulatory compliance.

> **No-go rule:** Do not merge or publish a signed enterprise release if signing credentials are exposed, action references are not immutable, production dependencies fail policy, a platform signature or notarization check fails, a provenance check is missing or unexpected, or customer-facing claims exceed the evidence available.

## 1. Pull-request and source-control controls

| ID | Check | Owner | Evidence | Status |
|---|---|---|---|---|
| PR-01 | Pull request is open against the protected default branch and contains the intended v0.2.0 desktop, workflow, validator, and documentation changes. | Release Engineering | PR file list and review record | ☐ |
| PR-02 | Required reviewers include at least one Security or Release Engineering reviewer and one product owner. | Repository Admin | GitHub branch-protection settings | ☐ |
| PR-03 | No private keys, PFX/P12 files, passwords, base64 certificate data, tokens, or customer data are present in the diff, history, logs, or artifacts. | Security | Secret scan and manual review | ☐ |
| PR-04 | `package-lock.json` is consistent with `package.json`; the lockfile is unchanged after `npm install --package-lock-only`. | Platform Engineering | CI output | ☐ |
| PR-05 | All changed files pass `git diff --check`; no generated caches, `node_modules`, `dist`, or local credentials are tracked. | Release Engineering | Git status and diff check | ☐ |
| PR-06 | The version, product name, app ID, release branch, workflow tag logic, and release notes are consistent. | Product + Release Engineering | Manifest review | ☐ |

## 2. CI and workflow security controls

| ID | Check | Owner | Evidence | Status |
|---|---|---|---|---|
| SEC-01 | Every third-party action is pinned to a reviewed full-length commit SHA. | Security | Workflow action inventory | ☐ |
| SEC-02 | Workflow-wide permissions default to `contents: read`; write permissions are limited to the publish job. | Security | YAML review | ☐ |
| SEC-03 | `id-token: write` and `attestations: write` occur only where provenance attestations are generated. | Security | YAML review | ☐ |
| SEC-04 | Windows, macOS, and publish jobs use the protected `release` environment with required reviewers. | Repository Admin | Environment configuration and approval log | ☐ |
| SEC-05 | Signing secrets are environment-scoped and are unavailable to pull-request workflows. | Security | Environment secret scope review | ☐ |
| SEC-06 | The workflow does not enable `ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES`, use `--clobber`, or silently replace an existing release. | Release Engineering | Automated policy check | ☐ |
| SEC-07 | Manual dispatch cannot bypass version-tag, environment-approval, dependency, signature, provenance, or publication gates. | Security | Rehearsal run | ☐ |
| SEC-08 | Workflow concurrency prevents two release attempts for the same version from racing. | Release Engineering | YAML and rehearsal evidence | ☐ |
| SEC-09 | Workflow logs and artifacts are reviewed for secrets, untrusted interpolation, unexpected network access, and unauthorized writes. | Security | Log review record | ☐ |
| SEC-10 | The repository audit log shows no unauthorized workflow, environment, branch-protection, tag, or secret changes during the release window. | Security | GitHub audit export | ☐ |

GitHub recommends least-privilege workflow permissions, careful secret handling, and immutable action references as part of secure Actions use.[1]

## 3. Dependency, SBOM, and build-integrity controls

| ID | Check | Owner | Evidence | Status |
|---|---|---|---|---|
| DEP-01 | `npm ci --ignore-scripts` completes from the committed lockfile. | Platform Engineering | CI log | ☐ |
| DEP-02 | Production dependency audit passes at the agreed threshold; all exceptions have owners and expiry dates. | Security | `npm audit --omit=dev` output and exception register | ☐ |
| DEP-03 | Development/build dependency findings are reviewed because packaging uses the Electron Builder toolchain. | Platform Engineering + Security | Full audit review | ☐ |
| DEP-04 | SBOM is generated in an approved SPDX or CycloneDX format and retained with release evidence. | Security | SBOM artifact | ☐ |
| DEP-05 | Unexpected lockfile changes, install scripts, package sources, and transitive dependencies are reviewed. | Platform Engineering | Dependency review | ☐ |
| DEP-06 | Electron, Electron Builder, Node.js, runner images, and packaging binaries are at approved versions. | Platform Engineering | Version inventory | ☐ |
| DEP-07 | The resulting application does not include development secrets, test fixtures, customer data, or unnecessary build tooling. | QA + Security | Packaged application inspection | ☐ |

## 4. Application QA and desktop security

| ID | Check | Owner | Evidence | Status |
|---|---|---|---|---|
| QA-01 | `node --check` passes for `src/main.js`, `src/preload.js`, and `src/renderer/app.js`. | QA | CI output | ☐ |
| QA-02 | Application launches on a clean supported Windows environment. | QA | Test record | ☐ |
| QA-03 | NSIS installation succeeds with the configured per-machine and Start Menu/Desktop shortcut options. | QA | Installation log or test record | ☐ |
| QA-04 | Upgrade from the prior preview preserves approved workspace data and does not overwrite customer data unexpectedly. | QA | Upgrade test | ☐ |
| QA-05 | Uninstall behavior matches the documented retention expectation and does not delete workspace data unexpectedly. | QA + Product | Uninstall test | ☐ |
| QA-06 | Drag-and-drop and file-picker intake accept only supported source extensions and handle duplicate files safely. | QA | Functional test | ☐ |
| QA-07 | Workspace persistence uses validated payloads, atomic writes, bounded record sizes, and restricted local file permissions. | Security + QA | Code review and test | ☐ |
| QA-08 | Unexpected navigation, new-window creation, permission requests, insecure content, and renderer Node access are blocked. | Security | Electron security review | ☐ |
| QA-09 | Content Security Policy is present and rejects unauthorized script, object, frame, and network behavior. | Security | Renderer test | ☐ |
| QA-10 | Keyboard navigation, focus states, reduced-motion behavior, readable contrast, and supported screen sizes are tested. | QA + Product | Accessibility test | ☐ |
| QA-11 | Linux AppImage, Debian package, Windows installer, and macOS DMG launch and perform the core smoke flow. | QA | Cross-platform matrix | ☐ |

## 5. Artifact, signing, and provenance gates

| ID | Check | Owner | Evidence | Status |
|---|---|---|---|---|
| REL-01 | Windows NSIS installer is produced with the intended version and architecture. | Release Engineering | Installer and manifest | ☐ |
| REL-02 | Windows Authenticode status is `Valid`, signer identity matches the approved publisher, and certificate thumbprint is recorded. | Security | PowerShell verification output | ☐ |
| REL-03 | macOS DMG is signed with the approved Developer ID identity and hardened runtime is verified. | Security | `codesign` and `spctl` output | ☐ |
| REL-04 | macOS notarization and stapling validation succeed where notarization is claimed. | Release Engineering | `xcrun stapler validate` output | ☐ |
| REL-05 | Linux packages meet the documented hash-based trust model or required package signing policy. | Security + QA | Linux verification record | ☐ |
| REL-06 | SHA-256 manifests match every published artifact byte-for-byte. | Release Engineering | `validate-release.sh` output | ☐ |
| REL-07 | Release manifests match artifact names, hashes, sizes, platform, version, and source SHA. | Release Engineering | Manifest verification output | ☐ |
| REL-08 | Artifact attestations verify against the expected repository, workflow, source revision, and artifact identity. | Security | `gh attestation verify` output | ☐ |
| REL-09 | A deliberately modified artifact fails hash or signature verification in a negative test. | Security + QA | Negative-test output | ☐ |
| REL-10 | Release publication refuses duplicate tags or asset replacement and preserves immutable release evidence. | Release Engineering | Rehearsal output | ☐ |
| REL-11 | Release evidence includes source SHA, workflow run, action-SHA inventory, SBOM, hashes, signatures, attestations, and approvals. | Security | Evidence package index | ☐ |

GitHub describes artifact attestations as a mechanism for establishing build provenance and recommends verification against the expected repository and artifact.[2]

## 6. Enterprise compliance and customer-readiness gates

| ID | Check | Owner | Evidence | Status |
|---|---|---|---|---|
| CMP-01 | Customer-facing release claims accurately distinguish preview functionality from production enterprise controls. | Legal + Product | Release-note approval | ☐ |
| CMP-02 | Data-residency statements identify the actual release scope; desktop-local persistence is not described as cloud residency enforcement. | Privacy + Legal | Data-residency review | ☐ |
| CMP-03 | Enterprise identity, audit, retention, deletion, support, and incident-notification dependencies are documented as available, planned, or not included. | Product + Security | Capability matrix | ☐ |
| CMP-04 | GSI distribution, deal-registration, margin-protection, data-isolation, and customer-notification rules are consistent with the release. | Partner Operations + Legal | Governance crosswalk | ☐ |
| CMP-05 | Customer support has installation verification, rollback, incident escalation, and certificate/provenance guidance. | Customer Success | Support runbook | ☐ |
| CMP-06 | The customer evidence package and release-notification template are approved. | Legal + Security | Approved artifacts | ☐ |
| CMP-07 | No claim uses “compliant,” “tamper-proof,” “secure by signature,” or “provenance-certified” without defined evidence scope. | Legal + Security | Claims review | ☐ |

## 7. Final sign-off record

| Function | Required signer | Decision | Date | Evidence link |
|---|---|---|---|---|
| QA | Named QA owner | ☐ Approve ☐ Reject | __________ | __________________ |
| Security | Named Security owner | ☐ Approve ☐ Reject | __________ | __________________ |
| Release Engineering | Named release owner | ☐ Approve ☐ Reject | __________ | __________________ |
| Product | Named product owner | ☐ Approve ☐ Reject | __________ | __________________ |
| Legal/Privacy | Required for customer claims | ☐ Approve ☐ Reject ☐ N/A | __________ | __________________ |
| Partner Operations | Required for GSI distribution | ☐ Approve ☐ Reject ☐ N/A | __________ | __________________ |
| Executive release approver | Required for enterprise release | ☐ Approve ☐ Reject | __________ | __________________ |

## References

[1]: https://docs.github.com/en/actions/reference/security/secure-use "GitHub Docs — Secure use reference"
[2]: https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds "GitHub Docs — Using artifact attestations to establish provenance for builds"
[3]: https://www.electronjs.org/docs/latest/tutorial/security "Electron Security Tutorial"
[4]: https://www.electron.build/code-signing "electron-builder Code Signing Documentation"
[5]: ./finlegal-desktop/.github/workflows/pr-release-verification.yml "FinLegal-Chat pull-request release verification workflow"
[6]: ./finlegal-desktop/scripts/validate-release.sh "FinLegal-Chat local release validator"
