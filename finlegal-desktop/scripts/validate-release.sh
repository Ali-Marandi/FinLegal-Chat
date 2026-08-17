#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: validate-release.sh --assets DIR --repo OWNER/REPO [--require-attestations]

Validates:
  - SHA256SUMS-linux.txt, SHA256SUMS-windows.txt, and SHA256SUMS-macos.txt when present
  - release-manifest-*.json entries against local files
  - GitHub artifact attestations with gh attestation verify when requested

The script never treats a missing attestation as valid when --require-attestations is set.
USAGE
}

ASSETS_DIR=""
REPO=""
REQUIRE_ATTESTATIONS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --assets) ASSETS_DIR="${2:?Missing value for --assets}"; shift 2 ;;
    --repo) REPO="${2:?Missing value for --repo}"; shift 2 ;;
    --require-attestations) REQUIRE_ATTESTATIONS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -n "$ASSETS_DIR" ]] || { echo '--assets is required.' >&2; exit 2; }
[[ -d "$ASSETS_DIR" ]] || { echo "Asset directory not found: $ASSETS_DIR" >&2; exit 2; }
if [[ "$REQUIRE_ATTESTATIONS" -eq 1 ]]; then
  [[ -n "$REPO" ]] || { echo '--repo is required with --require-attestations.' >&2; exit 2; }
  command -v gh >/dev/null 2>&1 || { echo 'GitHub CLI (gh) is required for attestation verification.' >&2; exit 2; }
fi

cd "$ASSETS_DIR"

hash_tool() {
  if command -v sha256sum >/dev/null 2>&1; then
    echo sha256sum
  elif command -v shasum >/dev/null 2>&1; then
    echo shasum
  else
    echo 'No sha256sum or shasum command is available.' >&2
    exit 2
  fi
}

HASH_TOOL="$(hash_tool)"
sha256_file() {
  if [[ "$HASH_TOOL" == "sha256sum" ]]; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

verify_checksum_file() {
  local checksum_file="$1"
  [[ -f "$checksum_file" ]] || return 0
  echo "[hash] $checksum_file"
  while read -r expected file; do
    [[ -z "${expected:-}" ]] && continue
    [[ "$expected" =~ ^[A-Fa-f0-9]{64}$ ]] || { echo "Invalid SHA-256 value in $checksum_file: $expected" >&2; exit 1; }
    file="${file#\*}"
    [[ -f "$file" ]] || { echo "Missing artifact referenced by $checksum_file: $file" >&2; exit 1; }
    actual="$(sha256_file "$file")"
    if [[ "${actual,,}" != "${expected,,}" ]]; then
      echo "HASH MISMATCH: $file" >&2
      echo "  expected: $expected" >&2
      echo "  actual:   $actual" >&2
      exit 1
    fi
    echo "  OK $file"
  done < <(sed 's/[[:space:]][[:space:]]*/ /' "$checksum_file")
}

verify_manifest() {
  local manifest="$1"
  [[ -f "$manifest" ]] || return 0
  command -v jq >/dev/null 2>&1 || { echo 'jq is required for release-manifest validation.' >&2; exit 2; }
  echo "[manifest] $manifest"
  jq -e '.version and .source_sha and .platform and (.artifacts | type == "array")' "$manifest" >/dev/null || {
    echo "Invalid release manifest: $manifest" >&2
    exit 1
  }
  jq -r '.artifacts[] | [.name, .sha256, (.size|tostring)] | @tsv' "$manifest" | while IFS=$'\t' read -r file expected expected_size; do
    [[ -f "$file" ]] || { echo "Manifest references missing file: $file" >&2; exit 1; }
    [[ "$expected" =~ ^[A-Fa-f0-9]{64}$ ]] || { echo "Invalid manifest hash for $file" >&2; exit 1; }
    actual="$(sha256_file "$file")"
    [[ "${actual,,}" == "${expected,,}" ]] || { echo "Manifest hash mismatch: $file" >&2; exit 1; }
    actual_size="$(wc -c < "$file" | tr -d ' ')"
    [[ "$actual_size" == "$expected_size" ]] || { echo "Manifest size mismatch: $file" >&2; exit 1; }
    echo "  OK $file"
  done
}

verify_attestation() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  echo "[attestation] $file"
  if ! gh attestation verify "$file" -R "$REPO"; then
    echo "Attestation verification failed: $file" >&2
    exit 1
  fi
}

for checksum in SHA256SUMS-linux.txt SHA256SUMS-windows.txt SHA256SUMS-macos.txt; do
  verify_checksum_file "$checksum"
done

for manifest in release-manifest-*.json; do
  [[ -e "$manifest" ]] || continue
  verify_manifest "$manifest"
done

if [[ "$REQUIRE_ATTESTATIONS" -eq 1 ]]; then
  found=0
  for file in *.exe *.dmg *.AppImage *.deb; do
    [[ -e "$file" ]] || continue
    found=1
    verify_attestation "$file"
  done
  if [[ "$found" -eq 0 ]]; then
    echo 'No release binaries found for attestation verification.' >&2
    exit 1
  fi
else
  echo '[attestation] skipped; rerun with --require-attestations and --repo OWNER/REPO'
fi

echo 'Validation passed.'
