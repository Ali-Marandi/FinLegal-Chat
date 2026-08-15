# Code-Signing Certificate Key Rotation and Emergency Revocation Procedure

**Scope:** Windows Authenticode certificates, Apple Developer ID Application certificates, Apple notarization credentials, GitHub Actions environment secrets, release artifacts, and customer/GSI distribution channels  
**Owners:** Security, Release Engineering, Platform Engineering, Legal, Customer Success, and GSI Operations  
**Related controls:** Protected `release` environment, two-person approval, SHA-pinned actions, signature verification, artifact hashes, SBOMs, and provenance attestations

## 1. Purpose and operating principles

This procedure ensures that FinLegal-Chat can rotate signing credentials before expiry, after suspected exposure, or after a change in publisher ownership without losing release control or creating ambiguity about which artifacts are trusted.

The procedure applies to both planned rotation and emergency revocation. It treats a signing private key as compromised when there is credible evidence of unauthorized access, even if no unauthorized signature has yet been found. A replacement certificate must use a newly generated key pair; it must never reuse a potentially exposed private key.

> **Core rule:** Stop signing first, preserve evidence second, revoke or rotate the authority third, and publish only a newly verified release after independent approval.

## 2. Credential inventory

Maintain a controlled inventory with the certificate or credential owner, platform, subject identity, thumbprint or Team ID, creation date, expiration date, storage location, GitHub environment, approved workflow, rotation window, backup custodian, and revocation contact.

| Credential | GitHub environment secret | Verification identity | Rotation evidence |
|---|---|---|---|
| Windows Authenticode PFX | `WINDOWS_CERTIFICATE_BASE64`, `WINDOWS_CERTIFICATE_PASSWORD` | Certificate subject, issuer, thumbprint, code-signing EKU | CA issuance record, thumbprint, test signature, workflow run |
| Apple Developer ID P12 | `MACOS_CERTIFICATE_BASE64`, `MACOS_CERTIFICATE_PASSWORD` | Developer ID Application identity, Team ID | Apple certificate record, signing output, notarization result |
| Apple notarization account | `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID` | Apple account and Team ID | Notarization submission and acceptance record |
| GitHub release authority | Environment approval and workflow token | Repository, environment, reviewers, permissions | Audit log, environment review, release run |

Do not store private keys, PFX/P12 files, passwords, app-specific passwords, or base64 values in source control, issue comments, pull requests, build artifacts, or unredacted incident tickets.

## 3. Planned rotation schedule

Begin planned rotation at least **30 days before certificate expiry**, or earlier if required by the certificate authority, Apple, customer contracts, or internal policy. For high-risk environments, use a shorter rotation window and conduct an interim access review.

The rotation owner opens a change ticket containing the reason, affected platform, current certificate identity, proposed cutover time, release impact, customer communication need, rollback plan, approvers, and evidence-retention location. Security confirms that the current certificate has no open incident and that the replacement certificate will use a new key pair.

Release Engineering freezes nonessential release-workflow changes during the cutover. Customer Success and GSI Operations are informed of the planned maintenance window if the rotation could affect customer distribution or release availability.

## 4. Planned Windows Authenticode rotation

### Phase A — Generate and validate the replacement key

1. On a trusted administrative Windows workstation, generate a new private key and request a new organization-validated code-signing certificate from the approved certificate authority.
2. Confirm the certificate subject, organization identity, code-signing enhanced key usage, validity, chain, and private-key association.
3. Record the new certificate thumbprint and expiry date in the credential inventory.
4. Export the certificate and private key to a password-protected PFX using a newly generated strong password.
5. Base64-encode the PFX on the trusted workstation without line wrapping.
6. Keep the new PFX and password under approved certificate custody until the GitHub environment update is complete.

### Phase B — Stage the replacement secret

1. Open **GitHub Settings → Environments → release → Environment secrets**.
2. Replace `WINDOWS_CERTIFICATE_BASE64` with the new single-line base64 PFX value.
3. Replace `WINDOWS_CERTIFICATE_PASSWORD` with the new PFX password.
4. Do not delete or alter the old credential inventory record until all affected release evidence is retained.
5. Require two reviewers to approve the environment change.
6. Confirm that no secret value appears in the audit record or workflow logs.

### Phase C — Test and cut over

1. Run an approved rehearsal or internal release using the protected environment.
2. Verify the installer with `Get-AuthenticodeSignature`.
3. Confirm that the signer subject, thumbprint, certificate chain, timestamp, file version, and SHA-256 hash match the release ticket.
4. Run a clean install, upgrade, launch, uninstall, and rollback test on a supported Windows host.
5. Publish the first customer-facing release signed by the replacement certificate only after Security and Release Engineering approve the evidence.
6. Update customer verification material with the new publisher certificate thumbprint when customer policy requires it.

### Phase D — Retire the old Windows key

After confirming that no approved release remains dependent on the old key, remove the old certificate from active signing systems and certificate stores according to the organization’s key-management policy. Retain the old certificate metadata, thumbprint, validity, release inventory, and revocation status in restricted evidence storage. Do not retain an operational copy of a retired private key unless required by policy and secured accordingly.

## 5. Planned macOS signing and notarization rotation

### Phase A — Generate and validate the replacement identity

1. In the Apple Developer account, create a new **Developer ID Application** certificate using a newly generated key pair.
2. Confirm the Team ID, organization identity, certificate type, validity, and private-key association.
3. Export the certificate and private key as a password-protected P12 from Keychain Access on a trusted Mac.
4. Create a new Apple app-specific password for the notarization account if the existing credential is being retired or may have been exposed.
5. Record certificate identity, Team ID, expiry, and notarization account owner in the credential inventory.

### Phase B — Stage replacement GitHub secrets

Update the protected `release` environment secrets:

```text
MACOS_CERTIFICATE_BASE64
MACOS_CERTIFICATE_PASSWORD
APPLE_ID
APPLE_APP_SPECIFIC_PASSWORD
APPLE_TEAM_ID
```

Require two-person approval for the environment change. Confirm that the Apple ID and Team ID correspond to the new Developer ID certificate. Never place the primary Apple ID password in GitHub Actions.

### Phase C — Test and cut over

1. Run an approved rehearsal on `macos-13` or the approved runner image.
2. Confirm `codesign --verify --deep --strict` succeeds.
3. Confirm `spctl --assess --type execute` succeeds under the customer’s distribution policy.
4. Submit the application and DMG for notarization.
5. Confirm the notarization request succeeds and the ticket is stapled.
6. Run `xcrun stapler validate` for both the application bundle and DMG.
7. Record the certificate identity, Team ID, notarization result, DMG hash, source SHA, workflow run, and clean-install result.
8. Publish only after Security and Release Engineering approve the evidence.

### Phase D — Retire the old Apple identity

Revoke the old Developer ID certificate in the Apple Developer account when appropriate, especially when the private key may have been exposed or the certificate is no longer controlled. Revoke or retire the old app-specific password. Preserve certificate metadata, notarization records, release mappings, and revocation evidence in restricted storage.

## 6. Emergency revocation triggers

Start emergency revocation immediately when any of the following is suspected:

- A PFX, P12, private key, certificate password, Apple app-specific password, or GitHub secret appears in logs, source, artifacts, tickets, or an unauthorized workstation.
- A signing action or runner may have executed unauthorized code with access to a signing secret.
- An unexpected installer is signed by the FinLegal publisher identity.
- A validly signed artifact has an unexpected source revision, workflow, dependency, or provenance record.
- A customer, endpoint security tool, certificate authority, Apple, or GSI partner reports suspicious signing activity.
- A signing workstation, certificate store, Apple account, or GitHub administrator account is compromised.

Treat the event as Critical until Security bounds exposure and confirms that no unauthorized artifact was produced.

## 7. Emergency procedure: first 15 minutes

The Incident Commander opens a Critical incident record and records the credential, platform, suspected exposure time, affected versions, source revisions, workflow runs, customer/GSI distribution paths, and reporter.

Release Engineering immediately pauses the `release` environment and prevents new signed builds, manual dispatch, tag-based publication, and partner distribution. Do not rerun or modify the suspicious workflow run.

Security disables or revokes the affected Windows certificate through the certificate authority or Apple Developer ID certificate through Apple’s developer portal, as applicable. Rotate all secrets available to the affected build jobs, including certificate passwords, Apple credentials, GitHub tokens or GitHub App credentials, package-registry credentials, and connected service tokens.

Preserve workflow logs, audit logs, release metadata, artifact copies, hashes, SBOMs, attestations, action-SHA inventory, dependency lockfiles, endpoint alerts, and distribution records. Keep a restricted forensic copy before normal cleanup.

## 8. Emergency procedure: first 60 minutes

Security determines whether the incident involves certificate exposure, signing-service misuse, workflow compromise, action compromise, runner compromise, dependency compromise, artifact substitution, or a false positive. Review all builds that accessed the affected credential during the exposure window or the full certificate validity period when the window is unknown.

For each artifact, compare the signed file, certificate identity, hash, source SHA, workflow run, action SHAs, SBOM, and provenance attestation. Quarantine any artifact with a signature failure, unexpected publisher, hash mismatch, missing attestation, unexpected source, unexpected workflow, or SBOM mismatch.

Customer Success and GSI Operations identify customers and partners that downloaded, installed, mirrored, cached, or redistributed affected versions. Legal and Privacy assess contractual and regulatory notification requirements.

## 9. Emergency replacement and clean release

Do not reuse the compromised private key. Generate a new key pair and obtain a replacement certificate or certificate identity. Configure a fresh protected GitHub environment or rotate the existing environment only after the incident record preserves the prior state. Require two-person approval for the first replacement signing run.

Rebuild from a clean, reviewed source revision using fresh action SHAs, clean runners, reviewed dependencies, verified SBOMs, and a new release identity. Generate new hashes and provenance attestations. Independently verify platform signatures and notarization. Use a new version or superseding release instead of silently replacing affected assets.

The replacement release evidence must include the source SHA, workflow run, action-SHA inventory, certificate thumbprint or Apple identity, artifact hashes, SBOM, attestation verification, clean-install tests, customer-impact assessment, and approval record.

## 10. Customer and GSI notification

Notify affected customers and GSIs only with Security- and Legal-approved language. State the affected versions, platforms, artifact names, hashes, distribution hold, verification instructions, replacement-release status, and support contact. Do not describe artifacts as safe or unaffected without a documented verification basis.

Require GSIs to stop redistribution, preserve distribution and access records, identify recipients, and coordinate communications. Partners must not delete or alter relevant evidence except to contain immediate harm or under written direction.

## 11. Recovery gates

| Gate | Required evidence | Approver |
|---|---|---|
| Credential containment | Revocation, rotation, secret-access review, and audit evidence | Security |
| Artifact scope | Complete signed-artifact and distribution inventory | Security + Release Engineering |
| Clean build | Reviewed source, fresh credentials, pinned actions, clean runner | Release Engineering |
| Platform verification | Authenticode, Developer ID, notarization, stapling, and hashes | Security + QA |
| Provenance verification | Attestation linked to expected repository, workflow, source, and artifact | Security |
| Customer readiness | Approved notice, verification instructions, support plan, GSI coordination | Legal + Customer Success |
| Distribution restart | Release manifest and two-person final approval | Incident Commander + Executive Sponsor |

## 12. Post-incident actions

Within five business days, conduct a blameless review covering certificate custody, secret exposure, GitHub environment approvals, action pinning, runner access, dependency controls, release immutability, customer notification, and GSI distribution.

Within thirty days, complete a tabletop exercise for both a compromised Windows PFX and a failed macOS notarization/provenance check. Test credential revocation, customer hold notices, evidence preservation, clean rebuild, and release restoration. Assign owners and due dates to all corrective actions.

## References

[1]: https://docs.github.com/en/actions/reference/security/secure-use "GitHub Docs — Secure use reference"
[2]: https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds "GitHub Docs — Using artifact attestations to establish provenance for builds"
[3]: https://developer.apple.com/help/account/manage-certificates/revoke-a-certificate/ "Apple Developer — Revoke a certificate"
[4]: https://learn.microsoft.com/windows-hardware/drivers/install/authenticode "Microsoft Learn — Authenticode"
[5]: ../finlegal-chat-github/finlegal-desktop/.github/workflows/release-v020.yml "FinLegal-Chat hardened v0.2.0 release workflow"
[6]: ./FinLegal-Chat_Signing_Key_and_Provenance_Incident_Response_Playbook.md "FinLegal-Chat signing-key and provenance incident response playbook"
