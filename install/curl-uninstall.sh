#!/bin/bash

# GitHub-hosted Descriptor Uninstallation Script
# Usage: curl -sSL https://raw.githubusercontent.com/orozcoh/descriptor/main/install/curl-uninstall.sh | bash

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/descriptor"

# Logging function
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (should not be)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root."
        log_error "Please run without sudo."
        exit 1
    fi
}

# Confirm uninstallation
confirm_uninstall() {
    echo "🧹 This will uninstall Descriptor if installed via curl to $INSTALL_DIR"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Uninstallation cancelled."
        exit 0
    fi
}

# Run uninstall
run_uninstall() {
    if [[ -d "$INSTALL_DIR" && -f "$INSTALL_DIR/install/uninstall.sh" ]]; then
        log_info "Found installation at $INSTALL_DIR. Running uninstall..."
        cd "$INSTALL_DIR"
        ./install/uninstall.sh
        log_success "Uninstallation complete!"
    else
        log_warning "No curl installation found at $INSTALL_DIR or uninstall.sh missing."
        log_info "Manually remove $INSTALL_DIR if needed."
        if command -v descriptor >/dev/null 2>&1; then
            log_warning "'descriptor' command still in PATH. Restart terminal or run 'hash -r'."
        fi
    fi
}

main() {
    echo "🧹 Starting Descriptor One-Command Uninstallation"
    echo "================================================"
    check_root
    confirm_uninstall
    run_uninstall
}

main "$@"
