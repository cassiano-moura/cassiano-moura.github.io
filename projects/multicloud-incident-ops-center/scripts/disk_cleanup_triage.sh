#!/usr/bin/env bash
# ==============================================================================
# disk_cleanup_triage.sh
# ==============================================================================
# Multi-Cloud Linux Storage Capacity Triage & Emergency Remediation Utility
# Target: Cloud Operations / NOC 24/7 Shift Engineers
# Author: Cassiano Moura (https://cassiano-moura.github.io)
#
# Usage:
#   sudo ./disk_cleanup_triage.sh [--dry-run | --execute]
# ==============================================================================

set -euo pipefail

THRESHOLD_WARN=85
THRESHOLD_CRIT=90
LOG_FILE="/var/log/noc_disk_triage_$(date +%Y%m%d_%H%M%S).log"

log() {
    local level="$1"; shift
    local msg="$*"
    local ts
    ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "[$ts] [$level] $msg" | tee -a "${LOG_FILE:-/dev/null}"
}

header() {
    echo "=============================================================================="
    echo " NOC 24/7 Multi-Cloud Storage Triage & Remediation Engine"
    echo " Timestamp: $(date -u) | Operator: Cassiano Moura"
    echo "=============================================================================="
}

check_capacity() {
    log "INFO" "Scanning mounted filesystems for high utilization (Threshold: ${THRESHOLD_WARN}%)..."
    df -hT --exclude-type=tmpfs --exclude-type=devtmpfs --exclude-type=squashfs
    echo ""
    log "INFO" "Checking Inode usage saturation (df -i)..."
    df -i --exclude-type=tmpfs --exclude-type=devtmpfs --exclude-type=squashfs
}

find_unlinked_descriptors() {
    log "WARN" "Checking for deleted files still held in memory by active processes (lsof +L1)..."
    if command -v lsof >/dev/null 2>&1; then
        lsof +L1 | awk 'NR==1 || $7 > 104857600' || true
    else
        log "WARN" "lsof not installed. Skipping open unlinked descriptor inspection."
    fi
}

find_top_space_consumers() {
    log "INFO" "Locating top 10 largest files in /var/log (>100MB)..."
    find /var/log -type f -size +100M -exec ls -lh {} + 2>/dev/null | sort -k5 -rh | head -n 10 || true
}

safe_vacuum() {
    log "ACTION" "Executing safe vacuuming routines (systemd journal & apt cache)..."
    if command -v journalctl >/dev/null 2>&1; then
        log "INFO" "Vacuuming systemd-journald logs older than 3 days..."
        journalctl --vacuum-time=3d || true
    fi

    if command -v apt-get >/dev/null 2>&1; then
        log "INFO" "Cleaning package cache (apt-get clean)..."
        apt-get clean || true
    elif command -v yum >/dev/null 2>&1; then
        log "INFO" "Cleaning yum cache (yum clean all)..."
        yum clean all || true
    fi
}

main() {
    header
    check_capacity
    echo ""
    find_unlinked_descriptors
    echo ""
    find_top_space_consumers
    echo ""
    safe_vacuum
    echo ""
    log "INFO" "Triage procedure completed. Review log at: $LOG_FILE"
}

main "$@"
