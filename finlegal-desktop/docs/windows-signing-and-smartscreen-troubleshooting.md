# FinLegal-Chat v0.2.0 Windows Signing and SmartScreen Troubleshooting Guide

**Audience:** Enterprise IT, endpoint-security, desktop engineering, GSI implementation teams, and pilot users  
**Scope:** FinLegal-Chat v0.2.0 Windows NSIS installer and related release verification evidence

## Safety rule

Do not bypass a failed signature, unexpected publisher, SHA-256 mismatch, or failed provenance check. Stop installation, preserve the installer, and contact the FinLegal security or support contact listed in your customer agreement.

> **SmartScreen warning and signature failure are different events.** A SmartScreen warning can occur because Microsoft has limited reputation for a new file or publisher, even when the file has a valid signature. A signature or hash failure means the artifact cannot be verified against its expected publisher or release evidence and must not be installed.[1]

## 1. Verify the source and artifact first

Download the installer only from the approved FinLegal release channel or the enterprise software-distribution system authorized by your organization. Confirm the expected version, architecture, filename, source SHA when supplied, and release URL.

Record the file before opening it:

```powershell
$installer = "C:\Path\To\FinLegal-Chat-Enterprise-Workspace-0.2.0.exe"
Get-FileHash $installer -Algorithm SHA256
Get-AuthenticodeSignature $installer | Format-List *
```

Compare the SHA-256 value with the FinLegal `SHA256SUMS-windows.txt` or release manifest. Compare the signer subject and certificate chain with the approved publisher identity in the release evidence. If the filename, hash, version, or publisher differs, do not proceed.

For an additional local validation, run the FinLegal release validator from a trusted engineering workstation:

```bash
./scripts/validate-release.sh \
  --assets /path/to/release-assets \
  --repo Ali-Marandi/FinLegal-Chat \
  --require-attestations
```

The validator requires the expected manifest and refuses to treat a missing attestation as valid when `--require-attestations` is set. Use the exact repository and approved release artifact; do not substitute a personal fork.

## 2. Interpret Authenticode results

`Get-AuthenticodeSignature` returns a status and signer certificate for the file. The release acceptance state is **Valid**, with the expected publisher identity and an intact certificate chain. The following table gives the required action.

| Result | Meaning | Customer action |
|---|---|---|
| `Valid` and expected publisher | The file’s Authenticode signature validates under the local trust policy. | Continue with hash, provenance, endpoint, and change-control checks. |
| `NotSigned` | No Authenticode signature was found. | Do not install; confirm that the correct Windows artifact was downloaded. |
| `HashMismatch` | The file content no longer matches the signed content. | Quarantine the file; do not retry or redistribute it. |
| `NotTrusted` | The certificate chain or trust policy is not accepted locally. | Do not override silently; have IT validate the certificate chain and approved publisher. |
| `UnknownError` or other failure | Verification did not complete reliably. | Preserve output and escalate to FinLegal Security and enterprise IT. |

A valid signature does not prove that the application is free of vulnerabilities or compliant with every customer obligation. It helps establish publisher identity and integrity of the signed content. Keep the verification output with the customer change record.

## 3. Common code-signing verification problems

### The installer reports “Unknown publisher”

First confirm that the file is the approved FinLegal v0.2.0 installer and that the signature status is `Valid`. An unknown publisher may indicate an unsigned or incorrectly signed file, a missing certificate chain, an untrusted enterprise endpoint policy, or an installer downloaded from an unapproved source. Do not use a certificate or publisher name supplied only in an email; compare it with the approved release evidence.

If the signature is valid but the publisher identity is not the expected FinLegal legal entity, stop. Treat this as a release-integrity incident until Security confirms the identity.

### The signature status is `HashMismatch`

The file changed after signing or was damaged, substituted, transformed by a distribution system, or downloaded incompletely. Do not repair, repackage, rename, or re-sign the file locally. Preserve the file, calculate its SHA-256 hash, record the source URL and timestamp, and provide the evidence through the approved security channel.

### The certificate is expired or revoked

Do not install. Record the certificate subject, thumbprint, issuer, validity dates, and status output. FinLegal Release Engineering must confirm whether the artifact was published during a valid signing period and whether a replacement release is required. Do not ask users to disable certificate validation.

### The certificate chain is not trusted on a managed endpoint

Enterprise root or intermediate certificate policies can affect local trust. Ask IT to validate the chain using its approved certificate-management process. Do not import a certificate from an email or disable endpoint trust controls without Security approval. If the certificate chain is valid under the public trust model but blocked by a customer policy, document the exception and obtain the customer’s formal approval.

### The SHA-256 hash does not match

Stop immediately. A hash mismatch is not a cosmetic warning and is not fixed by running the installer again. Obtain a fresh artifact from the approved channel, compare it with the official manifest, and notify FinLegal if the mismatch persists. Preserve both the mismatching artifact and the verification output for investigation.

## 4. Windows SmartScreen warnings

Microsoft Defender SmartScreen evaluates application and publisher reputation as well as other security signals. A new installer or newly rotated publisher certificate may have limited reputation even when the artifact is correctly signed. Microsoft documents that negative or unknown reputation for a file hash or publisher certificate can produce a warning.[1]

A SmartScreen warning should therefore be triaged alongside signature, hash, provenance, endpoint, and distribution checks. It must not be treated as proof that the installer is malicious, and it must not be ignored merely because the file appears to be signed.

### “Windows protected your PC” / “Microsoft Defender SmartScreen prevented an unrecognized app from starting”

1. Select **More info** only to inspect the displayed publisher and application name; do not select **Run anyway** yet.
2. Compare the publisher shown by Windows with the approved FinLegal publisher identity.
3. Cancel the prompt and verify the SHA-256 hash and Authenticode status using the commands above.
4. Verify the artifact provenance when the release evidence provides an attestation.
5. Ask enterprise IT or Security to approve the file through the organization’s controlled application-allowance process if all verification checks pass.
6. Record the SmartScreen message, Windows version, endpoint policy, publisher display, hash, signature output, source URL, and customer change ticket.

Do not advise customers to disable SmartScreen globally, add a broad antivirus exclusion, execute an unsigned installer, or use an unapproved workaround. Microsoft provides enterprise policy controls for SmartScreen, but those controls should be managed by the customer’s endpoint-security team rather than changed by individual users.[2]

### SmartScreen warning after certificate rotation

SmartScreen reputation may be lower after a new certificate or publisher identity is introduced. Confirm that the new certificate is the approved FinLegal certificate, that the artifact hash and provenance match the release, and that the signature is valid. If all evidence passes, route the file through the customer’s formal software-approval process and report the warning to FinLegal so Release Engineering can track reputation and distribution impact.

### SmartScreen warning only for one distribution channel

Compare the hash of the file received through the affected channel with the official hash. A proxy, content scanner, archive process, or software-distribution system may have transformed the file. If the hash changes, quarantine the transformed artifact and contact the distribution owner. Do not assume a warning is only a reputation issue until the bytes are verified.

## 5. Provenance verification failures

A provenance failure occurs when the artifact cannot be linked to the expected repository, workflow, source revision, or attestation identity. Treat it as a release hold. Confirm that the GitHub CLI is authenticated to the approved organization, the repository is correct, the artifact was downloaded from the expected release, and the attestation is available for that exact file.

Do not replace a failed attestation with a screenshot, an email assertion, or a manually generated hash. Provide FinLegal Security with the artifact name, local hash, source SHA, release URL, command output, and timestamp.

## 6. When to escalate immediately

Escalate as a security incident rather than a support issue when any of the following occurs: the hash differs from the official manifest; the signature is absent, invalid, revoked, or signed by an unexpected identity; provenance identifies a different repository, source, or workflow; a customer receives different bytes through different channels; a certificate or private key appears exposed; endpoint security identifies suspicious behavior; or a GSI cannot account for where an installer was copied or redistributed.

Preserve the installer and logs. Do not delete the file, repeatedly execute it, repackage it, or upload it to an unapproved service. FinLegal and the customer’s security team will coordinate containment, evidence preservation, release review, and any notification requirement.

## 7. Information to include in a support ticket

Include the release version, platform and architecture, installer filename, approved source URL, download timestamp, SHA-256 hash, `Get-AuthenticodeSignature` output, SmartScreen wording and screenshot if permitted by policy, Windows version/build, endpoint-security product and policy, provenance-verification output, customer change-ticket number, and whether the installer was executed.

Do not include private keys, certificate passwords, Apple credentials, customer documents, confidential source material, or unredacted security logs containing secrets.

## 8. Enterprise IT allow-listing guidance

If verification passes and the customer’s policy requires an allow-list entry, use the organization’s approved endpoint-management process. Prefer a publisher/certificate-based or managed software-deployment control when supported by the customer’s security policy, and record the exact artifact hash and release version. Avoid broad path-based, filename-based, or global SmartScreen exclusions.

The customer remains responsible for its endpoint policy and change approval. FinLegal should provide the approved publisher identity, release hash, source/release evidence, supported installation method, rollback process, and support escalation details.

## References

[1]: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation "Microsoft Learn — SmartScreen reputation for Windows app developers"
[2]: https://learn.microsoft.com/en-us/windows/security/operating-system-security/virus-and-threat-protection/microsoft-defender-smartscreen/available-settings "Microsoft Learn — Available Microsoft Defender SmartScreen settings"
[3]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-authenticodesignature "Microsoft Learn — Get-AuthenticodeSignature"
[4]: https://learn.microsoft.com/en-us/windows/security/operating-system-security/virus-and-threat-protection/microsoft-defender-smartscreen/ "Microsoft Learn — Microsoft Defender SmartScreen overview"
[5]: ../finlegal-chat-github/finlegal-desktop/scripts/validate-release.sh "FinLegal-Chat local release validator"
