#!/usr/bin/env bash
set -euo pipefail

# Install/update Alphamini camera + microphone apps via release APKs.
#
# Downloads from:
# https://github.com/Social-AI-VU/SIC-Android-Connectors-Alphamini/releases/tag/0.1.0
#
# IMPORTANT:
# - Alphamini must be connected over USB when running this script.
# - The script validates discoverability via `adb devices` before installing.
#
# Usage:
#   bash sic_applications/utils/alphamini_app_install.sh
#   bash sic_applications/utils/alphamini_app_install.sh --release-tag 0.1.0
#   bash sic_applications/utils/alphamini_app_install.sh --download-dir /tmp/alphamini-apks
#   ANDROID_SERIAL=<device-id> bash sic_applications/utils/alphamini_app_install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOWNLOAD_DIR_DEFAULT="${SCRIPT_DIR}/.alphamini_apks"

# GitHub release source (owner/repo/tag are used to build APK download URLs).
RELEASE_OWNER="Social-AI-VU"
RELEASE_REPO="SIC-Android-Connectors-Alphamini"
RELEASE_TAG="0.1.0"
DOWNLOAD_DIR="${DOWNLOAD_DIR_DEFAULT}"

# Parse optional CLI flags to override release tag and download directory.
while [[ $# -gt 0 ]]; do
  case "$1" in
    --release-tag)
      RELEASE_TAG="${2:-}"
      shift 2
      ;;
    --download-dir)
      DOWNLOAD_DIR="${2:-}"
      shift
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--release-tag <tag>] [--download-dir <path>]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: $0 [--release-tag <tag>] [--download-dir <path>]"
      exit 2
      ;;
  esac
done

CAMERA_APK="${DOWNLOAD_DIR}/camera_app-debug.apk"
MIC_APK="${DOWNLOAD_DIR}/mic_app-debug.apk"

CAMERA_URL="https://github.com/${RELEASE_OWNER}/${RELEASE_REPO}/releases/download/${RELEASE_TAG}/camera_app-debug.apk"
MIC_URL="https://github.com/${RELEASE_OWNER}/${RELEASE_REPO}/releases/download/${RELEASE_TAG}/mic_app-debug.apk"

CAMERA_PACKAGE="com.example.alphamini.camera"
MIC_PACKAGE="com.example.micarraytest"

require_cmd() {
  # Fail early with a clear message if a required tool is missing.
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Error: '${cmd}' is not installed or not in PATH."
    exit 1
  fi
}

adb_cmd() {
  # Route all adb calls through one helper so ANDROID_SERIAL is consistently honored.
  if [[ -n "${ANDROID_SERIAL:-}" ]]; then
    adb -s "${ANDROID_SERIAL}" "$@"
  else
    adb "$@"
  fi
}

check_adb_device() {
  # Ensure adb server is running and collect current device states.
  adb start-server >/dev/null
  local adb_output
  adb_output="$(adb devices)"
  local lines
  lines="$(echo "${adb_output}" | awk 'NR>1 && $2=="device" {print $1}')"
  local unauthorized_lines
  unauthorized_lines="$(echo "${adb_output}" | awk 'NR>1 && $2=="unauthorized" {print $1}')"
  local offline_lines
  offline_lines="$(echo "${adb_output}" | awk 'NR>1 && $2=="offline" {print $1}')"

  # If user picked a specific device, verify that exact serial is available.
  if [[ -n "${ANDROID_SERIAL:-}" ]]; then
    if ! echo "${lines}" | awk -v serial="${ANDROID_SERIAL}" '$0 == serial { found=1 } END { exit(found ? 0 : 1) }'; then
      echo "Error: ANDROID_SERIAL='${ANDROID_SERIAL}' is not listed as an attached device."
      echo "Run 'adb devices' and set ANDROID_SERIAL to one of the listed device IDs (state: device)."
      exit 1
    fi
    echo "Using device: ${ANDROID_SERIAL}"
    return
  fi

  # Otherwise require exactly one connected device in "device" state.
  local count
  count="$(echo "${lines}" | awk 'NF{n++} END{print n+0}')"
  if [[ "${count}" -eq 0 ]]; then
    echo "Error: No USB-connected Alphamini found in 'device' state."
    if [[ -n "${unauthorized_lines}" ]]; then
      echo "Found unauthorized device(s):"
      echo "${unauthorized_lines}"
      echo "Unlock Alphamini and accept the USB debugging prompt."
    fi
    if [[ -n "${offline_lines}" ]]; then
      echo "Found offline device(s):"
      echo "${offline_lines}"
      echo "Reconnect USB and rerun."
    fi
    echo "Current adb devices output:"
    echo "${adb_output}"
    exit 1
  elif [[ "${count}" -gt 1 ]]; then
    echo "Error: Multiple ADB devices connected in 'device' state."
    echo "Set ANDROID_SERIAL to select one:"
    echo "${lines}"
    exit 1
  fi
  echo "Using device: ${lines}"
}

download_apks() {
  # Download both APK assets from the chosen GitHub release tag.
  mkdir -p "${DOWNLOAD_DIR}"

  echo "Downloading camera APK from release ${RELEASE_TAG}..."
  curl -fL --retry 3 --connect-timeout 10 -o "${CAMERA_APK}" "${CAMERA_URL}"

  echo "Downloading microphone APK from release ${RELEASE_TAG}..."
  curl -fL --retry 3 --connect-timeout 10 -o "${MIC_APK}" "${MIC_URL}"
}

install_apk() {
  # Install (or replace) one APK on the selected device.
  local apk_path="$1"
  local package_name="$2"

  if [[ ! -f "${apk_path}" ]]; then
    echo "Error: APK not found: ${apk_path}"
    exit 1
  fi

  echo "Installing ${apk_path} ..."
  adb_cmd install -r -t "${apk_path}"
  echo "Installed package: ${package_name}"
}

verify_install() {
  # Confirm package presence after installation for quick operator feedback.
  local package_name="$1"
  if adb_cmd shell pm list packages | awk -v pkg="package:${package_name}" '$0 == pkg { found=1 } END { exit(found ? 0 : 1) }'; then
    echo "Verified on device: ${package_name}"
  else
    echo "Warning: package not found after install: ${package_name}"
  fi
}

uninstall_if_present() {
  # Best-effort cleanup: uninstall old package if it exists, continue otherwise.
  local package_name="$1"
  if adb_cmd shell pm list packages | awk -v pkg="package:${package_name}" '$0 == pkg { found=1 } END { exit(found ? 0 : 1) }'; then
    echo "Existing package found, uninstalling: ${package_name}"
    # Keep install flow resilient if uninstall reports a non-zero status.
    adb_cmd uninstall "${package_name}" >/dev/null 2>&1 || true
  else
    echo "Package not installed, skipping uninstall: ${package_name}"
  fi
}

main() {
  # 1) Validate required tools.
  require_cmd adb
  require_cmd curl

  # 2) Ensure exactly one target device is selected/reachable.
  check_adb_device

  # 3) Fetch APKs for the chosen release tag.
  download_apks

  # 4) Remove previous app installs if present (safe no-op when absent).
  uninstall_if_present "${CAMERA_PACKAGE}"
  uninstall_if_present "${MIC_PACKAGE}"

  # 5) Install + verify camera app.
  install_apk "${CAMERA_APK}" "${CAMERA_PACKAGE}"
  verify_install "${CAMERA_PACKAGE}"

  # 6) Install + verify microphone app.
  install_apk "${MIC_APK}" "${MIC_PACKAGE}"
  verify_install "${MIC_PACKAGE}"

  # 7) Print local APK paths for debugging/reuse.
  echo
  echo "Downloaded APKs:"
  echo "  ${CAMERA_APK}"
  echo "  ${MIC_APK}"
  echo "Done. If microphone permissions/array access do not work yet, reboot Alphamini."
}

main "$@"
